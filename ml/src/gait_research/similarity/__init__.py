"""Cross-cohort similarity discovery (subject-level).

Phases 0–6 are frozen. This package tests whether victims share a movement
pattern with each other that controls do not — including shared direction,
shape, coordination, and timing that univariate mean differences can miss.

Unit of analysis is always SUBJECT (n=31). Never treat gait cycles as n.
"""

from .abnormality import (
    load_preregistered_features,
    mean_pairwise_jaccard,
    permute_mean_pairwise_jaccard,
    run_abnormality_overlap,
)
from .coordination_crp import load_preregistered_pairs, run_coordination_crp
from .deviation import (
    SEED,
    bootstrap_mean_pairwise_cosine,
    consistency_to_mean_direction,
    control_referenced_deviations,
    cosines_to_direction,
    loso_mean_pairwise_cosine,
    mean_pairwise_cosine,
    pairwise_cosine_matrix,
    permute_mean_pairwise_cosine,
    run_deviation_alignment,
)
from .event_phases import load_preregistered_phases, run_event_phase_battery
from .shape_space import (
    load_preregistered_curves,
    run_shape_space,
    zscore_curves,
)

__all__ = [
    "SEED",
    "bootstrap_mean_pairwise_cosine",
    "consistency_to_mean_direction",
    "control_referenced_deviations",
    "cosines_to_direction",
    "load_preregistered_curves",
    "load_preregistered_features",
    "load_preregistered_pairs",
    "load_preregistered_phases",
    "loso_mean_pairwise_cosine",
    "mean_pairwise_cosine",
    "mean_pairwise_jaccard",
    "pairwise_cosine_matrix",
    "permute_mean_pairwise_cosine",
    "permute_mean_pairwise_jaccard",
    "run_abnormality_overlap",
    "run_coordination_crp",
    "run_deviation_alignment",
    "run_event_phase_battery",
    "run_shape_space",
    "zscore_curves",
]
