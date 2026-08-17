from pathlib import Path

import pandas as pd
import pytest

from gait_research.features.context import LABEL_COLUMNS

ROOT = Path(__file__).resolve().parents[2]
CYCLE_PATH = ROOT / "results" / "phase2" / "cycle_features.parquet"
SUBJECT_PATH = ROOT / "results" / "phase2" / "subject_features.parquet"


@pytest.mark.skipif(not CYCLE_PATH.is_file(), reason="Phase 2 outputs not generated")
def test_real_cycle_table():
    df = pd.read_parquet(CYCLE_PATH)
    assert len(df) == 880
    assert df["cycle_id"].nunique() == 880
    assert df["subject_id"].nunique() == 31
    for col in LABEL_COLUMNS:
        assert col not in df.columns
    assert "LKneeAngles_ax1_rom" in df.columns
    assert "cycle_duration_s" in df.columns
    assert df["LKneeAngles_ax1_rom"].notna().all()


@pytest.mark.skipif(not SUBJECT_PATH.is_file(), reason="Phase 2 outputs not generated")
def test_real_subject_table():
    df = pd.read_parquet(SUBJECT_PATH)
    assert len(df) == 31
    for col in LABEL_COLUMNS:
        assert col not in df.columns
    assert "LKneeAngles_ax1_rom__median" in df.columns
    assert df["n_cycles"].sum() == 880
