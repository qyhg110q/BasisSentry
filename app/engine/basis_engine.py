from __future__ import annotations

from dataclasses import dataclass

from app.models import BasisSnapshot
from app.utils.rolling_stats import RollingStats


@dataclass
class BasisState:
    stats: RollingStats
    duration_s: int = 0
    last_update_s: float | None = None


class BasisEngine:
    def __init__(
        self,
        window_seconds: int,
        abs_threshold: float,
        min_duration_s: int,
        sigma_floor: float,
    ) -> None:
        self.window_seconds = window_seconds
        self.abs_threshold = abs_threshold
        self.min_duration_s = min_duration_s
        self.sigma_floor = sigma_floor
        self.states: dict[str, BasisState] = {}

    def update(
        self,
        symbol: str,
        timestamp_s: float,
        spot_mid: float,
        perp_mid: float,
        perp_mark: float,
    ) -> BasisSnapshot:
        basis_mid = (spot_mid - perp_mid) / spot_mid if spot_mid else 0.0
        basis_mark = (spot_mid - perp_mark) / spot_mid if spot_mid else 0.0

        state = self.states.setdefault(symbol, BasisState(stats=RollingStats(self.window_seconds)))
        state.stats.add(timestamp_s, basis_mark)
        mean, std = state.stats.mean_std()
        std = max(std, self.sigma_floor)
        zscore = (basis_mark - mean) / std if std else 0.0

        if abs(basis_mark) >= self.abs_threshold:
            if state.last_update_s is None:
                state.duration_s = 1
            else:
                increment = max(1, int(round(timestamp_s - state.last_update_s)))
                state.duration_s += increment
        else:
            state.duration_s = 0

        state.last_update_s = timestamp_s

        return BasisSnapshot(
            symbol=symbol,
            spot_mid=spot_mid,
            perp_mid=perp_mid,
            perp_mark=perp_mark,
            basis_mid=basis_mid,
            basis_mark=basis_mark,
            zscore=zscore,
            duration_s=state.duration_s,
        )

    def is_spike(self, snapshot: BasisSnapshot, z_threshold: float) -> bool:
        return (
            abs(snapshot.basis_mark) >= self.abs_threshold
            and snapshot.zscore >= z_threshold
            and snapshot.duration_s >= self.min_duration_s
        )
