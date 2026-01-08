from app.engine.basis_engine import BasisEngine


def test_basis_zscore_and_duration() -> None:
    engine = BasisEngine(window_seconds=300, abs_threshold=0.02, min_duration_s=2)
    snapshot = engine.update("btcusdt", 0.0, 100.0, 99.0, 99.0)
    assert round(snapshot.basis_mark, 4) == 0.01
    assert snapshot.zscore == 0.0
    assert snapshot.duration_s == 0

    snapshot = engine.update("btcusdt", 1.0, 100.0, 97.0, 97.0)
    assert snapshot.duration_s == 1

    snapshot = engine.update("btcusdt", 2.0, 100.0, 97.0, 97.0)
    assert snapshot.duration_s >= 2
