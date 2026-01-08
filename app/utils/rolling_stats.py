from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import sqrt


@dataclass
class RollingStats:
    window_seconds: int
    values: deque[tuple[float, float]]

    def __init__(self, window_seconds: int) -> None:
        self.window_seconds = window_seconds
        self.values = deque()

    def add(self, timestamp_s: float, value: float) -> None:
        self.values.append((timestamp_s, value))
        self._trim(timestamp_s)

    def _trim(self, timestamp_s: float) -> None:
        cutoff = timestamp_s - self.window_seconds
        while self.values and self.values[0][0] < cutoff:
            self.values.popleft()

    def mean_std(self) -> tuple[float, float]:
        if not self.values:
            return 0.0, 0.0
        vals = [v for _, v in self.values]
        mean = sum(vals) / len(vals)
        if len(vals) == 1:
            return mean, 0.0
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        return mean, sqrt(variance)
