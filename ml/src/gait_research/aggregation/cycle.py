"""Cycle-level feature table helpers."""

from __future__ import annotations

import pandas as pd

from ..features.context import ID_COLUMNS


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in ID_COLUMNS]
