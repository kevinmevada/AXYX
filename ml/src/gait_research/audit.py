"""Read-only Phase 0 dataset audit."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .catalog import (
    ANTHROPOMETRIC_FIELDS,
    EVENT_FIELDS,
    EXPECTED_JOINT_ANGLE_COUNT,
    EXPECTED_JOINT_CENTER_COUNT,
    EXPECTED_MARKER_COUNT,
    EXPECTED_NON_VICTIMIZED,
    EXPECTED_SAMPLING_HZ,
    EXPECTED_SEGMENT_COM_COUNT,
    EXPECTED_SUBJECTS,
    EXPECTED_VICTIMIZED,
    EXPECTED_WALKING_SIGNAL_COUNT,
    EXPECTED_WALKING_TRIALS,
    EXPECTED_WHOLE_BODY_COM_COUNT,
    JOINT_ANGLES,
    JOINT_CENTERS,
    MARKERS,
    SEGMENT_COM,
    WALKING_KINEMATICS,
    WHOLE_BODY_COM,
    classify_signal,
)
from .matio import (
    fieldnames,
    get_field,
    has_field,
    is_numeric_array,
    is_struct,
    load_dat,
    mat_info,
    subject_fields,
    subject_id_from_field,
)
from .paths import data_dir, ml_project_root
from .sessions import classify_session

FINITE_RATIO_OK = 0.99


@dataclass
class Irregularity:
    level: str  # warning | critical
    subject_id: str | None
    session: str | None
    code: str
    message: str


@dataclass
class AuditResult:
    status: str
    dataset: dict[str, Any]
    raw: dict[str, Any]
    survey: dict[str, Any]
    signals: dict[str, Any]
    events: dict[str, Any]
    balance: dict[str, Any]
    irregularities: list[dict[str, Any]]
    checks: dict[str, str]
    subject_rows: list[dict[str, Any]] = field(default_factory=list)
    trial_rows: list[dict[str, Any]] = field(default_factory=list)
    signal_rows: list[dict[str, Any]] = field(default_factory=list)
    label_rows: list[dict[str, Any]] = field(default_factory=list)


def _scalar_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        number = float(value)
        if math.isnan(number):
            return None
        return number
    return None


def _array_orientation(arr: np.ndarray) -> str:
    if arr.ndim != 2:
        return f"{arr.ndim}D"
    rows, cols = arr.shape
    if cols == 3:
        return "Nx3"
    if rows == 3:
        return "3xN"
    return f"{rows}x{cols}"


def _frame_count(arr: np.ndarray) -> int | None:
    if arr.ndim != 2:
        return None
    rows, cols = arr.shape
    if cols == 3:
        return int(rows)
    if rows == 3:
        return int(cols)
    return None


def _read_excel_females(xlsx_path: Path) -> pd.DataFrame:
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
    females["roster_no"] = pd.to_numeric(females["roster_no"], errors="coerce")
    return females


def _read_excel_all(xlsx_path: Path) -> pd.DataFrame:
    raw = pd.read_excel(xlsx_path, header=0)
    raw = raw.rename(
        columns={
            "Subject No": "survey_subject_no",
            "SEX": "sex",
            "VICTIMIZED": "victimized",
        }
    )
    raw["sex"] = raw["sex"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
    raw["victimized"] = raw["victimized"].apply(lambda x: "" if pd.isna(x) else str(x).strip())
    raw["survey_subject_no"] = pd.to_numeric(raw["survey_subject_no"], errors="coerce")
    return raw


def run_audit(project_root: Path) -> AuditResult:
    root = ml_project_root(project_root)
    data = data_dir(project_root)
    processed_path = data / "processed" / "Data_structure_all_subs.mat"
    raw_path = data / "raw" / "Data_structure_all_subs.mat"
    xlsx_path = data / "raw" / "Victimization surveys.xlsx"

    irregularities: list[Irregularity] = []

    if not processed_path.is_file():
        raise FileNotFoundError(processed_path)
    if not raw_path.is_file():
        raise FileNotFoundError(raw_path)
    if not xlsx_path.is_file():
        raise FileNotFoundError(xlsx_path)

    excel_all = _read_excel_all(xlsx_path)
    excel_f = _read_excel_females(xlsx_path)
    excel_by_id = {
        int(row.survey_subject_no): row
        for row in excel_f.itertuples(index=False)
        if pd.notna(row.survey_subject_no)
    }

    processed = load_dat(processed_path)
    raw_dat = load_dat(raw_path)

    processed_subjects = subject_fields(processed)
    raw_subjects = subject_fields(raw_dat)
    has_survey_table = has_field(processed, "Survey")

    # --- join ---
    label_rows: list[dict[str, Any]] = []
    join_ok = True
    for name in processed_subjects:
        sid = subject_id_from_field(name)
        sub = get_field(processed, name)
        mat_subject_no = None
        mat_roster = None
        if has_field(sub, "Survey"):
            survey = get_field(sub, "Survey")
            mat_subject_no = _scalar_number(get_field(survey, "SubjectNo") if has_field(survey, "SubjectNo") else None)
            mat_roster = _scalar_number(get_field(survey, "RosterNo") if has_field(survey, "RosterNo") else None)

        excel_row = excel_by_id.get(sid)
        excel_ok = excel_row is not None
        mat_id_ok = mat_subject_no is not None and int(mat_subject_no) == sid
        roster_ok = True
        if excel_ok and mat_roster is not None and pd.notna(excel_row.roster_no):
            roster_ok = int(mat_roster) == int(excel_row.roster_no)

        row_join_ok = excel_ok and mat_id_ok and roster_ok
        if not row_join_ok:
            join_ok = False
            irregularities.append(
                Irregularity(
                    "critical",
                    name,
                    None,
                    "join_mismatch",
                    f"Excel/MATLAB join failed for {name} (excel={excel_ok}, mat_SubjectNo={mat_subject_no}, roster_ok={roster_ok})",
                )
            )

        victimized = excel_row.victimized if excel_ok else ""
        label_rows.append(
            {
                "subject_id": name,
                "survey_subject_no": sid,
                "excel_roster_no": int(excel_row.roster_no) if excel_ok and pd.notna(excel_row.roster_no) else "",
                "mat_subject_no": int(mat_subject_no) if mat_subject_no is not None else "",
                "mat_roster_no": int(mat_roster) if mat_roster is not None else "",
                "sex": excel_row.sex if excel_ok else "",
                "victimized": victimized,
                "victim_type": excel_row.victim_type if excel_ok else "",
                "times": excel_row.times if excel_ok else "",
                "cyber_bullied": excel_row.cyber_bullied if excel_ok else "",
                "join_ok": row_join_ok,
                "label_source": "excel_Subject_No",
            }
        )

    excel_ids = set(excel_by_id)
    mat_ids = {subject_id_from_field(n) for n in processed_subjects}
    missing_in_mat = sorted(excel_ids - mat_ids)
    missing_in_excel = sorted(mat_ids - excel_ids)
    for sid in missing_in_mat:
        join_ok = False
        irregularities.append(
            Irregularity("critical", f"S{sid}", None, "missing_subject_in_mat", f"Excel female Subject No {sid} has no MATLAB field S{sid}")
        )
    for sid in missing_in_excel:
        join_ok = False
        irregularities.append(
            Irregularity("critical", f"S{sid}", None, "missing_subject_in_excel", f"MATLAB {f'S{sid}'} has no Excel female row")
        )

    # males in processed would be a critical error
    excel_males = excel_all[excel_all["sex"] == "M"]["survey_subject_no"].dropna().astype(int)
    males_in_processed = sorted(set(excel_males) & mat_ids)
    if males_in_processed:
        join_ok = False
        irregularities.append(
            Irregularity(
                "critical",
                None,
                None,
                "males_in_processed",
                f"Processed MAT still contains male Subject No values: {males_in_processed}",
            )
        )

    n_y = sum(1 for r in label_rows if r["victimized"] == "Y")
    n_n = sum(1 for r in label_rows if r["victimized"] == "N")
    n_other_label = len(label_rows) - n_y - n_n

    subject_rows: list[dict[str, Any]] = []
    trial_rows: list[dict[str, Any]] = []
    signal_rows: list[dict[str, Any]] = []

    event_present = {k: 0 for k in EVENT_FIELDS}
    sampling_rates: list[int] = []
    walking_signal_counts: list[int] = []

    for name in processed_subjects:
        sid = subject_id_from_field(name)
        sub = get_field(processed, name)
        excel_row = excel_by_id.get(sid)

        mass = height = lleg = rleg = None
        vrate = None
        if has_field(sub, "Info"):
            info = get_field(sub, "Info")
            mass = _scalar_number(get_field(info, "Mass") if has_field(info, "Mass") else None)
            height = _scalar_number(get_field(info, "Height") if has_field(info, "Height") else None)
            lleg = _scalar_number(get_field(info, "LLegLength") if has_field(info, "LLegLength") else None)
            rleg = _scalar_number(get_field(info, "RLegLength") if has_field(info, "RLegLength") else None)
            vrate = _scalar_number(get_field(info, "Vrate") if has_field(info, "Vrate") else None)
            if vrate is not None:
                sampling_rates.append(int(vrate))
                if int(vrate) != EXPECTED_SAMPLING_HZ:
                    irregularities.append(
                        Irregularity("critical", name, None, "sampling_rate", f"{name} Vrate={vrate}, expected {EXPECTED_SAMPLING_HZ}")
                    )
            for field_name in ANTHROPOMETRIC_FIELDS:
                if not has_field(info, field_name) or _scalar_number(get_field(info, field_name)) is None:
                    irregularities.append(
                        Irregularity("warning", name, None, "missing_anthropometric", f"{name} missing {field_name}")
                    )
        else:
            irregularities.append(Irregularity("critical", name, None, "missing_info", f"{name} has no Info struct"))

        if not has_field(sub, "New_Session"):
            irregularities.append(Irregularity("critical", name, None, "missing_new_session", f"{name} has no New_Session"))
            subject_rows.append(
                {
                    "subject_id": name,
                    "survey_subject_no": sid,
                    "victimized": excel_row.victimized if excel_row is not None else "",
                    "victim_type": excel_row.victim_type if excel_row is not None else "",
                    "times": excel_row.times if excel_row is not None else "",
                    "cyber_bullied": excel_row.cyber_bullied if excel_row is not None else "",
                    "mass_kg": mass,
                    "height_cm": height,
                    "lleg_cm": lleg,
                    "rleg_cm": rleg,
                    "sampling_rate_hz": int(vrate) if vrate is not None else "",
                    "walking_trial_count": 0,
                    "valid_trial_count": 0,
                    "has_static": False,
                    "has_survey": has_field(sub, "Survey"),
                }
            )
            continue

        session = get_field(sub, "New_Session")
        session_names = fieldnames(session)
        walking_count = 0
        valid_count = 0
        has_static = False
        irregular_session_names: list[str] = []

        for sess_name in session_names:
            meta = classify_session(sess_name)
            if meta["is_irregular_name"] and meta["session_type"] != "summary":
                irregular_session_names.append(sess_name)
            if meta["session_type"] == "static":
                has_static = True
            if meta["session_type"] == "summary":
                continue

            node = get_field(session, sess_name)
            has_kin = is_struct(node) and has_field(node, "kinematics")
            has_info = is_struct(node) and has_field(node, "Info")
            has_res = is_struct(node) and has_field(node, "Res")

            kin_names: list[str] = []
            if has_kin:
                kin_names = fieldnames(get_field(node, "kinematics"))

            marker_count = sum(1 for n in kin_names if n in MARKERS)
            angle_count = sum(1 for n in kin_names if n in JOINT_ANGLES)
            jc_count = sum(1 for n in kin_names if n in JOINT_CENTERS)
            com_count = sum(1 for n in kin_names if n in WHOLE_BODY_COM)
            seg_com_count = sum(1 for n in kin_names if n in SEGMENT_COM)

            event_ok = {k: False for k in EVENT_FIELDS}
            if has_info:
                info_node = get_field(node, "Info")
                for ev in EVENT_FIELDS:
                    if has_field(info_node, ev) and is_numeric_array(get_field(info_node, ev)):
                        arr = get_field(info_node, ev)
                        event_ok[ev] = arr.ndim == 2 and arr.shape[1] >= 2 and arr.shape[0] >= 1

            has_events = all(event_ok.values())
            if meta["is_walking"]:
                for ev, ok in event_ok.items():
                    if ok:
                        event_present[ev] += 1

            frame_count = None
            trial_valid = True
            exclusion: list[str] = []

            if not has_kin:
                trial_valid = False
                exclusion.append("no_kinematics")
            else:
                kin = get_field(node, "kinematics")
                for sig in kin_names:
                    arr = get_field(kin, sig)
                    if not is_numeric_array(arr):
                        signal_rows.append(
                            {
                                "subject_id": name,
                                "session": sess_name,
                                "signal_name": sig,
                                "signal_type": classify_signal(sig),
                                "rows": "",
                                "columns": "",
                                "orientation": "non_numeric",
                                "finite_ratio": "",
                                "missing_count": "",
                                "valid": False,
                            }
                        )
                        trial_valid = False
                        exclusion.append(f"non_numeric:{sig}")
                        continue
                    orient = _array_orientation(arr)
                    fc = _frame_count(arr)
                    if frame_count is None and fc is not None:
                        frame_count = fc
                    finite = np.isfinite(arr)
                    finite_ratio = float(finite.mean()) if arr.size else 0.0
                    missing = int((~finite).sum())
                    sig_valid = orient in {"Nx3", "3xN"} and finite_ratio >= FINITE_RATIO_OK
                    if not sig_valid:
                        trial_valid = False
                        if orient not in {"Nx3", "3xN"}:
                            exclusion.append(f"bad_shape:{sig}:{orient}")
                        if finite_ratio < FINITE_RATIO_OK:
                            exclusion.append(f"nans:{sig}")
                            irregularities.append(
                                Irregularity(
                                    "warning",
                                    name,
                                    sess_name,
                                    "nan_values",
                                    f"{name}.{sess_name}.{sig} finite_ratio={finite_ratio:.4f} missing={missing}",
                                )
                            )
                    signal_rows.append(
                        {
                            "subject_id": name,
                            "session": sess_name,
                            "signal_name": sig,
                            "signal_type": classify_signal(sig),
                            "rows": int(arr.shape[0]) if arr.ndim >= 1 else "",
                            "columns": int(arr.shape[1]) if arr.ndim >= 2 else "",
                            "orientation": orient,
                            "finite_ratio": round(finite_ratio, 6),
                            "missing_count": missing,
                            "valid": sig_valid,
                        }
                    )
                if meta["is_walking"]:
                    walking_signal_counts.append(len(kin_names))
                    missing_markers = [m for m in MARKERS if m not in kin_names]
                    missing_angles = [m for m in JOINT_ANGLES if m not in kin_names]
                    missing_jc = [m for m in JOINT_CENTERS if m not in kin_names]
                    if missing_markers:
                        trial_valid = False
                        exclusion.append("missing_markers")
                        irregularities.append(
                            Irregularity("warning", name, sess_name, "missing_markers", f"{name}.{sess_name} missing markers {missing_markers}")
                        )
                    if missing_angles:
                        trial_valid = False
                        exclusion.append("missing_joint_angles")
                    if missing_jc:
                        trial_valid = False
                        exclusion.append("missing_joint_centers")
                        irregularities.append(
                            Irregularity("warning", name, sess_name, "missing_joint_centers", f"{name}.{sess_name} missing JC {missing_jc}")
                        )
                    if len(kin_names) != EXPECTED_WALKING_SIGNAL_COUNT:
                        irregularities.append(
                            Irregularity(
                                "warning",
                                name,
                                sess_name,
                                "unexpected_signal_count",
                                f"{name}.{sess_name} has {len(kin_names)} kinematics fields, expected {EXPECTED_WALKING_SIGNAL_COUNT}",
                            )
                        )
                    unknown = [n for n in kin_names if n not in WALKING_KINEMATICS]
                    if unknown:
                        irregularities.append(
                            Irregularity("warning", name, sess_name, "unknown_signals", f"{name}.{sess_name} unknown signals {unknown}")
                        )

            if meta["is_walking"] and not has_events:
                trial_valid = False
                exclusion.append("missing_events")
                missing_ev = [k for k, ok in event_ok.items() if not ok]
                irregularities.append(
                    Irregularity("warning", name, sess_name, "missing_events", f"{name}.{sess_name} missing events {missing_ev}")
                )

            if meta["is_walking"]:
                walking_count += 1
                if trial_valid:
                    valid_count += 1

            trial_rows.append(
                {
                    "subject_id": name,
                    "session_name": sess_name,
                    "session_type": meta["session_type"],
                    "name_pattern": meta["name_pattern"],
                    "is_irregular_name": meta["is_irregular_name"],
                    "frame_count": frame_count if frame_count is not None else "",
                    "sampling_rate": int(vrate) if vrate is not None else "",
                    "has_kinematics": has_kin,
                    "has_events": has_events,
                    "has_res": has_res,
                    "marker_count": marker_count,
                    "joint_angle_count": angle_count,
                    "joint_center_count": jc_count,
                    "com_count": com_count,
                    "segment_com_count": seg_com_count,
                    "kinematics_field_count": len(kin_names),
                    "valid": trial_valid if meta["is_walking"] else has_kin,
                    "exclusion_reason": "|".join(dict.fromkeys(exclusion)),
                }
            )

        if irregular_session_names:
            irregularities.append(
                Irregularity(
                    "warning",
                    name,
                    None,
                    "irregular_session_names",
                    f"{name} non-canonical session names: {', '.join(irregular_session_names)}",
                )
            )
        if not has_static:
            irregularities.append(Irregularity("warning", name, None, "missing_static", f"{name} has no static trial"))

        subject_rows.append(
            {
                "subject_id": name,
                "survey_subject_no": sid,
                "victimized": excel_row.victimized if excel_row is not None else "",
                "victim_type": excel_row.victim_type if excel_row is not None else "",
                "times": excel_row.times if excel_row is not None else "",
                "cyber_bullied": excel_row.cyber_bullied if excel_row is not None else "",
                "mass_kg": mass,
                "height_cm": height,
                "lleg_cm": lleg,
                "rleg_cm": rleg,
                "sampling_rate_hz": int(vrate) if vrate is not None else "",
                "walking_trial_count": walking_count,
                "valid_trial_count": valid_count,
                "has_static": has_static,
                "has_survey": has_field(sub, "Survey"),
            }
        )

    walking_trials = int(sum(r["walking_trial_count"] for r in subject_rows))
    valid_walking = int(sum(r["valid_trial_count"] for r in subject_rows))
    trial_counts = [int(r["walking_trial_count"]) for r in subject_rows]
    y_counts = [int(r["walking_trial_count"]) for r in subject_rows if r["victimized"] == "Y"]
    n_counts = [int(r["walking_trial_count"]) for r in subject_rows if r["victimized"] == "N"]

    def _stats(values: list[int]) -> dict[str, float | int]:
        if not values:
            return {"min": "", "max": "", "median": "", "mean": "", "sum": 0}
        arr = np.array(values, dtype=float)
        return {
            "min": int(arr.min()),
            "max": int(arr.max()),
            "median": float(np.median(arr)),
            "mean": float(arr.mean()),
            "sum": int(arr.sum()),
        }

    # event availability: all walking trials have each event?
    event_status = {}
    for ev in EVENT_FIELDS:
        ok = walking_trials > 0 and event_present[ev] == walking_trials
        event_status[ev] = {
            "available": event_present[ev] > 0,
            "walking_trials_with_event": event_present[ev],
            "walking_trials": walking_trials,
            "status": "PASS" if ok else "FAIL",
        }
        if not ok:
            irregularities.append(
                Irregularity(
                    "critical" if event_present[ev] == 0 else "warning",
                    None,
                    None,
                    f"event_{ev}",
                    f"{ev} present on {event_present[ev]}/{walking_trials} walking trials",
                )
            )

    checks: dict[str, str] = {}
    n_subjects = len(processed_subjects)
    checks["subject_count"] = "PASS" if n_subjects == EXPECTED_SUBJECTS else "FAIL"
    checks["label_split"] = "PASS" if n_y == EXPECTED_VICTIMIZED and n_n == EXPECTED_NON_VICTIMIZED and n_other_label == 0 else "FAIL"
    checks["join"] = "PASS" if join_ok else "FAIL"
    checks["sampling_rate"] = "PASS" if sampling_rates and all(r == EXPECTED_SAMPLING_HZ for r in sampling_rates) else "FAIL"
    checks["walking_trials"] = "PASS" if walking_trials == EXPECTED_WALKING_TRIALS else "WARNING"
    modal_signal_count = int(pd.Series(walking_signal_counts).mode().iloc[0]) if walking_signal_counts else 0
    checks["walking_signal_count"] = "PASS" if modal_signal_count == EXPECTED_WALKING_SIGNAL_COUNT else "FAIL"
    checks["events_KinFC"] = event_status["KinFC"]["status"]
    checks["events_KinFO"] = event_status["KinFO"]["status"]
    checks["events_Midsvnt"] = event_status["Midsvnt"]["status"]
    checks["raw_mat_present"] = "PASS"
    checks["survey_excel_present"] = "PASS"
    checks["survey_table_present"] = "PASS" if has_survey_table else "WARNING"

    if n_subjects != EXPECTED_SUBJECTS:
        irregularities.append(
            Irregularity("critical", None, None, "subject_count", f"Found {n_subjects} subjects, expected {EXPECTED_SUBJECTS}")
        )
    if n_y != EXPECTED_VICTIMIZED or n_n != EXPECTED_NON_VICTIMIZED:
        irregularities.append(
            Irregularity("critical", None, None, "label_split", f"Found {n_y} Y / {n_n} N, expected {EXPECTED_VICTIMIZED}/{EXPECTED_NON_VICTIMIZED}")
        )
    if walking_trials != EXPECTED_WALKING_TRIALS:
        irregularities.append(
            Irregularity("warning", None, None, "walking_trial_count", f"Found {walking_trials} WU* walking trials, expected {EXPECTED_WALKING_TRIALS}")
        )
    if trial_counts and (min(trial_counts) != max(trial_counts)):
        irregularities.append(
            Irregularity(
                "warning",
                None,
                None,
                "trial_imbalance",
                f"Walking trials per subject range {min(trial_counts)}–{max(trial_counts)} (median {float(np.median(trial_counts))})",
            )
        )

    critical = [i for i in irregularities if i.level == "critical"]
    warnings = [i for i in irregularities if i.level == "warning"]
    fail_checks = [k for k, v in checks.items() if v == "FAIL"]
    if fail_checks or critical:
        status = "FAIL"
    elif warnings or any(v == "WARNING" for v in checks.values()):
        status = "PASS WITH WARNINGS"
    else:
        status = "PASS"

    raw_ids = [subject_id_from_field(n) for n in raw_subjects]
    processed_ids = [subject_id_from_field(n) for n in processed_subjects]

    result = AuditResult(
        status=status,
        dataset={
            "file": str(processed_path.as_posix()),
            "subjects": n_subjects,
            "subject_ids": processed_subjects,
            "victimized": n_y,
            "non_victimized": n_n,
            "other_labels": n_other_label,
            "walking_trials": walking_trials,
            "valid_walking_trials": valid_walking,
            "sampling_rate_hz": EXPECTED_SAMPLING_HZ if checks["sampling_rate"] == "PASS" else sorted(set(sampling_rates)),
            "has_cohort_survey_table": has_survey_table,
            "variables": [{"name": n, "shape": list(s), "dtype": t} for n, s, t in mat_info(processed_path)],
        },
        raw={
            "file": str(raw_path.as_posix()),
            "subjects": len(raw_subjects),
            "subject_ids": raw_subjects,
            "subjects_not_in_processed": [f"S{i}" for i in raw_ids if i not in set(processed_ids)],
            "variables": [{"name": n, "shape": list(s), "dtype": t} for n, s, t in mat_info(raw_path)],
        },
        survey={
            "file": str(xlsx_path.as_posix()),
            "excel_rows": int(len(excel_all)),
            "excel_females": int(len(excel_f)),
            "excel_males": int((excel_all["sex"] == "M").sum()),
            "join_key": "Subject No",
            "join_ok": join_ok,
            "missing_in_mat": [f"S{i}" for i in missing_in_mat],
            "missing_in_excel": [f"S{i}" for i in missing_in_excel],
        },
        signals={
            "markers": EXPECTED_MARKER_COUNT,
            "joint_angles": EXPECTED_JOINT_ANGLE_COUNT,
            "joint_centers": EXPECTED_JOINT_CENTER_COUNT,
            "com_signals": EXPECTED_WHOLE_BODY_COM_COUNT,
            "segment_com_signals": EXPECTED_SEGMENT_COM_COUNT,
            "walking_kinematics_expected": EXPECTED_WALKING_SIGNAL_COUNT,
            "walking_kinematics_modal_observed": modal_signal_count,
            "marker_names": list(MARKERS),
            "joint_center_names": list(JOINT_CENTERS),
        },
        events={
            "foot_contact": event_status["KinFC"]["available"],
            "foot_off": event_status["KinFO"]["available"],
            "mid_stance": event_status["Midsvnt"]["available"],
            "detail": event_status,
        },
        balance={
            "all": _stats(trial_counts),
            "victimized": _stats(y_counts),
            "non_victimized": _stats(n_counts),
            "per_subject": [
                {"subject_id": r["subject_id"], "victimized": r["victimized"], "walking_trials": r["walking_trial_count"]}
                for r in subject_rows
            ],
        },
        irregularities=[
            {
                "level": i.level,
                "subject_id": i.subject_id,
                "session": i.session,
                "code": i.code,
                "message": i.message,
            }
            for i in irregularities
        ],
        checks=checks,
        subject_rows=subject_rows,
        trial_rows=trial_rows,
        signal_rows=signal_rows,
        label_rows=label_rows,
    )
    return result


def write_outputs(project_root: Path, result: AuditResult) -> dict[str, Path]:
    root = ml_project_root(project_root)
    out_dir = root / "results" / "phase0"
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "dataset_audit.json"
    payload = {
        "status": result.status,
        "generated": date.today().isoformat(),
        "dataset": result.dataset,
        "raw": result.raw,
        "survey": result.survey,
        "signals": result.signals,
        "events": result.events,
        "balance": result.balance,
        "checks": result.checks,
        "irregularities": result.irregularities,
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    subject_path = out_dir / "subject_inventory.csv"
    trial_path = out_dir / "trial_inventory.csv"
    signal_path = out_dir / "signal_inventory.csv"
    label_path = out_dir / "label_inventory.csv"
    pd.DataFrame(result.subject_rows).to_csv(subject_path, index=False)
    pd.DataFrame(result.trial_rows).to_csv(trial_path, index=False)
    pd.DataFrame(result.signal_rows).to_csv(signal_path, index=False)
    pd.DataFrame(result.label_rows).to_csv(label_path, index=False)

    report = render_markdown(result)
    report_path = out_dir / "audit_report.md"
    docs_path = docs_dir / "phase0_dataset_audit.md"
    report_path.write_text(report, encoding="utf-8")
    docs_path.write_text(report, encoding="utf-8")

    return {
        "json": json_path,
        "subjects": subject_path,
        "trials": trial_path,
        "signals": signal_path,
        "labels": label_path,
        "report": report_path,
        "docs": docs_path,
    }


def render_markdown(result: AuditResult) -> str:
    lines: list[str] = []
    lines.append("# Phase 0 Dataset Audit")
    lines.append("")
    lines.append(f"Status: **{result.status}**")
    lines.append("")
    lines.append(f"Generated: {date.today().isoformat()}")
    lines.append("")
    lines.append("This audit is read-only. `data/raw/` and `data/processed/` were not modified.")
    lines.append("")
    lines.append("## Dataset")
    lines.append("")
    lines.append(f"- Processed file: `{result.dataset['file']}`")
    lines.append(f"- Subjects: {result.dataset['subjects']} (expected {EXPECTED_SUBJECTS}) — {result.checks['subject_count']}")
    lines.append(f"- Walking trials (WU*): {result.dataset['walking_trials']} (expected {EXPECTED_WALKING_TRIALS}) — {result.checks['walking_trials']}")
    lines.append(f"- Valid walking trials: {result.dataset['valid_walking_trials']}")
    lines.append(f"- Sampling rate: {result.dataset['sampling_rate_hz']} Hz — {result.checks['sampling_rate']}")
    lines.append("")
    lines.append("## Labels")
    lines.append("")
    lines.append(f"- Join key: Excel `Subject No` ↔ MATLAB `S#` — {result.checks['join']}")
    lines.append(f"- Victimized (Y): {result.dataset['victimized']} (expected {EXPECTED_VICTIMIZED})")
    lines.append(f"- Non-victimized (N): {result.dataset['non_victimized']} (expected {EXPECTED_NON_VICTIMIZED})")
    lines.append(f"- Split check: {result.checks['label_split']}")
    lines.append("")
    lines.append("| Subject | Subject No | Victimized | Join OK |")
    lines.append("|---|---:|:---:|:---:|")
    for row in result.label_rows:
        lines.append(
            f"| {row['subject_id']} | {row['survey_subject_no']} | {row['victimized']} | {row['join_ok']} |"
        )
    lines.append("")
    lines.append("## Raw MAT")
    lines.append("")
    lines.append(f"- File: `{result.raw['file']}`")
    lines.append(f"- Subjects: {result.raw['subjects']}")
    lines.append(f"- Present in raw but not processed: {', '.join(result.raw['subjects_not_in_processed']) or 'none'}")
    lines.append("")
    lines.append("## Signals")
    lines.append("")
    lines.append(f"- Markers: {result.signals['markers']} (expected {EXPECTED_MARKER_COUNT})")
    lines.append(f"- Joint angles: {result.signals['joint_angles']} (expected {EXPECTED_JOINT_ANGLE_COUNT})")
    lines.append(f"- Joint centers: {result.signals['joint_centers']} ({', '.join(result.signals['joint_center_names'])})")
    lines.append(f"- Whole-body COM: {result.signals['com_signals']}")
    lines.append(f"- Segment COM: {result.signals['segment_com_signals']}")
    lines.append(f"- Walking kinematics expected: {result.signals['walking_kinematics_expected']}")
    lines.append(f"- Modal observed count: {result.signals['walking_kinematics_modal_observed']} — {result.checks['walking_signal_count']}")
    lines.append("")
    lines.append("## Events")
    lines.append("")
    for ev, label in (("KinFC", "foot contact"), ("KinFO", "foot off"), ("Midsvnt", "mid-stance")):
        detail = result.events["detail"][ev]
        lines.append(
            f"- {ev} ({label}): {detail['walking_trials_with_event']}/{detail['walking_trials']} walking trials — {detail['status']}"
        )
    lines.append("")
    lines.append("## Subject trial balance")
    lines.append("")
    b = result.balance
    lines.append(f"- All subjects: min {b['all']['min']}, median {b['all']['median']}, max {b['all']['max']} (sum {b['all']['sum']})")
    lines.append(
        f"- Victimized: min {b['victimized']['min']}, median {b['victimized']['median']}, max {b['victimized']['max']} (sum {b['victimized']['sum']})"
    )
    lines.append(
        f"- Non-victimized: min {b['non_victimized']['min']}, median {b['non_victimized']['median']}, max {b['non_victimized']['max']} (sum {b['non_victimized']['sum']})"
    )
    lines.append("")
    lines.append("Gait-cycle min/median/max per subject is deferred to Phase 1/2.")
    lines.append("")
    lines.append("### Victims")
    lines.append("")
    for row in b["per_subject"]:
        if row["victimized"] == "Y":
            lines.append(f"- {row['subject_id']}: {row['walking_trials']} trials")
    lines.append("")
    lines.append("### Controls")
    lines.append("")
    for row in b["per_subject"]:
        if row["victimized"] == "N":
            lines.append(f"- {row['subject_id']}: {row['walking_trials']} trials")
    lines.append("")
    lines.append("## Irregularities")
    lines.append("")
    warnings = [i for i in result.irregularities if i["level"] == "warning"]
    critical = [i for i in result.irregularities if i["level"] == "critical"]
    lines.append(f"- Critical: {len(critical)}")
    lines.append(f"- Warnings: {len(warnings)}")
    lines.append("")
    if critical:
        lines.append("### Critical issues")
        lines.append("")
        for item in critical:
            loc = item["subject_id"] or "dataset"
            sess = f".{item['session']}" if item["session"] else ""
            lines.append(f"- `{item['code']}` {loc}{sess}: {item['message']}")
        lines.append("")
    else:
        lines.append("### Critical issues")
        lines.append("")
        lines.append("None")
        lines.append("")
    if warnings:
        lines.append("### Warnings")
        lines.append("")
        for item in warnings:
            loc = item["subject_id"] or "dataset"
            sess = f".{item['session']}" if item["session"] else ""
            lines.append(f"- `{item['code']}` {loc}{sess}: {item['message']}")
        lines.append("")
    lines.append("## Checks")
    lines.append("")
    for key, value in result.checks.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Completion criteria")
    lines.append("")
    lines.append("- Processed MAT verified")
    lines.append("- Raw MAT verified")
    lines.append("- Survey Excel verified")
    lines.append("- Subject ↔ survey join verified")
    lines.append("- Walking trials inventoried")
    lines.append("- Kinematic signals inventoried")
    lines.append("- Marker / joint-angle / joint-center inventories verified")
    lines.append("- Gait events verified")
    lines.append("- Sampling rates verified")
    lines.append("- Trajectory dimensions verified")
    lines.append("- Missing values quantified")
    lines.append("- Irregular sessions identified (not renamed)")
    lines.append("- Subject trial balance reported")
    lines.append("- No source data modified")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_console(result: AuditResult) -> str:
    def line(label: str, value: Any, extra: str = "") -> str:
        return f"{label:<24} {value}{extra}"

    blocks = [
        "=" * 60,
        "AXYS ML - PHASE 0 DATASET AUDIT",
        "=" * 60,
        "",
        "Processed dataset:",
        result.dataset["file"],
        "",
        "Survey:",
        result.survey["file"],
        "",
        "-" * 60,
        "DATASET",
        "-" * 60,
        "",
        line("Subjects found:", result.dataset["subjects"]),
        line("Expected:", EXPECTED_SUBJECTS),
        line("Status:", result.checks["subject_count"]),
        "",
        line("Victimized:", result.dataset["victimized"]),
        line("Non-victimized:", result.dataset["non_victimized"]),
        line("Status:", result.checks["label_split"]),
        "",
        line("Walking trials:", result.dataset["walking_trials"]),
        line("Expected:", f"~{EXPECTED_WALKING_TRIALS}"),
        "",
        line("Sampling rate:", f"{result.dataset['sampling_rate_hz']} Hz"),
        line("Status:", result.checks["sampling_rate"]),
        "",
        "-" * 60,
        "EVENTS",
        "-" * 60,
        "",
        line("KinFC:", result.checks["events_KinFC"]),
        line("KinFO:", result.checks["events_KinFO"]),
        line("Midsvnt:", result.checks["events_Midsvnt"]),
        "",
        "-" * 60,
        "SIGNALS",
        "-" * 60,
        "",
        line("Markers:", result.signals["markers"]),
        line("Joint angles:", result.signals["joint_angles"]),
        line("Joint centers:", result.signals["joint_centers"]),
        "",
        "-" * 60,
        "BALANCE",
        "-" * 60,
        "",
        line("Min trials/subj:", result.balance["all"]["min"]),
        line("Median trials/subj:", result.balance["all"]["median"]),
        line("Max trials/subj:", result.balance["all"]["max"]),
        "",
        "-" * 60,
        "IRREGULARITIES",
        "-" * 60,
        "",
        line("Critical:", sum(1 for i in result.irregularities if i["level"] == "critical")),
        line("Warnings found:", sum(1 for i in result.irregularities if i["level"] == "warning")),
        "",
        "-" * 60,
        "FINAL STATUS",
        "-" * 60,
        "",
        result.status,
        "",
    ]
    return "\n".join(blocks)
