"""Phase 2 read-only feature extraction. Does not modify data/ or use labels."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.phase2 import render_phase2_console, run_phase2, write_phase2_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="AXYS ML Phase 2 feature engine (label-blind)")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    result = run_phase2(root)
    paths = write_phase2_outputs(root, result)
    print(render_phase2_console(result))
    print("Wrote:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    leaked = "victimized" in result["cycle_df"].columns or "victimized" in result["subject_df"].columns
    n_ok = len(result["cycle_df"]) == result["n_records"] == 880
    return 1 if leaked or not n_ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
