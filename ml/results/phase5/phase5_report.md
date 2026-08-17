# Phase 5 Within-Victim Gait Similarity and Subgroup Discovery

Generated: 2026-08-13

## Objective

Phase 3 found no shared victim-versus-control signature. Phase 4 found no victim-enriched population phenotypes.
Phase 5 asks whether the **17 victimized subjects** are more similar to each other than chance, and whether they form stable gait subgroups that differ from the **14 controls**.

Independent unit: **subject** (n=31; 17 victimized). Cycles were not clustering units.

The gait representation is the certified Phase 4 family-balanced compact matrix (31 × 27), built without victimization in scaling, PCA, or feature selection. Labels were used only to subset victims and to test similarity/enrichment.

## Within-victim similarity

- Observed mean pairwise distance (17 victims): **20.4168**
- Permutation null mean (random 17 of 31): **20.0601** (SD 2.4786; 5th–95th 15.8454–24.1456)
- Permutation p (more similar than chance): **0.547**
- Permutations: 999, unit=subject
- Victim–victim / control–control / victim–control mean pairwise: 20.4168 / 20.0157 / 19.7539

## Nearest neighbors

- Fraction of victims whose 1-NN is another victim: **0.529** (null mean 0.536, perm p=0.615)
- Mean 3-NN victim fraction: **0.471**

## Victim subgroups

- Selected k: **None**
- Reason: `no_stable_phenotype_structure`
- Number of stable subgroups: **0**
- Sizes: none
- Leave-one-**victim**-out mean ARI: **nan**

k was chosen from silhouette, minimum size, and victim-level bootstrap ARI — not from victim-versus-control separation.

## All 17 victims vs 14 controls (compact space)

Centroid distance=4.5893, perm p=0.771.

## Subgroup vs controls

No stable victim subgroups, so subgroup-vs-control tests were not interpreted.

## Strongest biomechanical characteristics (subgroup vs other victims)

Not applicable.

## Anatomical regions

Not applicable.

## Gait phases (median |δ| by bin midpoint, subgroup vs controls)

Not applicable.

## Confounding

Not applicable.

## Limitations

- n=17 is small; a 4-person split can be an outlier set.
- Compact space was estimated on all 31 subjects (gait-only, label-blind features).
- No classifier, victim score, or causal claim.

## Scientific conclusion

No robust within-victim gait structure was detected. Victims are not more similar to each other than random groups of 17 in the certified gait representation, or any candidate split failed stability/size rules. This does not revive a population-wide victim signature.

Phase 6 was not started.
