from pathlib import Path

import numpy as np
import pytest

from gait_research.phase6 import certify_phase6
from gait_research.trajectories.engine import run_phase6
from gait_research.trajectories.load import load_normalized_cube

ROOT = Path(__file__).resolve().parents[2]
NPZ = ROOT / "results" / "phase1" / "gait_cycles" / "normalized_core.npz"


@pytest.mark.skipif(not NPZ.is_file(), reason="Phase 1 trajectories missing")
def test_load_880_x_101():
    blob = load_normalized_cube(ROOT)
    assert blob["cube"].shape[0] == 880
    assert blob["cube"].shape[2] == 101
    assert blob["cube"].shape[3] == 3


@pytest.mark.skipif(not NPZ.is_file(), reason="Phase 1 trajectories missing")
def test_live_pipeline_subject_level():
    result = run_phase6(ROOT, n_perm_primary=199, n_perm_secondary=99, n_boot=50)
    assert result["n_subjects"] == 31
    assert result["n_cycles"] == 880
    assert result["n_time"] == 101
    assert result["agg"]["median"].shape[0] == 31
    cert = certify_phase6(result)
    failed = [c for c in cert["checks"] if c["status"] == "FAIL"]
    assert not failed, failed
    # n is subjects, not cycles
    assert result["victim"].sum() == 17
    assert (~result["victim"]).sum() == 14
