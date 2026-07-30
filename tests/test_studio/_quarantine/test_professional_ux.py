"""Tests for professional UX services (cohorts, reports)."""

from __future__ import annotations

from pathlib import Path

from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.services.cohort_service import CohortService
from motion_engine.studio.services.export_service import ExportService
from motion_engine.studio.services.motion_service import MotionService


def test_cohort_catalog_annotates_subjects() -> None:
    service = CohortService()
    subjects = [
        SubjectModel(subject_id="S2", session_count=1),
        SubjectModel(subject_id="S14", session_count=1),
        SubjectModel(subject_id="S99", session_count=1),
    ]
    annotated = service.annotate(subjects)
    assert annotated[0].cohort == "Healthy"
    assert annotated[1].cohort == "Parkinson's"
    assert annotated[2].cohort is None
    rows = service.explorer_tree(annotated)
    assert rows[0]["name"] == "Dataset"
    assert any("Parkinson" in r["name"] for r in rows)


def test_clinical_report_pdf(tmp_path: Path) -> None:
    service = ExportService(MotionService())
    out = service.export_clinical_report(
        tmp_path / "report.pdf",
        fields={"subject": "S2", "session": "WU01", "cadence": 110},
    )
    assert out.exists()
    assert out.stat().st_size > 100
