from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class BookTicker:
    symbol: str
    bid_price: float
    bid_qty: float
    ask_price: float
    ask_qty: float
    event_time: int

    @property
    def mid(self) -> float:
        return (self.bid_price + self.ask_price) / 2


@dataclass
class MarkPrice:
    symbol: str
    mark_price: float
    funding_rate: float
    event_time: int


@dataclass
class DepthSnapshot:
    symbol: str
    bids: list[tuple[float, float]]
    asks: list[tuple[float, float]]
    event_time: int


@dataclass
class AggTrade:
    symbol: str
    price: float
    qty: float
    is_buyer_maker: bool
    event_time: int


@dataclass
class BasisSnapshot:
    symbol: str
    spot_mid: float
    perp_mid: float
    perp_mark: float
    basis_mid: float
    basis_mark: float
    zscore: float
    duration_s: int


@dataclass
class WallState:
    symbol: str
    side: Literal["bid", "ask"]
    wall_price: float
    wall_qty: float
    wall_notional: float
    wall_share: float
    best_bid: float
    best_ask: float
    present_since: float
    last_seen_ts: float


@dataclass
class WallEvent:
    event_type: str
    reason: str
    wall_state: WallState
    disappeared_notional: Optional[float] = None
    explained_notional: Optional[float] = None
