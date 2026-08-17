"""Family 3 — spatial excursions. Axes are axis_1/2/3 until lab AP/ML/VT is certified."""

from __future__ import annotations

from .anatomy import SPATIAL_SIGNALS, meta
from .base import AXIS_NAMES, FeatureSpec, excursion, path_length_3d
from .context import CycleRecord


def specs() -> list[FeatureSpec]:
    out: list[FeatureSpec] = []
    for signal in SPATIAL_SIGNALS:
        info = meta(signal)
        for axis in AXIS_NAMES:
            out.append(
                FeatureSpec(
                    name=f"{signal}_{axis}_excursion",
                    family="spatial",
                    source_signal=signal,
                    anatomical_region=info["region"],
                    side=info["side"],
                    unit="mm",
                    aggregation="excursion",
                    phase="full_cycle",
                    related_anatomy=info["related"],
                    description=f"{signal} {axis} peak-to-peak displacement (coordinate meaning unverified)",
                )
            )
        out.append(
            FeatureSpec(
                name=f"{signal}_path3d",
                family="spatial",
                source_signal=signal,
                anatomical_region=info["region"],
                side=info["side"],
                unit="mm",
                aggregation="path_length",
                phase="full_cycle",
                related_anatomy=info["related"],
                description=f"{signal} 3D path length over the cycle",
            )
        )
    return out


def extract(record: CycleRecord) -> dict[str, float]:
    values: dict[str, float] = {}
    for signal in SPATIAL_SIGNALS:
        arr = record.signals.get(signal)
        if arr is None:
            continue
        for j, axis in enumerate(AXIS_NAMES):
            values[f"{signal}_{axis}_excursion"] = excursion(arr, j)
        values[f"{signal}_path3d"] = path_length_3d(arr)
    return values
