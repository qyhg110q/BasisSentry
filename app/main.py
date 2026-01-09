from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import asdict
from typing import Any

from app.config import AppConfig, load_config
from app.engine.alerts import AlertManager
from app.engine.basis_engine import BasisEngine
from app.engine.event_pack import EventPackRecorder
from app.engine.event_store import EventStore
from app.engine.wall_detector import WallDetector
from app.models import AggTrade, BookTicker, DepthSnapshot, MarkPrice
from app.universe import load_universe
from app.ui_gateway import SymbolState, UiGateway, WallSummary, create_app
from app.utils.time import now_s
from app.ws.futures_client import FuturesStreamMessage, FuturesWsClient
from app.ws.spot_client import SpotStreamMessage, SpotWsClient
import uvicorn


class AppRuntime:
    def __init__(self, config: AppConfig, gateway: UiGateway | None = None) -> None:
        self.config = config
        self.logger = logging.getLogger("app")
        self.event_store = EventStore(config.output.data_dir)
        self.alerts = AlertManager()
        self.event_pack = EventPackRecorder(config.output.data_dir, config.event_pack)
        self.basis_engine = BasisEngine(
            window_seconds=config.basis.window_seconds,
            abs_threshold=config.basis.basis_abs_threshold,
            min_duration_s=config.basis.min_duration_s,
            sigma_floor=config.basis.sigma_floor_bps / 10000,
        )
        self.wall_detector = WallDetector(config.wall)
        self.spot_book: dict[str, BookTicker] = {}
        self.perp_book: dict[str, BookTicker] = {}
        self.perp_mark: dict[str, MarkPrice] = {}
        self.gateway = gateway
        self.last_basis_ts_ms: dict[str, int] = {}

    def _get_state(self, symbol: str) -> SymbolState:
        if self.gateway and symbol in self.gateway.cache.states:
            return self.gateway.cache.states[symbol]
        return SymbolState(symbol=symbol)

    def _record_event(self, payload: dict[str, Any]) -> None:
        self.event_store.append(payload)
        self.logger.info("event: %s", payload["event_type"])
        if self.gateway:
            self.gateway.record_event(payload)

    async def _handle_basis(self, symbol: str, timestamp_s: float) -> None:
        ts_ms = int(timestamp_s * 1000)
        last_ts = self.last_basis_ts_ms.get(symbol, 0)
        if ts_ms - last_ts < self.config.basis.calc_interval_ms:
            return
        self.last_basis_ts_ms[symbol] = ts_ms
        spot = self.spot_book.get(symbol)
        perp = self.perp_book.get(symbol)
        mark = self.perp_mark.get(symbol)
        if not (spot and perp and mark):
            return
        snapshot = self.basis_engine.update(
            symbol=symbol,
            timestamp_s=timestamp_s,
            spot_mid=spot.mid,
            perp_mid=perp.mid,
            perp_mark=mark.mark_price,
        )
        event_payload = {
            "ts": ts_ms,
            "symbol": symbol,
            "spot_mid": snapshot.spot_mid,
            "perp_mid": snapshot.perp_mid,
            "perp_mark": snapshot.perp_mark,
            "basis_mid": snapshot.basis_mid,
            "basis_mark": snapshot.basis_mark,
            "zscore": snapshot.zscore,
            "duration_s": snapshot.duration_s,
        }
        self.event_pack.record(symbol, {"ts": event_payload["ts"], "type": "basis", **event_payload})
        if self.gateway:
            state = self._get_state(symbol)
            state.spot_mid = snapshot.spot_mid
            state.perp_mid = snapshot.perp_mid
            state.perp_mark = snapshot.perp_mark
            state.basis_mid = snapshot.basis_mid
            state.basis_mark = snapshot.basis_mark
            state.zscore = snapshot.zscore
            state.duration_s = snapshot.duration_s
            state.last_update_ts = event_payload["ts"]
            self.gateway.update_state(state)
        if self.basis_engine.is_spike(snapshot, self.config.basis.z_threshold):
            event_payload.update(
                {
                    "event_type": "BASIS_SPIKE",
                    "event_reason": "basis_mark exceeds threshold with zscore",
                }
            )
            self._record_event(event_payload)
            if self.gateway:
                state = self._get_state(symbol)
                state.last_basis_event = "BASIS_SPIKE"
                state.last_basis_event_ts = event_payload["ts"]
                self.gateway.update_state(state)
            self.alerts.notify(f"BASIS_SPIKE {symbol} {snapshot.basis_mark:.4f}")

    async def _handle_wall(self, depth: DepthSnapshot) -> None:
        self.event_pack.record(depth.symbol, {"ts": depth.event_time, "type": "depth", **asdict(depth)})
        for event in self.wall_detector.evaluate(depth, side="bid"):
            wall = event.wall_state
            payload = {
                "ts": depth.event_time,
                "symbol": wall.symbol,
                "spot_mid": self.spot_book.get(wall.symbol).mid if wall.symbol in self.spot_book else 0.0,
                "perp_mid": self.perp_book.get(wall.symbol).mid if wall.symbol in self.perp_book else 0.0,
                "perp_mark": self.perp_mark.get(wall.symbol).mark_price if wall.symbol in self.perp_mark else 0.0,
                "basis_mid": 0.0,
                "basis_mark": 0.0,
                "zscore": 0.0,
                "duration_s": 0,
                "wall": {
                    "side": wall.side,
                    "wall_price": wall.wall_price,
                    "wall_qty": wall.wall_qty,
                    "wall_notional": wall.wall_notional,
                    "wall_share": wall.wall_share,
                    "best_bid": wall.best_bid,
                    "best_ask": wall.best_ask,
                },
                "event_type": event.event_type,
                "event_reason": event.reason,
            }
            self.event_pack.record(wall.symbol, {"ts": depth.event_time, "type": "wall_event", **payload})
            self._record_event(payload)
            if self.gateway:
                state = self._get_state(wall.symbol)
                state.wall = WallSummary(
                    side=wall.side,
                    wall_price=wall.wall_price,
                    wall_qty=wall.wall_qty,
                    wall_notional=wall.wall_notional,
                    wall_share=wall.wall_share,
                    best_bid=wall.best_bid,
                    best_ask=wall.best_ask,
                )
                state.last_wall_event = event.event_type
                state.last_wall_event_ts = depth.event_time
                state.last_update_ts = depth.event_time
                self.gateway.update_state(state)
            if event.event_type in {"WALL_REMOVE", "WALL_REMOVE_OR_EATEN"}:
                self.alerts.notify(f"{event.event_type} {wall.symbol} {wall.wall_price}")

    def handle_spot_message(self, message: SpotStreamMessage) -> None:
        stream = message.stream
        data = message.data
        if stream.endswith("@bookTicker"):
            ticker = BookTicker(
                symbol=data["s"].lower(),
                bid_price=float(data["b"]),
                bid_qty=float(data["B"]),
                ask_price=float(data["a"]),
                ask_qty=float(data["A"]),
                event_time=int(data.get("E") or data.get("eventTime") or 0),
            )
            self.spot_book[ticker.symbol] = ticker
            if self.gateway:
                state = self._get_state(ticker.symbol)
                state.spot_mid = ticker.mid
                state.last_update_ts = ticker.event_time or int(now_s() * 1000)
                self.gateway.update_state(state)
            asyncio.create_task(self._handle_basis(ticker.symbol, now_s()))
            self.event_pack.record(ticker.symbol, {"ts": ticker.event_time, "type": "spot_book", **asdict(ticker)})
        elif "@depth" in stream:
            depth = DepthSnapshot(
                symbol=data["s"].lower(),
                bids=[(float(p), float(q)) for p, q in data.get("b", [])],
                asks=[(float(p), float(q)) for p, q in data.get("a", [])],
                event_time=int(data.get("E") or data.get("eventTime") or 0),
            )
            asyncio.create_task(self._handle_wall(depth))
        elif stream.endswith("@aggTrade"):
            trade = AggTrade(
                symbol=data["s"].lower(),
                price=float(data["p"]),
                qty=float(data["q"]),
                is_buyer_maker=bool(data["m"]),
                event_time=int(data.get("E") or data.get("T") or 0),
            )
            self.wall_detector.add_trade(trade)
            self.event_pack.record(trade.symbol, {"ts": trade.event_time, "type": "aggTrade", **asdict(trade)})

    def handle_futures_message(self, message: FuturesStreamMessage) -> None:
        stream = message.stream
        data = message.data
        if stream.endswith("@bookTicker"):
            ticker = BookTicker(
                symbol=data["s"].lower(),
                bid_price=float(data["b"]),
                bid_qty=float(data["B"]),
                ask_price=float(data["a"]),
                ask_qty=float(data["A"]),
                event_time=int(data.get("E") or data.get("eventTime") or 0),
            )
            self.perp_book[ticker.symbol] = ticker
            if self.gateway:
                state = self._get_state(ticker.symbol)
                state.perp_mid = ticker.mid
                state.last_update_ts = ticker.event_time or int(now_s() * 1000)
                self.gateway.update_state(state)
            asyncio.create_task(self._handle_basis(ticker.symbol, now_s()))
            self.event_pack.record(ticker.symbol, {"ts": ticker.event_time, "type": "perp_book", **asdict(ticker)})
        elif stream.endswith("@markPrice@1s"):
            mark = MarkPrice(
                symbol=data["s"].lower(),
                mark_price=float(data["p"]),
                funding_rate=float(data["r"]),
                event_time=int(data.get("E") or data.get("eventTime") or 0),
            )
            self.perp_mark[mark.symbol] = mark
            if self.gateway:
                state = self._get_state(mark.symbol)
                state.perp_mark = mark.mark_price
                state.last_update_ts = mark.event_time or int(now_s() * 1000)
                self.gateway.update_state(state)
            asyncio.create_task(self._handle_basis(mark.symbol, now_s()))
            self.event_pack.record(mark.symbol, {"ts": mark.event_time, "type": "mark", **asdict(mark)})


async def run_app(config: AppConfig, dry_run: bool = False) -> None:
    if config.symbols.mode == "auto":
        universe = await load_universe(config.symbols.auto_filters, config.rest)
        symbols = universe.symbols
    else:
        symbols = [s.lower() for s in config.symbols.manual_list]

    if dry_run:
        print("Universe symbols:")
        for symbol in symbols:
            print(symbol)
        print("Spot streams:")
        for symbol in symbols:
            print(f"{symbol}@bookTicker")
            print(f"{symbol}@depth20@100ms")
            print(f"{symbol}@aggTrade")
        print("Futures streams:")
        for symbol in symbols:
            print(f"{symbol}@bookTicker")
            print(f"{symbol}@markPrice@1s")
        return

    gateway = UiGateway(config.output.data_dir) if config.ui.enabled else None
    runtime = AppRuntime(config, gateway=gateway)
    spot_clients: list[SpotWsClient] = []
    if config.ws.spot_bookticker_separate:
        spot_clients.append(
            SpotWsClient(
                base_url=config.ws.spot_base,
                symbols=symbols,
                max_streams_per_conn=config.ws.max_streams_per_conn,
                backoff_min=config.ws.reconnect_backoff.min,
                backoff_max=config.ws.reconnect_backoff.max,
                proxy_url=config.ws.proxy_url,
                use_aiohttp=config.ws.client == "aiohttp",
                streams=["bookTicker"],
            )
        )
        spot_clients.append(
            SpotWsClient(
                base_url=config.ws.spot_base,
                symbols=symbols,
                max_streams_per_conn=config.ws.max_streams_per_conn,
                backoff_min=config.ws.reconnect_backoff.min,
                backoff_max=config.ws.reconnect_backoff.max,
                proxy_url=config.ws.proxy_url,
                use_aiohttp=config.ws.client == "aiohttp",
                streams=[stream for stream in config.ws.spot_streams if stream != "bookTicker"],
            )
        )
    else:
        spot_clients.append(
            SpotWsClient(
                base_url=config.ws.spot_base,
                symbols=symbols,
                max_streams_per_conn=config.ws.max_streams_per_conn,
                backoff_min=config.ws.reconnect_backoff.min,
                backoff_max=config.ws.reconnect_backoff.max,
                proxy_url=config.ws.proxy_url,
                use_aiohttp=config.ws.client == "aiohttp",
                streams=config.ws.spot_streams,
            )
        )
    futures_clients: list[FuturesWsClient] = []
    if config.ws.futures_bookticker_separate:
        futures_clients.append(
            FuturesWsClient(
                base_url=config.ws.futures_base,
                symbols=symbols,
                max_streams_per_conn=config.ws.max_streams_per_conn,
                backoff_min=config.ws.reconnect_backoff.min,
                backoff_max=config.ws.reconnect_backoff.max,
                proxy_url=config.ws.proxy_url,
                use_aiohttp=config.ws.client == "aiohttp",
                streams=["bookTicker"],
            )
        )
        futures_clients.append(
            FuturesWsClient(
                base_url=config.ws.futures_base,
                symbols=symbols,
                max_streams_per_conn=config.ws.max_streams_per_conn,
                backoff_min=config.ws.reconnect_backoff.min,
                backoff_max=config.ws.reconnect_backoff.max,
                proxy_url=config.ws.proxy_url,
                use_aiohttp=config.ws.client == "aiohttp",
                streams=[stream for stream in config.ws.futures_streams if stream != "bookTicker"],
            )
        )
    else:
        futures_clients.append(
            FuturesWsClient(
                base_url=config.ws.futures_base,
                symbols=symbols,
                max_streams_per_conn=config.ws.max_streams_per_conn,
                backoff_min=config.ws.reconnect_backoff.min,
                backoff_max=config.ws.reconnect_backoff.max,
                proxy_url=config.ws.proxy_url,
                use_aiohttp=config.ws.client == "aiohttp",
                streams=config.ws.futures_streams,
            )
        )

    tasks = [asyncio.create_task(client.run(runtime.handle_spot_message)) for client in spot_clients]
    tasks.extend(asyncio.create_task(client.run(runtime.handle_futures_message)) for client in futures_clients)
    if gateway and config.ui.enabled:
        app = create_app(gateway)
        server = uvicorn.Server(
            uvicorn.Config(app, host=config.ui.host, port=config.ui.port, log_level="info")
        )
        tasks.append(asyncio.create_task(server.serve()))

    await asyncio.gather(*tasks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BasisSentry monitoring")
    parser.add_argument("run", nargs="?", help="run the service")
    parser.add_argument("--config", required=True, help="config yaml path")
    parser.add_argument("--dry-run", action="store_true", help="print subscriptions and exit")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config(args.config)
    logging.basicConfig(level=config.output.log_level)
    asyncio.run(run_app(config, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
