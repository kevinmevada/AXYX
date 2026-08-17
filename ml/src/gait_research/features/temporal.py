"""Family 2 — event timing and cycle duration."""

from __future__ import annotations

from .base import FeatureSpec, event_pct
from .context import CycleRecord


def specs() -> list[FeatureSpec]:
    common = dict(
        family="temporal",
        source_signal="events",
        anatomical_region="gait_cycle",
        side="ipsilateral",
        related_anatomy="KinFC/KinFO/Midsvnt",
        phase="full_cycle",
    )
    return [
        FeatureSpec(name="cycle_duration_s", unit="s", aggregation="duration", description="ipsilateral FC to next ipsilateral FC", **common),
        FeatureSpec(name="stance_pct", unit="pct_cycle", aggregation="event_timing", description="ipsilateral FO timing; proxy for stance percent", **common),
        FeatureSpec(name="swing_pct", unit="pct_cycle", aggregation="event_timing", description="100 - stance_pct", **common),
        FeatureSpec(name="stance_duration_s", unit="s", aggregation="duration", description="IC to ipsilateral FO", **common),
        FeatureSpec(name="swing_duration_s", unit="s", aggregation="duration", description="ipsilateral FO to next IC", **common),
        FeatureSpec(name="foot_off_pct", unit="pct_cycle", aggregation="event_timing", description="ipsilateral foot-off percent", **common),
        FeatureSpec(name="opposite_contact_pct", unit="pct_cycle", aggregation="event_timing", description="contralateral FC percent", **common),
        FeatureSpec(name="opposite_foot_off_pct", unit="pct_cycle", aggregation="event_timing", description="contralateral FO percent", **common),
        FeatureSpec(name="mid_stance_pct", unit="pct_cycle", aggregation="event_timing", description="first mid-stance event percent in the cycle window", **common),
    ]


def extract(record: CycleRecord) -> dict[str, float]:
    dur = float(record.duration_seconds)
    fo = event_pct(record.ipsilateral_foot_off_frame, record.start_frame, record.end_frame)
    opp_fc = event_pct(record.opposite_contact_frame, record.start_frame, record.end_frame)
    opp_fo = event_pct(record.opposite_foot_off_frame, record.start_frame, record.end_frame)
    ms = event_pct(record.mid_stance_frame, record.start_frame, record.end_frame)
    stance_s = dur * fo / 100.0 if fo == fo else float("nan")  # NaN-safe
    swing_s = dur - stance_s if stance_s == stance_s else float("nan")
    swing_pct = 100.0 - fo if fo == fo else float("nan")
    return {
        "cycle_duration_s": dur,
        "stance_pct": fo,
        "swing_pct": swing_pct,
        "stance_duration_s": stance_s,
        "swing_duration_s": swing_s,
        "foot_off_pct": fo,
        "opposite_contact_pct": opp_fc,
        "opposite_foot_off_pct": opp_fo,
        "mid_stance_pct": ms,
    }
