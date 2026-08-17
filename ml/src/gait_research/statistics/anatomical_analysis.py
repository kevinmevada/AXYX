"""Anatomical roll-up of comparison results via Phase 2 catalog metadata."""

from __future__ import annotations

import pandas as pd

from ..features.anatomy import SIGNAL_ANATOMY
from ..features.registry import all_specs


def _base_name(feature: str) -> str:
    if feature.endswith("__median"):
        return feature[: -len("__median")]
    return feature


def attach_anatomy(comparisons: pd.DataFrame) -> pd.DataFrame:
    specs = {s.name: s for s in all_specs()}
    regions = []
    families = []
    sides = []
    sources = []
    for feat in comparisons["feature"]:
        base = _base_name(str(feat))
        spec = specs.get(base)
        if spec is None:
            # var_/sym_ already catalogued under full name
            spec = specs.get(str(feat))
        if spec is None:
            regions.append("unknown")
            families.append("unknown")
            sides.append("unknown")
            sources.append("")
            continue
        src = spec.source_signal.split("|")[0]
        ana = SIGNAL_ANATOMY.get(src, {})
        regions.append(spec.anatomical_region or ana.get("region", "unknown"))
        families.append(spec.family)
        sides.append(spec.side)
        sources.append(spec.source_signal)
    out = comparisons.copy()
    out["anatomical_region"] = regions
    out["family"] = families
    out["side"] = sides
    out["source_signal"] = sources
    return out


def anatomical_summary(df: pd.DataFrame, *, fdr_alpha: float = 0.10, delta_min: float = 0.33) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows = []
    for region, part in df.groupby("anatomical_region"):
        strong = part.loc[part["cliffs_delta"].abs() >= delta_min]
        fdr_hit = part.loc[part.get("fdr_q", pd.Series(dtype=float)) <= fdr_alpha] if "fdr_q" in part.columns else part.iloc[0:0]
        rows.append(
            {
                "anatomical_region": region,
                "n_features": int(len(part)),
                "n_medium_or_large_effect": int(len(strong)),
                "n_fdr_pass": int(len(fdr_hit)),
                "median_abs_cliffs_delta": float(part["cliffs_delta"].abs().median()),
                "max_abs_cliffs_delta": float(part["cliffs_delta"].abs().max()),
            }
        )
    return pd.DataFrame(rows).sort_values("max_abs_cliffs_delta", ascending=False)
