"""Phase 0 read-only dataset audit.

Never modifies data/raw or data/processed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.audit import render_console, run_audit, write_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="AXYS ML Phase 0 dataset audit (read-only)")
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Project root containing data/, results/, docs/",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    result = run_audit(root)
    paths = write_outputs(root, result)
    print(render_console(result))
    print("Wrote:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    return 0 if result.status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
