from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any


class EventStore:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.data_dir / "events.jsonl"

    def append(self, payload: dict[str, Any]) -> None:
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def asdict(obj: Any) -> dict[str, Any]:
        return asdict(obj)
