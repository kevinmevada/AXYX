"""Cycle quality scoring with domain-aware missingness."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .catalog import (
    DOMAIN_SIGNALS,
    DURATION_FAIL_MAX_S,
    DURATION_FAIL_MIN_S,
    DURATION_WARN_MAX_S,
    DURATION_WARN_MIN_S,
    LOWER_BODY_DOMAINS,
    LOWER_BODY_FINITE_FAIL,
    LOWER_BODY_FINITE_WARN,
    UPPER_BODY_DOMAINS,
)
from .events import ExtractedCycle
from .normalize import window_finite_ratio


@dataclass
class DomainScore:
    name: str
    present: int
    expected: int
    finite_ratio: float | None
    status: str  # PASS | WARNING | FAIL | UNAVAILABLE


@dataclass
class CycleQuality:
    events_fc: str
    events_opposite_fc: str
    events_fo: str
    events_mid_stance: str
    duration_status: str
    duration_seconds: float
    duration_frames: int
    lower_body_status: str
    upper_body_status: str
    overall: str
    usable_lower_body: bool
    reasons: list[str] = field(default_factory=list)
    domains: dict[str, DomainScore] = field(default_factory=dict)


def _duration_status(duration_s: float) -> tuple[str, str | None]:
    if duration_s < DURATION_FAIL_MIN_S or duration_s > DURATION_FAIL_MAX_S:
        return "FAIL", f"implausible duration {duration_s:.3f}s"
    if duration_s < DURATION_WARN_MIN_S or duration_s > DURATION_WARN_MAX_S:
        return "WARNING", f"unusual duration {duration_s:.3f}s"
    return "PASS", None


def _event_status(present: bool, extra: int = 0) -> tuple[str, str | None]:
    if not present:
        return "FAIL", None
    if extra > 0:
        return "WARNING", None
    return "PASS", None


def _aggregate_domain_status(scores: list[DomainScore]) -> str:
    if not scores:
        return "UNAVAILABLE"
    if any(s.status == "FAIL" for s in scores):
        return "FAIL"
    if all(s.status == "UNAVAILABLE" for s in scores):
        return "UNAVAILABLE"
    if any(s.status in {"WARNING", "UNAVAILABLE"} for s in scores):
        return "WARNING"
    return "PASS"


def score_cycle(
    cycle: ExtractedCycle,
    kinematics: dict[str, np.ndarray],
    sampling_hz: float,
) -> CycleQuality:
    duration_frames = cycle.end_frame - cycle.start_frame
    duration_s = duration_frames / sampling_hz
    reasons: list[str] = []

    fc_status, _ = _event_status(True)
    opp_status, _ = _event_status(cycle.opposite_contact is not None, cycle.extra_opposite_contacts)
    fo_status, _ = _event_status(cycle.ipsilateral_foot_off is not None, cycle.extra_ipsilateral_fo)
    n_ms = (1 if cycle.mid_stance is not None else 0) + cycle.extra_mid_stance
    if n_ms == 0:
        ms_status = "WARNING"
    elif n_ms > 2:
        ms_status = "WARNING"
    else:
        ms_status = "PASS"

    if opp_status == "FAIL":
        reasons.append("missing opposite foot contact")
    elif cycle.extra_opposite_contacts:
        reasons.append(f"extra opposite FC x{cycle.extra_opposite_contacts}")
    if fo_status == "FAIL":
        reasons.append("missing ipsilateral foot off")
        fo_status = "WARNING"
    if n_ms == 0:
        reasons.append("missing mid-stance")
    elif n_ms > 2:
        reasons.append(f"unexpected mid-stance count {n_ms}")

    dur_status, dur_reason = _duration_status(duration_s)
    if dur_reason:
        reasons.append(dur_reason)

    domains: dict[str, DomainScore] = {}
    for domain, names in DOMAIN_SIGNALS.items():
        ratios = []
        present = 0
        for name in names:
            arr = kinematics.get(name)
            if arr is None:
                continue
            present += 1
            ratio = window_finite_ratio(arr, cycle.start_frame, cycle.end_frame)
            if ratio is not None:
                ratios.append(ratio)
        finite = float(np.mean(ratios)) if ratios else None
        if present == 0:
            status = "UNAVAILABLE"
        elif finite is not None and domain in LOWER_BODY_DOMAINS and finite < LOWER_BODY_FINITE_FAIL:
            status = "FAIL"
        elif finite is not None and finite < LOWER_BODY_FINITE_WARN:
            status = "WARNING"
        elif present < len(names):
            status = "WARNING"
        else:
            status = "PASS"
        domains[domain] = DomainScore(domain, present, len(names), finite, status)

    lower = _aggregate_domain_status([domains[d] for d in LOWER_BODY_DOMAINS if d in domains])
    upper = _aggregate_domain_status([domains[d] for d in UPPER_BODY_DOMAINS if d in domains])
    if lower == "FAIL":
        reasons.append("insufficient lower-body trajectory coverage")
    if upper in {"WARNING", "FAIL", "UNAVAILABLE"}:
        reasons.append(f"upper-body {upper.lower()}")

    # Upper-body gaps do not fail or warn the cycle overall; they are domain notes.
    overall = "PASS"
    if dur_status == "FAIL" or opp_status == "FAIL" or fc_status == "FAIL" or lower == "FAIL":
        overall = "FAIL"
    elif (
        dur_status == "WARNING"
        or fo_status != "PASS"
        or ms_status != "PASS"
        or opp_status == "WARNING"
        or lower == "WARNING"
    ):
        overall = "PASS WITH WARNINGS"

    usable = overall != "FAIL"
    return CycleQuality(
        events_fc=fc_status,
        events_opposite_fc=opp_status,
        events_fo=fo_status,
        events_mid_stance=ms_status,
        duration_status=dur_status,
        duration_seconds=duration_s,
        duration_frames=duration_frames,
        lower_body_status=lower,
        upper_body_status=upper,
        overall=overall,
        usable_lower_body=usable,
        reasons=reasons,
        domains=domains,
    )
