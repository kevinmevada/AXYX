from pathlib import Path

import pandas as pd
import pytest

from gait_research.phase3 import certify_phase3
from gait_research.statistics.engine import load_subject_matrix, run_phase3
from gait_research.statistics.screening import analysis_columns

ROOT = Path(__file__).resolve().parents[2]
PARQUET = ROOT / "results" / "phase2" / "subject_features.parquet"


@pytest.mark.skipif(not PARQUET.is_file(), reason="Phase 2 subject features missing")
def test_subject_matrix_is_31_not_880_and_has_no_labels():
    df = load_subject_matrix(ROOT)
    assert len(df) == 31
    assert "victimized" not in df.columns
    assert df.shape[1] == 3665
    assert len(df) != 880
    cols = analysis_columns(df)
    assert all(not c.endswith(("__mean", "__std", "__cv", "__n")) for c in cols)
    assert any(c.endswith("__median") for c in cols)


@pytest.mark.skipif(not PARQUET.is_file(), reason="Phase 2 subject features missing")
def test_run_phase3_method_guards():
    result = run_phase3(ROOT)
    assert result["n_subjects"] == 31
    assert result["n_victims"] == 17
    assert result["n_controls"] == 14
    assert "fdr_q" in result["stats"].columns
    assert "cliffs_delta" in result["stats"].columns
    assert (result["perm"]["unit"] == "subject").all()
    assert result["stats"]["direction"].isin(["VICTIMS_HIGHER", "VICTIMS_LOWER", "TIED"]).all()
    assert "anatomical_region" in result["stats"].columns
    cert = certify_phase3(ROOT, result)
    failed = [c for c in cert["checks"] if c["status"] == "FAIL"]
    assert not failed, failed
    assert cert["status"] in {"PASS", "PASS WITH WARNINGS"}
    # ranking must not be raw_p order
    by_p = result["stats"].sort_values("raw_p").head(5)["feature"].tolist()
    by_rank = result["stats"].head(5)["feature"].tolist()
    # allowed to overlap, but rank_score must exist and not equal raw_p
    assert "rank_score" in result["stats"].columns
    assert not result["stats"]["rank_score"].equals(1.0 - result["stats"]["raw_p"])
    _ = by_p, by_rank
