from __future__ import annotations

import asyncio
import json
from collections import deque
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.config import EventPackConfig


class EventPackRecorder:
    def __init__(self, data_dir: str, config: EventPackConfig) -> None:
        self.data_dir = Path(data_dir)
        self.config = config
        self.buffers: dict[str, deque[dict[str, Any]]] = {}
        self.lock = asyncio.Lock()

    def record(self, symbol: str, payload: dict[str, Any]) -> None:
        buffer = self.buffers.setdefault(symbol, deque())
        buffer.append(payload)
        cutoff_ms = payload["ts"] - self.config.pre_seconds * 1000
        while buffer and buffer[0]["ts"] < cutoff_ms:
            buffer.popleft()

    async def emit(self, event_id: str, symbol: str, post_records: list[dict[str, Any]]) -> None:
        async with self.lock:
            target_dir = self.data_dir / "event_packs" / event_id
            target_dir.mkdir(parents=True, exist_ok=True)
            records = list(self.buffers.get(symbol, deque())) + post_records
            file_path = target_dir / "records.jsonl"
            with file_path.open("w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    async def capture_post_window(self, symbol: str) -> list[dict[str, Any]]:
        await asyncio.sleep(self.config.post_seconds)
        return list(self.buffers.get(symbol, deque()))


def serialize_payload(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "__dataclass_fields__"):
        return asdict(payload)
    return dict(payload)
