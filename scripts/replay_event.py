from __future__ import annotations

import argparse
import json
from pathlib import Path


def replay_event(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            records.append(json.loads(line))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay event pack")
    parser.add_argument("path", help="path to records.jsonl")
    args = parser.parse_args()
    records = replay_event(Path(args.path))
    print(f"Loaded {len(records)} records")


if __name__ == "__main__":
    main()
