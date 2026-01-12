from app.config import WallConfig
from app.engine.wall_detector import WallDetector
from app.models import AggTrade, DepthSnapshot


def _depth(symbol: str, bid_price: float, bid_qty: float) -> DepthSnapshot:
    bids = [(bid_price, bid_qty)] + [(bid_price - i, 1.0) for i in range(1, 20)]
    asks = [(bid_price + 1, 1.0)] * 20
    return DepthSnapshot(symbol=symbol, bids=bids, asks=asks, event_time=0)


def test_wall_thresholds() -> None:
    config = WallConfig(hard_min_wall_usdt=200000, k_median=8, share_threshold=0.25, range_bps=30)
    detector = WallDetector(config)
    depth = _depth("btcusdt", 100.0, 3000.0)
    events = detector.evaluate(depth)
    assert any(event.event_type == "WALL_APPEAR" for event in events)


def test_wall_remove_vs_eaten() -> None:
    config = WallConfig()
    detector = WallDetector(config)
    depth = _depth("btcusdt", 100.0, 3000.0)
    detector.evaluate(depth)

    trade = AggTrade(symbol="btcusdt", price=100.0, qty=1.0, is_buyer_maker=False, event_time=1000)
    detector.add_trade(trade)

    empty_depth = DepthSnapshot(symbol="btcusdt", bids=[(99.0, 1.0)], asks=[(101.0, 1.0)], event_time=1000)
    events = detector.evaluate(empty_depth)
    assert events
    assert events[-1].event_type in {"WALL_REMOVE", "WALL_EATEN"}
