from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Optional

from app.config import WallConfig
from app.models import AggTrade, DepthSnapshot, WallEvent, WallState


@dataclass
class WallMetrics:
    price: float
    qty: float
    notional: float
    share: float
    best_bid: float
    best_ask: float


class WallDetector:
    def __init__(self, config: WallConfig) -> None:
        self.config = config
        self.current_wall: dict[tuple[str, str], WallState] = {}
        self.trades: dict[str, list[AggTrade]] = {}

    def add_trade(self, trade: AggTrade) -> None:
        bucket = self.trades.setdefault(trade.symbol, [])
        bucket.append(trade)

    def _recent_trades(self, symbol: str, now_ms: int) -> list[AggTrade]:
        window_ms = self.config.trade_confirm.trade_window_s * 1000
        trades = self.trades.get(symbol, [])
        filtered = [t for t in trades if now_ms - t.event_time <= window_ms]
        self.trades[symbol] = filtered
        return filtered

    def _calc_wall_metrics(self, depth: DepthSnapshot, side: str) -> Optional[WallMetrics]:
        levels = depth.bids if side == "bid" else depth.asks
        if not levels:
            return None
        notionals = [price * qty for price, qty in levels]
        max_index = max(range(len(notionals)), key=notionals.__getitem__)
        max_price, max_qty = levels[max_index]
        max_notional = notionals[max_index]
        med = median(notionals)
        total = sum(notionals)
        share = max_notional / total if total else 0.0
        best_bid = depth.bids[0][0] if depth.bids else 0.0
        best_ask = depth.asks[0][0] if depth.asks else 0.0
        return WallMetrics(
            price=max_price,
            qty=max_qty,
            notional=max_notional,
            share=share,
            best_bid=best_bid,
            best_ask=best_ask,
        )

    def _is_wall(self, metrics: WallMetrics, notionals: Iterable[float]) -> bool:
        if metrics.notional < self.config.hard_min_wall_usdt:
            return False
        med = median(list(notionals)) if notionals else 0.0
        if med and metrics.notional < self.config.k_median * med:
            return False
        if metrics.share < self.config.share_threshold:
            return False
        best_bid = metrics.best_bid
        if best_bid and metrics.price > best_bid * (1 + self.config.range_bps / 10000):
            return False
        return True

    def evaluate(self, depth: DepthSnapshot, side: str = "bid") -> list[WallEvent]:
        events: list[WallEvent] = []
        metrics = self._calc_wall_metrics(depth, side)
        if not metrics:
            return events
        levels = depth.bids if side == "bid" else depth.asks
        notionals = [price * qty for price, qty in levels]
        is_wall = self._is_wall(metrics, notionals)
        wall_key = (depth.symbol, side)
        previous = self.current_wall.get(wall_key)

        if is_wall:
            wall_state = WallState(
                symbol=depth.symbol,
                side=side,
                wall_price=metrics.price,
                wall_qty=metrics.qty,
                wall_notional=metrics.notional,
                wall_share=metrics.share,
                best_bid=metrics.best_bid,
                best_ask=metrics.best_ask,
                present_since=previous.present_since if previous else depth.event_time / 1000,
                last_seen_ts=depth.event_time / 1000,
            )
            if not previous:
                events.append(WallEvent("WALL_APPEAR", "wall detected", wall_state))
            else:
                if wall_state.wall_price != previous.wall_price:
                    events.append(WallEvent("WALL_MOVE", "wall price moved", wall_state))
                elif wall_state.wall_notional > previous.wall_notional * 1.2:
                    events.append(WallEvent("WALL_GROW", "wall notional increased", wall_state))
                elif wall_state.wall_notional < previous.wall_notional * 0.7:
                    events.append(WallEvent("WALL_WEAKEN", "wall notional decreased", wall_state))
            self.current_wall[wall_key] = wall_state
            return events

        if previous:
            disappeared_notional = previous.wall_notional
            explained = 0.0
            if self.config.trade_confirm.use_aggTrade:
                trades = self._recent_trades(depth.symbol, depth.event_time)
                price_band = previous.wall_price * (self.config.trade_confirm.trade_price_bps / 10000)
                for trade in trades:
                    if abs(trade.price - previous.wall_price) <= price_band:
                        explained += trade.price * trade.qty
            threshold = disappeared_notional * self.config.trade_confirm.trade_explain_ratio
            if self.config.trade_confirm.use_aggTrade:
                if explained < threshold:
                    event_type = "WALL_REMOVE"
                    reason = "wall removed without enough trades"
                else:
                    event_type = "WALL_EATEN"
                    reason = "wall removed with trades"
            else:
                event_type = "WALL_REMOVE_OR_EATEN"
                reason = "wall removed without trade confirmation"

            events.append(
                WallEvent(
                    event_type,
                    reason,
                    previous,
                    disappeared_notional=disappeared_notional,
                    explained_notional=explained,
                )
            )
            self.current_wall.pop(wall_key, None)

        return events
