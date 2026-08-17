from pathlib import Path

import pandas as pd
import pytest

from gait_research.phase5 import certify_phase5
from gait_research.within_victim.engine import run_phase5
from gait_research.phenotypes.representation import assert_no_labels

ROOT = Path(__file__).resolve().parents[2]
PARQUET = ROOT / "results" / "phase2" / "subject_features.parquet"


@pytest.mark.skipif(not PARQUET.is_file(), reason="Phase 2 outputs missing")
def test_live_phase5_guards():
    result = run_phase5(ROOT)
    assert result["n_victims"] == 17
    assert result["n_controls"] == 14
    assert result["n_subjects"] == 31
    assert result["similarity"]["unit"] == "subject"
    assert result["nn_perm"]["unit"] == "subject"
    assert "victimized" not in result["subgroups"]["assignments"].columns
    assert_no_labels(pd.DataFrame(result["rep"]["compact"], columns=result["rep"]["compact_names"]))
    cert = certify_phase5(result)
    failed = [c for c in cert["checks"] if c["status"] == "FAIL"]
    assert not failed, failed
    assert cert["status"] in {"PASS", "PASS WITH WARNINGS"}
    k = result["subgroups"]["choice"]["k"]
    if k is None:
        assert (result["subgroups"]["assignments"]["subgroup"] == "none_stable").all()
        assert len(result["vs_controls_compact"]) == 0
    else:
        assert result["subgroups"]["assignments"]["subgroup"].nunique() == k
        assert (result["vs_controls_compact"]["unit"] == "subject").all()
