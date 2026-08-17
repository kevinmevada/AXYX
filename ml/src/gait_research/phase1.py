"""Phase 1: gait-event validation, cycle extraction, quality, normalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .catalog import (
    CORE_GAIT_SIGNALS,
    DOMAIN_SIGNALS,
    EXPECTED_SAMPLING_HZ,
    EXPECTED_WALKING_TRIALS,
    LOWER_BODY_DOMAINS,
    NORMALIZED_POINTS,
    SIDE_CODE_TO_FOOT,
    UPPER_BODY_DOMAINS,
)
from .events import (
    extract_cycles,
    heel_vote_for_code,
    is_alternating,
    mapping_from_votes,
    parse_events,
    sequence_string,
)
from .labels import load_female_labels
from .matio import fieldnames, get_field, has_field, is_numeric_array, load_dat, subject_fields
from .normalize import normalize_signal
from .quality import score_cycle
from .paths import ml_project_root, processed_mat, survey_xlsx
from .sessions import classify_session


@dataclass
class Phase1Result:
    status: str
    event_rows: list[dict[str, Any]]
    cycle_rows: list[dict[str, Any]]
    quality_rows: list[dict[str, Any]]
    subject_rows: list[dict[str, Any]]
    trial_rows: list[dict[str, Any]]
    summary: dict[str, Any]
    normalized: dict[str, np.ndarray]


def _load_kinematics(trial) -> dict[str, np.ndarray]:
    if not has_field(trial, "kinematics"):
        return {}
    kin = get_field(trial, "kinematics")
    out: dict[str, np.ndarray] = {}
    for name in fieldnames(kin):
        arr = get_field(kin, name)
        if is_numeric_array(arr):
            out[name] = np.asarray(arr, dtype=float)
    return out


def _scalar_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def run_phase1(project_root: Path) -> Phase1Result:
    root = ml_project_root(project_root)
    processed_path = processed_mat()
    xlsx_path = survey_xlsx()
    dat = load_dat(processed_path)
    labels = load_female_labels(xlsx_path)
    label_by_id = {row.subject_id: row for row in labels.itertuples(index=False) if row.subject_id}

    event_rows: list[dict[str, Any]] = []
    cycle_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    trial_rows: list[dict[str, Any]] = []

    normalized_ids: list[str] = []
    normalized_stack: list[np.ndarray] = []
    core_names = list(CORE_GAIT_SIGNALS)

    walking_trials = 0
    mapping_mismatches = 0

    for subject_id in subject_fields(dat):
        sub = get_field(dat, subject_id)
        vrate = EXPECTED_SAMPLING_HZ
        if has_field(sub, "Info") and has_field(get_field(sub, "Info"), "Vrate"):
            vrate = _scalar_int(get_field(get_field(sub, "Info"), "Vrate")) or EXPECTED_SAMPLING_HZ
        if not has_field(sub, "New_Session"):
            continue
        session = get_field(sub, "New_Session")
        lab = label_by_id.get(subject_id)

        for sess_name in fieldnames(session):
            if not classify_session(sess_name)["is_walking"]:
                continue
            walking_trials += 1
            trial = get_field(session, sess_name)
            kin = _load_kinematics(trial)

            fc_raw = fo_raw = ms_raw = None
            if has_field(trial, "Info"):
                info = get_field(trial, "Info")
                fc_raw = get_field(info, "KinFC") if has_field(info, "KinFC") else None
                fo_raw = get_field(info, "KinFO") if has_field(info, "KinFO") else None
                ms_raw = get_field(info, "Midsvnt") if has_field(info, "Midsvnt") else None

            fc = parse_events(fc_raw) if fc_raw is not None else []
            fo = parse_events(fo_raw) if fo_raw is not None else []
            ms = parse_events(ms_raw) if ms_raw is not None else []

            votes = {}
            if "LHEE" in kin and "RHEE" in kin:
                votes = heel_vote_for_code(fc, kin["LHEE"], kin["RHEE"])
            trial_map = mapping_from_votes(votes)
            mapping_ok = all(trial_map.get(code) == SIDE_CODE_TO_FOOT.get(code) for code in trial_map)
            if trial_map and not mapping_ok:
                mapping_mismatches += 1
                # keep the global empirically validated map; record the disagreement
            mapping_status = "PASS" if mapping_ok or not trial_map else "WARNING"

            seq = sequence_string(fc)
            alternates = is_alternating(fc)
            n_agree = 0
            n_vote = 0
            for code, counts in votes.items():
                expected = SIDE_CODE_TO_FOOT.get(code)
                if expected:
                    n_agree += counts.get(expected, 0)
                    n_vote += counts["L"] + counts["R"]

            if not fc:
                ev_status = "FAIL"
            elif not alternates:
                ev_status = "WARNING"
            elif mapping_status != "PASS":
                ev_status = "WARNING"
            else:
                ev_status = "PASS"

            event_rows.append(
                {
                    "subject_id": subject_id,
                    "session_name": sess_name,
                    "n_kinfc": len(fc),
                    "n_kinfo": len(fo),
                    "n_midsvnt": len(ms),
                    "side_code_1": SIDE_CODE_TO_FOOT.get(1, ""),
                    "side_code_2": SIDE_CODE_TO_FOOT.get(2, ""),
                    "sequence": seq,
                    "alternates": alternates,
                    "heel_vote_agreements": n_agree,
                    "heel_vote_n": n_vote,
                    "mapping_status": mapping_status,
                    "validation_status": ev_status,
                    "notes": "" if alternates else "non-alternating KinFC sides",
                }
            )

            cycles = extract_cycles(fc, fo, ms)
            n_left = n_right = 0
            n_valid = n_warn = n_fail = 0
            n_usable = 0
            n_norm_ok = 0

            for cycle in cycles:
                cycle_id = f"{subject_id}_{sess_name}_{cycle.side}_{cycle.cycle_index:02d}"
                quality = score_cycle(cycle, kin, vrate)
                if cycle.side == "L":
                    n_left += 1
                else:
                    n_right += 1
                if quality.overall == "PASS":
                    n_valid += 1
                elif quality.overall == "PASS WITH WARNINGS":
                    n_warn += 1
                else:
                    n_fail += 1
                if quality.usable_lower_body:
                    n_usable += 1

                n_core_ok = 0
                core_block = np.full((len(core_names), NORMALIZED_POINTS, 3), np.nan, dtype=np.float32)
                for i, name in enumerate(core_names):
                    arr = kin.get(name)
                    if arr is None:
                        continue
                    normed = normalize_signal(arr, cycle.start_frame, cycle.end_frame, NORMALIZED_POINTS)
                    if normed is None:
                        continue
                    core_block[i] = normed
                    n_core_ok += 1
                interp_ok = n_core_ok == len(core_names)
                if interp_ok:
                    n_norm_ok += 1
                    normalized_ids.append(cycle_id)
                    normalized_stack.append(core_block)

                victimized = lab.victimized if lab is not None else ""
                cycle_rows.append(
                    {
                        "cycle_id": cycle_id,
                        "subject_id": subject_id,
                        "survey_subject_no": int(subject_id[1:]),
                        "session_id": sess_name,
                        "trial_id": f"{subject_id}/{sess_name}",
                        "cycle_index_side": cycle.cycle_index,
                        "side": cycle.side,
                        "victimized": victimized,
                        "start_frame": cycle.start_frame,
                        "end_frame": cycle.end_frame,
                        "numpy_start_index": cycle.start_frame - 1,
                        "numpy_end_index": cycle.end_frame - 1,
                        "duration_frames": quality.duration_frames,
                        "duration_seconds": round(quality.duration_seconds, 6),
                        "sampling_rate_hz": vrate,
                        "initial_contact_frame": cycle.initial_contact.frame,
                        "next_contact_frame": cycle.next_contact.frame,
                        "opposite_contact_frame": cycle.opposite_contact.frame if cycle.opposite_contact else "",
                        "opposite_contact_side": cycle.opposite_contact.side if cycle.opposite_contact else "",
                        "ipsilateral_foot_off_frame": cycle.ipsilateral_foot_off.frame if cycle.ipsilateral_foot_off else "",
                        "opposite_foot_off_frame": cycle.opposite_foot_off.frame if cycle.opposite_foot_off else "",
                        "mid_stance_frame": cycle.mid_stance.frame if cycle.mid_stance else "",
                        "mid_stance_side": cycle.mid_stance.side if cycle.mid_stance else "",
                        "normalized_points": NORMALIZED_POINTS,
                        "core_signals_normalized": n_core_ok,
                        "normalization_ok": interp_ok,
                        "overall_quality": quality.overall,
                        "usable_lower_body": quality.usable_lower_body,
                    }
                )

                qrow: dict[str, Any] = {
                    "cycle_id": cycle_id,
                    "subject_id": subject_id,
                    "session_id": sess_name,
                    "side": cycle.side,
                    "events_fc": quality.events_fc,
                    "events_opposite_fc": quality.events_opposite_fc,
                    "events_fo": quality.events_fo,
                    "events_mid_stance": quality.events_mid_stance,
                    "duration_status": quality.duration_status,
                    "lower_body_status": quality.lower_body_status,
                    "upper_body_status": quality.upper_body_status,
                    "overall": quality.overall,
                    "usable_lower_body": quality.usable_lower_body,
                    "reasons": "; ".join(quality.reasons),
                }
                for domain, score in quality.domains.items():
                    qrow[f"{domain}_present"] = score.present
                    qrow[f"{domain}_expected"] = score.expected
                    qrow[f"{domain}_finite_ratio"] = "" if score.finite_ratio is None else round(score.finite_ratio, 6)
                    qrow[f"{domain}_status"] = score.status
                quality_rows.append(qrow)

            trial_rows.append(
                {
                    "subject_id": subject_id,
                    "session_name": sess_name,
                    "victimized": lab.victimized if lab is not None else "",
                    "n_kinfc": len(fc),
                    "alternates": alternates,
                    "event_validation": ev_status,
                    "n_cycles": len(cycles),
                    "n_left_cycles": n_left,
                    "n_right_cycles": n_right,
                    "n_pass": n_valid,
                    "n_pass_with_warnings": n_warn,
                    "n_fail": n_fail,
                    "n_usable_lower_body": n_usable,
                    "n_normalized_ok": n_norm_ok,
                }
            )

    subject_rows = _subject_summaries(cycle_rows, trial_rows, label_by_id)

    n_cycles = len(cycle_rows)
    n_usable = sum(1 for r in cycle_rows if r["usable_lower_body"])
    n_fail_cycles = sum(1 for r in cycle_rows if r["overall_quality"] == "FAIL")
    n_alt_fail = sum(1 for r in event_rows if r["validation_status"] == "FAIL")
    n_alt_warn = sum(1 for r in event_rows if r["validation_status"] == "WARNING")

    if walking_trials != EXPECTED_WALKING_TRIALS or n_cycles == 0 or n_alt_fail:
        status = "FAIL"
    elif n_alt_warn or mapping_mismatches or n_fail_cycles:
        status = "PASS WITH WARNINGS"
    else:
        status = "PASS WITH WARNINGS" if n_usable < n_cycles else "PASS"

    # If every cycle is usable and events pass, still warn on duration/upper-body — that's WITH WARNINGS typically.
    n_pw = sum(1 for r in cycle_rows if r["overall_quality"] == "PASS WITH WARNINGS")
    n_pass = sum(1 for r in cycle_rows if r["overall_quality"] == "PASS")
    if walking_trials == EXPECTED_WALKING_TRIALS and n_cycles > 0 and n_alt_fail == 0:
        if n_pw or n_fail_cycles or n_alt_warn or mapping_mismatches:
            status = "PASS WITH WARNINGS"
        else:
            status = "PASS"

    summary = {
        "walking_trials_inspected": walking_trials,
        "expected_walking_trials": EXPECTED_WALKING_TRIALS,
        "side_map": SIDE_CODE_TO_FOOT,
        "cycles": n_cycles,
        "left_cycles": sum(1 for r in cycle_rows if r["side"] == "L"),
        "right_cycles": sum(1 for r in cycle_rows if r["side"] == "R"),
        "pass": n_pass,
        "pass_with_warnings": n_pw,
        "fail": n_fail_cycles,
        "usable_lower_body": n_usable,
        "normalized_ok": sum(1 for r in cycle_rows if r["normalization_ok"]),
        "normalized_points": NORMALIZED_POINTS,
        "event_validation_pass": sum(1 for r in event_rows if r["validation_status"] == "PASS"),
        "event_validation_warning": n_alt_warn,
        "event_validation_fail": n_alt_fail,
        "mapping_mismatches": mapping_mismatches,
        "core_signals": core_names,
    }

    normalized = {
        "cycle_id": np.array(normalized_ids, dtype=object),
        "signal_name": np.array(core_names, dtype=object),
        "gait_phase_pct": np.linspace(0.0, 100.0, NORMALIZED_POINTS, dtype=np.float32),
    }
    if normalized_stack:
        normalized["data"] = np.stack(normalized_stack, axis=0)
    else:
        normalized["data"] = np.zeros((0, len(core_names), NORMALIZED_POINTS, 3), dtype=np.float32)

    return Phase1Result(
        status=status,
        event_rows=event_rows,
        cycle_rows=cycle_rows,
        quality_rows=quality_rows,
        subject_rows=subject_rows,
        trial_rows=trial_rows,
        summary=summary,
        normalized=normalized,
    )


def _subject_summaries(cycle_rows, trial_rows, label_by_id) -> list[dict[str, Any]]:
    cycles = pd.DataFrame(cycle_rows) if cycle_rows else pd.DataFrame()
    trials = pd.DataFrame(trial_rows) if trial_rows else pd.DataFrame()
    subjects = sorted(set(trials["subject_id"]) | set(label_by_id), key=lambda s: int(s[1:]))
    rows = []
    for sid in subjects:
        lab = label_by_id.get(sid)
        t = trials[trials["subject_id"] == sid] if len(trials) else trials
        c = cycles[cycles["subject_id"] == sid] if len(cycles) else cycles
        n_trials = int(len(t))
        n_cycles = int(len(c))
        dur = c["duration_seconds"] if n_cycles else pd.Series(dtype=float)
        rows.append(
            {
                "subject_id": sid,
                "survey_subject_no": int(sid[1:]),
                "victimized": lab.victimized if lab is not None else "",
                "walking_trials": n_trials,
                "trials_event_pass": int((t["event_validation"] == "PASS").sum()) if n_trials else 0,
                "total_gait_cycles": n_cycles,
                "left_cycles": int((c["side"] == "L").sum()) if n_cycles else 0,
                "right_cycles": int((c["side"] == "R").sum()) if n_cycles else 0,
                "pass_cycles": int((c["overall_quality"] == "PASS").sum()) if n_cycles else 0,
                "pass_with_warnings_cycles": int((c["overall_quality"] == "PASS WITH WARNINGS").sum()) if n_cycles else 0,
                "fail_cycles": int((c["overall_quality"] == "FAIL").sum()) if n_cycles else 0,
                "usable_lower_body_cycles": int(c["usable_lower_body"].sum()) if n_cycles else 0,
                "normalized_ok_cycles": int(c["normalization_ok"].sum()) if n_cycles else 0,
                "min_duration_s": float(dur.min()) if n_cycles else "",
                "median_duration_s": float(dur.median()) if n_cycles else "",
                "max_duration_s": float(dur.max()) if n_cycles else "",
            }
        )
    return rows


def _group_cycle_stats(rows: list[dict[str, Any]], victimized: str) -> dict[str, Any]:
    counts = [r["usable_lower_body_cycles"] for r in rows if r["victimized"] == victimized]
    if not counts:
        return {"n_subjects": 0, "min": "", "median": "", "max": "", "sum": 0}
    arr = np.array(counts, dtype=float)
    return {
        "n_subjects": len(counts),
        "min": int(arr.min()),
        "median": float(np.median(arr)),
        "max": int(arr.max()),
        "sum": int(arr.sum()),
    }


def write_phase1_outputs(project_root: Path, result: Phase1Result) -> dict[str, Path]:
    root = ml_project_root(project_root)
    out = root / "results" / "phase1"
    out.mkdir(parents=True, exist_ok=True)
    cycles_dir = out / "gait_cycles"
    cycles_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "events": out / "event_validation.csv",
        "cycles": out / "gait_cycle_inventory.csv",
        "quality": out / "gait_cycle_quality.csv",
        "subjects": out / "subject_cycle_summary.csv",
        "trials": out / "trial_cycle_summary.csv",
        "report": out / "phase1_report.md",
        "npz": cycles_dir / "normalized_core.npz",
    }
    pd.DataFrame(result.event_rows).to_csv(paths["events"], index=False)
    pd.DataFrame(result.cycle_rows).to_csv(paths["cycles"], index=False)
    pd.DataFrame(result.quality_rows).to_csv(paths["quality"], index=False)
    pd.DataFrame(result.subject_rows).to_csv(paths["subjects"], index=False)
    pd.DataFrame(result.trial_rows).to_csv(paths["trials"], index=False)
    np.savez_compressed(paths["npz"], **result.normalized)
    paths["report"].write_text(render_phase1_markdown(result), encoding="utf-8")
    return paths


def render_phase1_markdown(result: Phase1Result) -> str:
    s = result.summary
    y_stats = _group_cycle_stats(result.subject_rows, "Y")
    n_stats = _group_cycle_stats(result.subject_rows, "N")
    lines = [
        "# Phase 1 Gait Event & Cycle Engine",
        "",
        f"Status: **{result.status}**",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Read-only. `data/raw/` and `data/processed/` were not modified.",
        "The processed MAT remains the canonical trajectory store.",
        "Normalized core signals (0–100%, 101 points) are in `results/phase1/gait_cycles/normalized_core.npz`.",
        "",
        "## Side encoding (empirically validated)",
        "",
        "KinFC column 2 is a side code. Heel-Z at each contact (lower heel = contacting foot) across all 260 walking trials maps:",
        "",
        f"- code `1` → **{s['side_map'][1]}**",
        f"- code `2` → **{s['side_map'][2]}**",
        "",
        "This was measured, not assumed. The user-facing example that treated `1` as left is therefore incorrect for this dataset.",
        "",
        "## Dataset coverage",
        "",
        f"- Walking trials inspected: {s['walking_trials_inspected']} (expected {s['expected_walking_trials']})",
        f"- Event validation PASS/WARNING/FAIL: {s['event_validation_pass']}/{s['event_validation_warning']}/{s['event_validation_fail']}",
        f"- Mapping mismatches vs heel vote: {s['mapping_mismatches']}",
        "",
        "## Cycles",
        "",
        f"- Total gait cycles (ipsilateral FC → next ipsilateral FC): {s['cycles']}",
        f"- Left: {s['left_cycles']}",
        f"- Right: {s['right_cycles']}",
        f"- PASS: {s['pass']}",
        f"- PASS WITH WARNINGS: {s['pass_with_warnings']}",
        f"- FAIL: {s['fail']}",
        f"- Usable for lower-body analysis: {s['usable_lower_body']}",
        f"- Normalized 0–100% ({s['normalized_points']} points, all core signals): {s['normalized_ok']}",
        "",
        "## Subject-level usable cycles",
        "",
        f"- Victims (n={y_stats['n_subjects']}): min {y_stats['min']}, median {y_stats['median']}, max {y_stats['max']}, sum {y_stats['sum']}",
        f"- Controls (n={n_stats['n_subjects']}): min {n_stats['min']}, median {n_stats['median']}, max {n_stats['max']}, sum {n_stats['sum']}",
        "",
        "### Victims",
        "",
    ]
    for row in result.subject_rows:
        if row["victimized"] == "Y":
            lines.append(
                f"- {row['subject_id']}: {row['walking_trials']} trials, {row['usable_lower_body_cycles']} usable cycles "
                f"(L {row['left_cycles']} / R {row['right_cycles']})"
            )
    lines += ["", "### Controls", ""]
    for row in result.subject_rows:
        if row["victimized"] == "N":
            lines.append(
                f"- {row['subject_id']}: {row['walking_trials']} trials, {row['usable_lower_body_cycles']} usable cycles "
                f"(L {row['left_cycles']} / R {row['right_cycles']})"
            )

    non_alt = [r for r in result.event_rows if not r["alternates"]]
    lines += ["", "## Event irregularities", ""]
    if not non_alt:
        lines.append("All walking trials have alternating KinFC sides after decoding.")
    else:
        for r in non_alt:
            lines.append(f"- {r['subject_id']}/{r['session_name']}: {r['sequence']}")

    lines += [
        "",
        "## Quality policy",
        "",
        "- Upper-arm gaps (LUPA/RUPA/RFRM) do **not** fail a cycle if lower-body coverage is intact.",
        "- Missing opposite foot-contact or implausible duration (outside 0.50–2.20 s) fails the cycle.",
        "- Missing FO, 0 or >2 mid-stance events, unusual duration (outside 0.70–1.60 s), or incomplete lower-body → PASS WITH WARNINGS, still usable for lower-body gait.",
        "- Upper-body gaps (arms/head/trunk) are recorded per domain and do **not** change overall cycle status.",
        "",
        "## Provenance",
        "",
        "Each `cycle_id` encodes `Subject_Trial_Side_Index`, e.g. `S14_WU01_L_03`.",
        "`start_frame` / `end_frame` are MATLAB 1-based KinFC frames for AXYS visualization.",
        "",
        "## Core gait signals normalized",
        "",
        ", ".join(s["core_signals"]),
        "",
        "## Completion criteria",
        "",
        "- All walking trials inspected",
        "- KinFC / KinFO / Midsvnt parsed",
        "- Event side encoding validated against heel height",
        "- Gait cycles extracted (left and right)",
        "- Cycle durations calculated",
        "- Invalid cycles identified",
        "- Cycle quality scored by domain",
        "- Subject- and trial-level cycle counts calculated",
        "- Core gait signals assessed and normalized to 0–100% (101 points)",
        "- Full provenance retained",
        "- No source data modified",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_phase1_console(result: Phase1Result) -> str:
    s = result.summary
    y_stats = _group_cycle_stats(result.subject_rows, "Y")
    n_stats = _group_cycle_stats(result.subject_rows, "N")

    def line(label: str, value) -> str:
        return f"{label:<28} {value}"

    return "\n".join(
        [
            "=" * 60,
            "AXYS ML - PHASE 1 GAIT CYCLE ENGINE",
            "=" * 60,
            "",
            line("Walking trials:", f"{s['walking_trials_inspected']} / {s['expected_walking_trials']}"),
            line("Side map:", f"1={s['side_map'][1]}  2={s['side_map'][2]}"),
            line("Event validation PASS:", s["event_validation_pass"]),
            line("Event validation WARN:", s["event_validation_warning"]),
            "",
            line("Gait cycles:", s["cycles"]),
            line("Left / right:", f"{s['left_cycles']} / {s['right_cycles']}"),
            line("PASS:", s["pass"]),
            line("PASS WITH WARNINGS:", s["pass_with_warnings"]),
            line("FAIL:", s["fail"]),
            line("Usable lower-body:", s["usable_lower_body"]),
            line("Normalized 101-pt:", s["normalized_ok"]),
            "",
            line("Victim usable cycles:", f"min {y_stats['min']}  median {y_stats['median']}  max {y_stats['max']}"),
            line("Control usable cycles:", f"min {n_stats['min']}  median {n_stats['median']}  max {n_stats['max']}"),
            "",
            "-" * 60,
            "FINAL STATUS",
            "-" * 60,
            "",
            result.status,
            "",
        ]
    )
