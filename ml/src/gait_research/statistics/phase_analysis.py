"""Gait-phase effect profiles. Uses already-computed subject-level comparisons."""

from __future__ import annotations

import re

import pandas as pd

PHASE_RE = re.compile(r"_phase_(\d+)_(\d+)_")


def phase_effects(comparisons: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in comparisons.iterrows():
        m = PHASE_RE.search(str(row["feature"]))
        if not m:
            continue
        lo, hi = int(m.group(1)), int(m.group(2))
        rec = row.to_dict()
        rec["phase_lo"] = lo
        rec["phase_hi"] = hi
        rec["phase_mid"] = 0.5 * (lo + hi)
        rows.append(rec)
    if not rows:
        return pd.DataFrame(columns=list(comparisons.columns) + ["phase_lo", "phase_hi", "phase_mid"])
    return pd.DataFrame(rows)
