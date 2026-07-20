"""CLI entry: python -m benchmarks.run_benchmarks"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure src/ is importable when run as a script from repo root.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from benchmarks.harness import run_suite  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AXYX rendering architecture benchmarks")
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--json", type=Path, default=None, help="Write report JSON")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )
    report = run_suite(repeats=args.repeats)
    for line in report.summary_lines():
        print(line)
    if args.json is not None:
        args.json.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        print(f"Wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
