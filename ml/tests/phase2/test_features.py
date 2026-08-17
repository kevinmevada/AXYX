import numpy as np
import pandas as pd

from gait_research.aggregation.subject import aggregate_subjects
from gait_research.features.base import event_pct, series_stats
from gait_research.features.context import LABEL_COLUMNS, CycleRecord
from gait_research.features.kinematic import extract as kin_extract
from gait_research.features.registry import all_specs, cycle_specs
from gait_research.features.temporal import extract as temp_extract


def _record(signals, duration=1.0, side="L") -> CycleRecord:
    return CycleRecord(
        cycle_id="TEST_L_01",
        subject_id="S99",
        session_id="WU01",
        trial_id="S99/WU01",
        side=side,
        start_frame=0,
        end_frame=100,
        duration_seconds=duration,
        sampling_rate_hz=100,
        ipsilateral_foot_off_frame=60,
        opposite_contact_frame=50,
        opposite_foot_off_frame=10,
        mid_stance_frame=30,
        signals=signals,
    )


def test_constant_series_rom_zero():
    stats = series_stats(np.full(101, 5.0))
    assert stats["rom"] == 0
    assert stats["mean"] == 5
    assert stats["std"] == 0


def test_linear_series_rom_100():
    x = np.linspace(0, 100, 101)
    stats = series_stats(x)
    assert stats["rom"] == 100
    assert stats["min"] == 0
    assert stats["max"] == 100


def test_sine_rom_about_2():
    t = np.linspace(0, 2 * np.pi, 101)
    stats = series_stats(np.sin(t))
    assert abs(stats["max"] - 1) < 1e-6
    assert abs(stats["min"] + 1) < 1e-6
    assert abs(stats["rom"] - 2) < 1e-6


def test_kinematic_on_synthetic_knee():
    knee = np.zeros((101, 3))
    knee[:, 0] = np.linspace(10, 50, 101)
    rec = _record({"LKneeAngles": knee})
    feats = kin_extract(rec)
    assert abs(feats["LKneeAngles_ax1_rom"] - 40) < 1e-6
    assert abs(feats["LKneeAngles_ax1_min"] - 10) < 1e-6
    assert abs(feats["LKneeAngles_ax1_max"] - 50) < 1e-6
    assert abs(feats["LKneeAngles_ax1_tmax_pct"] - 100) < 1e-6
    assert abs(feats["LKneeAngles_ax1_tmin_pct"] - 0) < 1e-6


def test_temporal_foot_off_percent():
    rec = _record({"LKneeAngles": np.zeros((101, 3))}, duration=1.0)
    feats = temp_extract(rec)
    assert abs(feats["foot_off_pct"] - 60.0) < 1e-9
    assert abs(feats["stance_pct"] - 60.0) < 1e-9
    assert abs(feats["cycle_duration_s"] - 1.0) < 1e-9


def test_event_pct_helper():
    assert abs(event_pct(88, 15, 127) - (88 - 15) / 112 * 100) < 1e-9


def test_registry_unique_names():
    names = [s.name for s in all_specs()]
    assert len(names) == len(set(names))
    assert any(s.family == "kinematic" for s in cycle_specs())
    assert any(s.family == "symmetry" for s in all_specs())


def test_subject_aggregation_median_and_no_labels():
    df = pd.DataFrame(
        {
            "cycle_id": ["a", "b", "c"],
            "subject_id": ["S1", "S1", "S1"],
            "session_id": ["WU01"] * 3,
            "trial_id": ["S1/WU01"] * 3,
            "side": ["L", "L", "R"],
            "start_frame": [1, 2, 3],
            "end_frame": [10, 20, 30],
            "duration_seconds": [1.0, 1.0, 1.0],
            "LKneeAngles_ax1_rom": [41.0, 42.0, 97.0],
            "RKneeAngles_ax1_rom": [40.0, 40.0, 41.0],
            "cycle_duration_s": [1.0, 1.0, 1.0],
        }
    )
    out = aggregate_subjects(df)
    assert len(out) == 1
    assert abs(out.loc[0, "LKneeAngles_ax1_rom__median"] - 42.0) < 1e-9
    for col in LABEL_COLUMNS:
        assert col not in out.columns
    assert "sym_KneeAngles_ax1_rom_absdiff" in out.columns
    assert abs(out.loc[0, "sym_KneeAngles_ax1_rom_absdiff"] - abs(41.5 - 41.0)) < 1e-9
