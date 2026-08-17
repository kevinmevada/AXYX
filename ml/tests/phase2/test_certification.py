from pathlib import Path

import pytest

from gait_research.phase2_certify import certify_phase2

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(
    not (ROOT / "results" / "phase2" / "cycle_features.parquet").is_file(),
    reason="Phase 2 outputs missing",
)
def test_phase2_certification_has_no_failures():
    payload = certify_phase2(ROOT)
    failed = [c for c in payload["checks"] if c["status"] == "FAIL"]
    assert not failed, failed
    assert payload["counts"]["cycle_rows"] == 880
    assert payload["counts"]["subject_rows"] == 31
    assert payload["counts"]["cycle_feature_columns"] == 714
    assert payload["counts"]["subject_columns"] == 3665
    assert payload["counts"]["catalog_entries"] == 805
