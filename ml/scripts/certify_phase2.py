"""Phase 2 certification. Does not modify data/raw or data/processed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.phase2_certify import (  # noqa: E402
    certify_phase2,
    render_cert_console,
    write_certification,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="AXYS ML Phase 2 certification")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()

    catalog_path = root / "results" / "phase2" / "feature_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    from gait_research.features.base import SGOLAY_POLY, SGOLAY_WINDOW
    from gait_research.features.registry import cycle_specs, subject_extra_specs

    catalog["smoothing"] = {
        **catalog.get("smoothing", {}),
        "derivative_filter": "savitzky_golay",
        "window": SGOLAY_WINDOW,
        "polyorder": SGOLAY_POLY,
        "nan_handling": {
            "rom_min_max_mean": "finite samples only; NaNs dropped, not imputed",
            "derivatives": "isolated NaNs linearly interpolated before Savitzky-Golay, then differentiated; documented, identical for all cycles, no labels",
        },
        "group_labels_used": False,
    }
    catalog["cycle_features"] = [s.to_dict() for s in cycle_specs()]
    catalog["subject_extra_features"] = [s.to_dict() for s in subject_extra_specs()]
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    payload = certify_phase2(root)
    paths = write_certification(root, payload)
    print(render_cert_console(payload))
    print("Wrote:")
    for k, p in paths.items():
        print(f"  {k}: {p}")
    return 0 if payload["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
