from pathlib import Path

import pandas as pd
import pytest

from gait_research.phase4 import certify_phase4
from gait_research.phenotypes.engine import run_discovery, run_phase4
from gait_research.phenotypes.representation import assert_no_labels, build_representation

ROOT = Path(__file__).resolve().parents[2]
PARQUET = ROOT / "results" / "phase2" / "subject_features.parquet"
CLUSTERS = ROOT / "results" / "phase3" / "screening" / "redundancy_clusters.csv"


@pytest.mark.skipif(not (PARQUET.is_file() and CLUSTERS.is_file()), reason="Phase 2/3 outputs missing")
def test_representation_is_subject_level_and_compact():
    rep = build_representation(ROOT)
    assert rep["n_subjects"] == 31
    assert rep["compact"].shape[0] == 31
    assert 8 <= rep["compact"].shape[1] <= 100
    assert_no_labels(pd.DataFrame(rep["compact"], columns=rep["compact_names"]))
    assert "victimized" not in rep["raw_names"]


@pytest.mark.skipif(not (PARQUET.is_file() and CLUSTERS.is_file()), reason="Phase 2/3 outputs missing")
def test_discovery_then_labels():
    disc = run_discovery(ROOT)
    assert disc["n_subjects"] == 31
    assert "victimized" not in disc["assignments"].columns
    assert_no_labels(disc["compact_frame"])
    assert len(disc["metrics"]) >= 6
    assert (disc["stability"]["unit"] == "subject").all()
    result = run_phase4(ROOT)
    cert = certify_phase4(ROOT, result)
    failed = [c for c in cert["checks"] if c["status"] == "FAIL"]
    assert not failed, failed
    assert cert["status"] in {"PASS", "PASS WITH WARNINGS"}
    if result["choice"]["k"] is not None:
        assert "victimized" not in result["assignments"].columns
        assert (result["enrichment"]["unit"] == "subject").all()
        assert result["assignments"]["phenotype"].nunique() == result["choice"]["k"]
    else:
        assert len(result["enrichment"]) == 0
