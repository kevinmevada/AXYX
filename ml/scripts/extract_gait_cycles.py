"""Phase 1 read-only gait-cycle extraction.

Never modifies data/raw or data/processed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.phase1 import render_phase1_console, run_phase1, write_phase1_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="AXYS ML Phase 1 gait cycle engine (read-only)")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()

    result = run_phase1(root)
    paths = write_phase1_outputs(root, result)
    print(render_phase1_console(result))
    print("Wrote:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    return 0 if result.status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
