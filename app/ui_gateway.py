from __future__ import annotations

import asyncio
import json
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Deque

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware


@dataclass
class WallSummary:
    side: str
    wall_price: float
    wall_qty: float
    wall_notional: float
    wall_share: float
    best_bid: float
    best_ask: float


@dataclass
class SymbolState:
    symbol: str
    spot_mid: float = 0.0
    perp_mark: float = 0.0
    perp_mid: float = 0.0
    basis_mark: float = 0.0
    basis_mid: float = 0.0
    zscore: float = 0.0
    duration_s: int = 0
    last_update_ts: int = 0
    wall: WallSummary | None = None
    last_wall_event: str | None = None
    last_wall_event_ts: int | None = None
    last_basis_event: str | None = None
    last_basis_event_ts: int | None = None


@dataclass
class UiCache:
    states: dict[str, SymbolState] = field(default_factory=dict)
    events: Deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=6000))
    timeseries: dict[str, Deque[dict[str, Any]]] = field(default_factory=dict)


class UiGateway:
    def __init__(self, data_dir: str, event_window_minutes: int = 60) -> None:
        self.logger = logging.getLogger("ui_gateway")
        self.cache = UiCache(events=deque(maxlen=event_window_minutes * 60))
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.data_dir = Path(data_dir)

    def update_state(self, state: SymbolState) -> None:
        self.cache.states[state.symbol] = state
        series = self.cache.timeseries.setdefault(state.symbol, deque(maxlen=6 * 60 * 60))
        series.append(
            {
                "ts": state.last_update_ts,
                "spot_mid": state.spot_mid,
                "perp_mark": state.perp_mark,
                "basis_mark": state.basis_mark,
                "zscore": state.zscore,
                "duration_s": state.duration_s,
                "wall_notional": state.wall.wall_notional if state.wall else 0.0,
                "wall_price": state.wall.wall_price if state.wall else 0.0,
            }
        )

    def record_event(self, payload: dict[str, Any]) -> None:
        self.cache.events.append(payload)
        self.queue.put_nowait(payload)

    def list_event_packs(self) -> list[dict[str, Any]]:
        packs_dir = self.data_dir / "event_packs"
        if not packs_dir.exists():
            return []
        results: list[dict[str, Any]] = []
        for path in packs_dir.iterdir():
            if not path.is_dir():
                continue
            records_path = path / "records.jsonl"
            results.append(
                {
                    "id": path.name,
                    "path": str(records_path),
                }
            )
        return results

    def load_event_pack(self, pack_id: str) -> list[dict[str, Any]]:
        records_path = self.data_dir / "event_packs" / pack_id / "records.jsonl"
        if not records_path.exists():
            return []
        records: list[dict[str, Any]] = []
        with records_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                records.append(json.loads(line))
        return records


async def _ws_sender(ws: WebSocket, gateway: UiGateway) -> None:
    while True:
        payload = await gateway.queue.get()
        await ws.send_json({"type": "event", "ts": payload.get("ts"), "data": payload})


async def _ws_state_publisher(ws: WebSocket, gateway: UiGateway) -> None:
    while True:
        await asyncio.sleep(1)
        snapshot = list(gateway.cache.states.values())
        payload = [state.__dict__ for state in snapshot]
        await ws.send_json({"type": "state_update", "ts": int(time.time() * 1000), "data": payload})


def create_app(gateway: UiGateway) -> FastAPI:
    app = FastAPI(title="BasisSentry UI")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/v1/symbols")
    async def get_symbols() -> dict[str, Any]:
        return {
            "symbols": list(gateway.cache.states.keys()),
            "states": [state.__dict__ for state in gateway.cache.states.values()],
        }

    @app.get("/api/v1/state")
    async def get_state(symbol: str) -> dict[str, Any]:
        state = gateway.cache.states.get(symbol)
        return {"state": state.__dict__ if state else None}

    @app.get("/api/v1/events")
    async def get_events(symbol: str | None = None, since: int | None = None, types: str | None = None) -> dict[str, Any]:
        events = list(gateway.cache.events)
        if symbol:
            events = [event for event in events if event.get("symbol") == symbol]
        if since:
            events = [event for event in events if event.get("ts", 0) >= since]
        if types:
            allowed = {t.strip() for t in types.split(",")}
            events = [event for event in events if event.get("event_type") in allowed]
        return {"events": events[:1000]}

    @app.get("/api/v1/timeseries")
    async def get_timeseries(symbol: str, range: str = "5m") -> dict[str, Any]:
        ranges = {"5m": 300, "15m": 900, "1h": 3600, "6h": 21600}
        seconds = ranges.get(range, 300)
        series = list(gateway.cache.timeseries.get(symbol, deque()))
        if not series:
            return {"series": []}
        cutoff = series[-1]["ts"] - seconds * 1000
        return {"series": [point for point in series if point["ts"] >= cutoff]}

    @app.get("/api/v1/event-packs")
    async def get_event_packs() -> dict[str, Any]:
        return {"packs": gateway.list_event_packs()}

    @app.get("/api/v1/event-packs/{pack_id}")
    async def get_event_pack(pack_id: str) -> dict[str, Any]:
        return {"records": gateway.load_event_pack(pack_id)}

    @app.websocket("/ws/v1/stream")
    async def ws_stream(ws: WebSocket) -> None:
        await ws.accept()
        sender = asyncio.create_task(_ws_sender(ws, gateway))
        publisher = asyncio.create_task(_ws_state_publisher(ws, gateway))
        try:
            await asyncio.gather(sender, publisher)
        finally:
            sender.cancel()
            publisher.cancel()

    return app
