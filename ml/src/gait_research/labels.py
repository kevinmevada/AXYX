"""Female survey labels keyed by MATLAB subject field (S14, ...)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_female_labels(xlsx_path: Path) -> pd.DataFrame:
    raw = pd.read_excel(xlsx_path, header=0)
    raw = raw.rename(
        columns={
            "Subject No": "survey_subject_no",
            "SEX": "sex",
            "VICTIMIZED": "victimized",
            "IF YES - person/online/both/ND/NO": "victim_type",
            "How many times ": "times",
            "CYBER BULLIED": "cyber_bullied",
            "No": "roster_no",
        }
    )
    for col in ("sex", "victimized", "victim_type", "times", "cyber_bullied"):
        if col in raw.columns:
            raw[col] = raw[col].apply(lambda x: "" if pd.isna(x) else str(x).strip())
    females = raw[raw["sex"] == "F"].copy()
    females["survey_subject_no"] = pd.to_numeric(females["survey_subject_no"], errors="coerce")
    females["subject_id"] = females["survey_subject_no"].apply(
        lambda n: f"S{int(n)}" if pd.notna(n) else ""
    )
    return females
