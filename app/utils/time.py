from __future__ import annotations

import time


def now_ms() -> int:
    return int(time.time() * 1000)


def now_s() -> float:
    return time.time()
