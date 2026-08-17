"""Gait-event parsing, side validation, and cycle boundary extraction."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .catalog import SIDE_CODE_TO_FOOT


@dataclass
class Event:
    frame: int  # MATLAB 1-based
    side_code: int
    side: str  # L or R


@dataclass
class TrialEvents:
    foot_contact: list[Event]
    foot_off: list[Event]
    mid_stance: list[Event]


def as_event_array(raw) -> np.ndarray:
    arr = np.atleast_2d(np.asarray(raw))
    if arr.size == 0:
        return np.zeros((0, 2), dtype=int)
    if arr.shape[1] < 2:
        raise ValueError(f"event array must be k x 2, got {arr.shape}")
    return arr[:, :2].astype(int)


def decode_side(code: int, mapping: dict[int, str] | None = None) -> str:
    mapping = mapping or SIDE_CODE_TO_FOOT
    if code not in mapping:
        return "?"
    return mapping[code]


def parse_events(raw, mapping: dict[int, str] | None = None) -> list[Event]:
    arr = as_event_array(raw)
    events = []
    for frame, code in arr:
        events.append(Event(frame=int(frame), side_code=int(code), side=decode_side(int(code), mapping)))
    events.sort(key=lambda e: (e.frame, e.side_code))
    return events


def sequence_string(events: list[Event]) -> str:
    return " → ".join(e.side for e in events) if events else ""


def is_alternating(events: list[Event]) -> bool:
    if len(events) < 2:
        return True
    for a, b in zip(events, events[1:]):
        if a.side == "?" or b.side == "?":
            return False
        if a.side == b.side:
            return False
    return True


def contacting_foot_from_heels(lhee_z: float, rhee_z: float) -> str | None:
    if not np.isfinite(lhee_z) or not np.isfinite(rhee_z):
        return None
    if lhee_z == rhee_z:
        return None
    return "L" if lhee_z < rhee_z else "R"


def heel_vote_for_code(
    fc_events: list[Event],
    lhee: np.ndarray,
    rhee: np.ndarray,
) -> dict[int, dict[str, int]]:
    """Count contacting-foot votes (lower heel Z) per KinFC side code."""
    votes: dict[int, dict[str, int]] = {}
    n = lhee.shape[0]
    for ev in fc_events:
        idx = ev.frame - 1
        if idx < 0 or idx >= n:
            continue
        foot = contacting_foot_from_heels(float(lhee[idx, 2]), float(rhee[idx, 2]))
        if foot is None:
            continue
        bucket = votes.setdefault(ev.side_code, {"L": 0, "R": 0})
        bucket[foot] += 1
    return votes


def mapping_from_votes(votes: dict[int, dict[str, int]]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for code, counts in votes.items():
        if counts["L"] == counts["R"]:
            continue
        mapping[code] = "L" if counts["L"] > counts["R"] else "R"
    return mapping


def consecutive_repeats(events: list[Event]) -> list[tuple[int, int, str]]:
    repeats = []
    for a, b in zip(events, events[1:]):
        if a.side == b.side and a.side != "?":
            repeats.append((a.frame, b.frame, a.side))
    return repeats


@dataclass
class ExtractedCycle:
    side: str
    cycle_index: int  # 1-based per trial+side
    start_frame: int
    end_frame: int
    initial_contact: Event
    next_contact: Event
    opposite_contact: Event | None
    ipsilateral_foot_off: Event | None
    opposite_foot_off: Event | None
    mid_stance: Event | None
    extra_opposite_contacts: int = 0
    extra_ipsilateral_fo: int = 0
    extra_mid_stance: int = 0


def _in_open_interval(frame: int, start: int, end: int) -> bool:
    return start < frame < end


def _pick_events(events: list[Event], start: int, end: int, side: str | None = None) -> list[Event]:
    out = []
    for ev in events:
        if not _in_open_interval(ev.frame, start, end):
            continue
        if side is not None and ev.side != side:
            continue
        out.append(ev)
    return out


def extract_cycles(fc: list[Event], fo: list[Event], ms: list[Event]) -> list[ExtractedCycle]:
    """Ipsilateral FC → next ipsilateral FC, independently for L and R."""
    cycles: list[ExtractedCycle] = []
    by_side: dict[str, list[Event]] = {"L": [], "R": []}
    for ev in fc:
        if ev.side in by_side:
            by_side[ev.side].append(ev)

    for side in ("L", "R"):
        contacts = by_side[side]
        opposite = "R" if side == "L" else "L"
        for i, (start_ev, end_ev) in enumerate(zip(contacts, contacts[1:]), start=1):
            start, end = start_ev.frame, end_ev.frame
            opp_fc = _pick_events(fc, start, end, opposite)
            ipsi_fo = _pick_events(fo, start, end, side)
            opp_fo = _pick_events(fo, start, end, opposite)
            mid = _pick_events(ms, start, end)
            cycles.append(
                ExtractedCycle(
                    side=side,
                    cycle_index=i,
                    start_frame=start,
                    end_frame=end,
                    initial_contact=start_ev,
                    next_contact=end_ev,
                    opposite_contact=opp_fc[0] if opp_fc else None,
                    ipsilateral_foot_off=ipsi_fo[0] if ipsi_fo else None,
                    opposite_foot_off=opp_fo[0] if opp_fo else None,
                    mid_stance=mid[0] if mid else None,
                    extra_opposite_contacts=max(0, len(opp_fc) - 1),
                    extra_ipsilateral_fo=max(0, len(ipsi_fo) - 1),
                    extra_mid_stance=max(0, len(mid) - 1),
                )
            )
    cycles.sort(key=lambda c: (c.start_frame, c.side))
    return cycles
