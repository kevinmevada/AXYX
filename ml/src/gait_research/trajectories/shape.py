"""Predefined trajectory-shape descriptors. Savitzky-Golay matches Phase 2."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from ..features.base import SGOLAY_POLY, SGOLAY_WINDOW, smooth_series
from ..statistics.effect_sizes import cliffs_delta
from ..statistics.multiple_testing import benjamini_hochberg


def shape_row(y: np.ndarray) -> dict:
    y = np.asarray(y, dtype=float)
    finite = np.isfinite(y)
    out = {
        "peak_magnitude": float("nan"),
        "peak_timing_pct": float("nan"),
        "min_magnitude": float("nan"),
        "min_timing_pct": float("nan"),
        "n_extrema": float("nan"),
        "vel_rms": float("nan"),
        "mean_abs_accel": float("nan"),
    }
    if finite.sum() < SGOLAY_WINDOW:
        return out
    sm = smooth_series(y)
    imax = int(np.nanargmax(sm))
    imin = int(np.nanargmin(sm))
    out["peak_magnitude"] = float(sm[imax])
    out["peak_timing_pct"] = float(imax)
    out["min_magnitude"] = float(sm[imin])
    out["min_timing_pct"] = float(imin)
    vel = np.gradient(sm)
    acc = np.gradient(vel)
    out["vel_rms"] = float(np.sqrt(np.nanmean(vel * vel)))
    out["mean_abs_accel"] = float(np.nanmean(np.abs(acc)))
    sgn = np.sign(vel)
    sgn[sgn == 0] = np.nan
    d = np.diff(sgn)
    out["n_extrema"] = float(np.nansum(np.abs(d) > 0))
    return out


def shape_table(X: np.ndarray, subject_id: np.ndarray, victim: np.ndarray, channel: str) -> pd.DataFrame:
    rows = []
    for i, sid in enumerate(subject_id):
        rec = shape_row(X[i])
        rec["subject_id"] = sid
        rec["victimized"] = "Y" if victim[i] else "N"
        rec["channel"] = channel
        rec["sgolay_window"] = SGOLAY_WINDOW
        rec["sgolay_poly"] = SGOLAY_POLY
        rows.append(rec)
    return pd.DataFrame(rows)


def compare_shape(df: pd.DataFrame, metrics: tuple[str, ...]) -> pd.DataFrame:
    rows = []
    for ch, g in df.groupby("channel"):
        v = g[g["victimized"] == "Y"]
        c = g[g["victimized"] == "N"]
        for m in metrics:
            xv = pd.to_numeric(v[m], errors="coerce").to_numpy()
            xc = pd.to_numeric(c[m], errors="coerce").to_numpy()
            xv, xc = xv[np.isfinite(xv)], xc[np.isfinite(xc)]
            p = float("nan")
            if xv.size >= 2 and xc.size >= 2:
                try:
                    p = float(mannwhitneyu(xv, xc, alternative="two-sided").pvalue)
                except ValueError:
                    p = float("nan")
            rows.append(
                {
                    "channel": ch,
                    "metric": m,
                    "victim_median": float(np.median(xv)) if xv.size else float("nan"),
                    "control_median": float(np.median(xc)) if xc.size else float("nan"),
                    "cliffs_delta": cliffs_delta(xv, xc),
                    "raw_p": p,
                }
            )
    out = pd.DataFrame(rows)
    if len(out):
        out["fdr_q"] = benjamini_hochberg(out["raw_p"].to_numpy())
    return out
