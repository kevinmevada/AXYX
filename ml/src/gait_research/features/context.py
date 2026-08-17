"""Cycle context for label-blind feature extraction."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


ID_COLUMNS = (
    "cycle_id",
    "subject_id",
    "session_id",
    "trial_id",
    "side",
    "start_frame",
    "end_frame",
    "duration_seconds",
)

# Explicitly excluded from feature construction.
LABEL_COLUMNS = ("victimized", "victim_type", "times", "cyber_bullied", "survey_subject_no")


@dataclass
class CycleRecord:
    cycle_id: str
    subject_id: str
    session_id: str
    trial_id: str
    side: str
    start_frame: float
    end_frame: float
    duration_seconds: float
    sampling_rate_hz: float
    ipsilateral_foot_off_frame: object
    opposite_contact_frame: object
    opposite_foot_off_frame: object
    mid_stance_frame: object
    signals: dict[str, np.ndarray]  # name -> (101, 3)


def dt_seconds(record: CycleRecord) -> float:
    if not np.isfinite(record.duration_seconds) or record.duration_seconds <= 0:
        return float("nan")
    return float(record.duration_seconds / 100.0)


def inventory_without_labels(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    drop = [c for c in LABEL_COLUMNS if c in df.columns]
    return df.drop(columns=drop)
