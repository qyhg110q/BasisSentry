from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def generate_report(records: list[dict]) -> dict:
    basis_values = [r.get("basis_mark") for r in records if r.get("type") == "basis"]
    wall_events = [r for r in records if r.get("type") == "wall_event"]
    max_basis = max(basis_values) if basis_values else 0.0
    min_basis = min(basis_values) if basis_values else 0.0
    return {
        "records": len(records),
        "max_basis": max_basis,
        "min_basis": min_basis,
        "wall_events": len(wall_events),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate report from event pack")
    parser.add_argument("path", help="path to records.jsonl")
    parser.add_argument("--out", default="report.json", help="output report file")
    args = parser.parse_args()
    records = load_records(Path(args.path))
    report = generate_report(records)
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report written to {args.out}")


if __name__ == "__main__":
    main()
