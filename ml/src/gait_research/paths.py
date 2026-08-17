"""Monorepo path helpers — ML outputs live under ml/; shared data under repo root."""

from __future__ import annotations

from pathlib import Path

# ml/
ML_ROOT = Path(__file__).resolve().parents[2]
# repo root (AXYX/)
REPO_ROOT = ML_ROOT.parent


def data_dir(_project_root: Path | None = None) -> Path:
    """Shared captures and survey Excel (repo data/, not ml/data/)."""
    return REPO_ROOT / "data"


def ml_project_root(project_root: Path | None = None) -> Path:
    """Root for ml/results, ml/docs, ml/scripts (defaults to ml/)."""
    if project_root is None:
        return ML_ROOT
    resolved = project_root.resolve()
    if resolved.name == "ml" or (resolved / "src" / "gait_research").is_dir():
        return resolved
    candidate = resolved / "ml"
    return candidate if candidate.is_dir() else ML_ROOT


def survey_xlsx(_project_root: Path | None = None) -> Path:
    return data_dir() / "raw" / "Victimization surveys.xlsx"


def processed_mat(_project_root: Path | None = None) -> Path:
    return data_dir() / "processed" / "Data_structure_all_subs.mat"


def raw_mat(_project_root: Path | None = None) -> Path:
    return data_dir() / "raw" / "Data_structure_all_subs.mat"
