import numpy as np
import pandas as pd

from gait_research.phenotypes.enrichment import composition_table, permutation_enrichment
from gait_research.phenotypes.confounding import phenotype_covariates
from gait_research.phenotypes.characterization import phenotype_feature_effects


def test_known_enrichment_and_subject_permutation_unit():
    assign = pd.DataFrame(
        {
            "subject_id": [f"S{i}" for i in range(31)],
            "phenotype": [1] * 17 + [2] * 14,
        }
    )
    labels = pd.DataFrame(
        {
            "subject_id": [f"S{i}" for i in range(31)],
            "victimized": ["Y"] * 16 + ["N"] + ["N"] * 13 + ["Y"],
        }
    )
    comp = composition_table(assign, labels)
    p1 = comp.loc[comp.phenotype == 1].iloc[0]
    assert p1["n_victimized"] == 16
    perm = permutation_enrichment(assign, labels, n_perm=199, seed=1)
    assert (perm["unit"] == "subject").all()
    assert perm.loc[perm.phenotype == 1, "perm_p"].iloc[0] < 0.05


def test_characterization_has_no_victim_columns():
    rng = np.random.default_rng(0)
    raw = rng.normal(size=(31, 3))
    raw[:10, 0] += 5
    labels = np.array([1] * 10 + [2] * 21)
    meta = pd.DataFrame({"feature": ["f0", "f1", "f2"], "family": ["kinematic"] * 3})
    fx = phenotype_feature_effects(raw, ["f0", "f1", "f2"], labels, meta)
    assert "victimized" not in fx.columns
    top = fx.loc[fx.phenotype == 1].iloc[0]
    assert top["feature"] == "f0"
    assert top["direction"] == "HIGHER_IN_PHENOTYPE"


def test_confounding_kruskal():
    assign = pd.DataFrame({"subject_id": [f"S{i}" for i in range(10)], "phenotype": [1] * 5 + [2] * 5})
    cov = pd.DataFrame(
        {
            "subject_id": [f"S{i}" for i in range(10)],
            "mass_kg": list(range(5)) + list(range(50, 55)),
            "height_cm": [160] * 10,
            "lleg_cm": [80] * 10,
            "rleg_cm": [80] * 10,
        }
    )
    out = phenotype_covariates(assign, cov)
    mass_p = out.loc[out.variable == "mass_kg", "kruskal_p"].iloc[0]
    assert mass_p < 0.05
