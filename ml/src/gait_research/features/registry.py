"""Feature family registry. Cycle-level families only; symmetry/variability are subject-level."""

from __future__ import annotations

from . import coordination, kinematic, phase, smoothness, spatial, symmetry, temporal, variability
from .base import FeatureSpec

CYCLE_MODULES = (kinematic, temporal, spatial, phase, coordination, smoothness)
SUBJECT_MODULES = (symmetry, variability)


def cycle_specs() -> list[FeatureSpec]:
    specs: list[FeatureSpec] = []
    for mod in CYCLE_MODULES:
        specs.extend(mod.specs())
    names = [s.name for s in specs]
    if len(names) != len(set(names)):
        dup = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(f"duplicate cycle feature names: {dup}")
    return specs


def subject_extra_specs() -> list[FeatureSpec]:
    specs: list[FeatureSpec] = []
    for mod in SUBJECT_MODULES:
        specs.extend(mod.specs())
    return specs


def all_specs() -> list[FeatureSpec]:
    specs = cycle_specs() + subject_extra_specs()
    names = [s.name for s in specs]
    if len(names) != len(set(names)):
        dup = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(f"duplicate feature names: {dup}")
    return specs
