# Phase 4 Gait Phenotype and Heterogeneity Discovery

Generated: 2026-08-13

## 1. Objective

Determine whether the 31 subjects form stable, interpretable gait phenotypes, and only then whether victimization is disproportionately represented in any phenotype.

## 2. Scientific motivation from Phase 3

Phase 3 found no FDR-supported, robust, shared victim-versus-control gait signature. Phase 4 therefore tests heterogeneity (multiple natural gait patterns) rather than a single population-wide victim signature.

## 3. Dataset

Phase 2 subject features (31 × 3665) restricted to Phase 3 label-blind redundancy representatives.

## 4. Independent unit

**n = 31 independent subjects.** 880 gait cycles are repeated observations within subjects and were not treated as independent clustering units.

## 5. Label-blind methodology

Victimization labels were absent from feature selection, median/IQR scaling, family PCA, global PCA, clustering, k selection, stability, and phenotype characterization. Labels were joined only after assignments were frozen.

## 6. Feature representation

- Source: 335 Phase 3 representatives
- Compact family-balanced dimensions: 27
- Balancing: within-family PCA (keep ≥80% family variance, cap 8 PCs), then divide by √n_pcs so families do not dominate Euclidean distance

- coordination: 6 source features → 2 family PCs
- kinematic: 163 source features → 4 family PCs
- phase: 71 source features → 8 family PCs
- smoothness: 2 source features → 1 family PCs
- spatial: 21 source features → 5 family PCs
- symmetry: 44 source features → 3 family PCs
- temporal: 3 source features → 2 family PCs
- variability: 25 source features → 2 family PCs

## 7. Scaling

Median / IQR robust scaling, parameters estimated on all 31 subjects without labels. Non-finite values imputed with the column median before scaling. Zero-IQR columns set to 0.

## 8. Dimensionality reduction

PCA describes variance of the compact representation. PC1 explains 37.2% of that variance. Components were **not** chosen to separate victims and controls. Clustering used the family-PC matrix, not a victimization-tuned subspace.

## 9. Cluster methodology

Primary: hierarchical Ward. Sensitivity: k-means (10 random inits, seed 20260813). Candidates k ∈ {2,3,4}.

## 10. Cluster-number selection

k was selected from silhouette, minimum cluster size, and subject-bootstrap ARI. **Victim/control separation was not a selection criterion.**

Selection: `{'k': 2, 'method': 'hierarchical', 'reason': 'max_bootstrap_ari_among_stable_hierarchical', 'silhouette': 0.41503306618271296, 'mean_boot_ari': 0.7546071898190309, 'min_size': 4, 'criteria': {'min_cluster_size': 4, 'min_silhouette': 0.2, 'min_mean_boot_ari': 0.5}}`

k=2 (max_bootstrap_ari_among_stable_hierarchical); sizes={1: np.int64(27), 2: np.int64(4)}.

## 11. Stability analysis

Subject-level 80% subsamples (150 replicates) and leave-one-subject-out ARI. Cycles were never resampled as if they were people.

## 12. Phenotype characterization

Each phenotype was contrasted with the remaining subjects using Cliff's delta on original (unscaled) features. Victimization was not used.

## 13. Trajectory characterization

When a stable solution existed, Phase 1 normalized cycles were summarized as subject medians, then phenotype medians (0–100% gait cycle). Inventory victimization columns were dropped before this step.

## 14. Victimization enrichment

Overall base rate: 17/31 victimized, 14/31 controls.

- Phenotype 1: 15/27 victimized (prop=0.56, expected=0.55, Fisher p=1, perm p=1, FDR q=1)
- Phenotype 2: 2/4 victimized (prop=0.50, expected=0.55, Fisher p=1, perm p=1, FDR q=1)

Permutation shuffles **subject** labels. Multiple phenotypes are FDR-controlled on permutation p-values.

## 15. Confounding analysis

mass_kg Kruskal p=0.976, height_cm Kruskal p=0.0499, lleg_cm Kruskal p=0.882, rleg_cm Kruskal p=0.836

Anthropometry (mass, height, leg length) was not used to build clusters. An association would mean the gait phenotype may partly reflect body size rather than victimization.

## 16. Sensitivity analysis

Adjusted Rand index between hierarchical vs k-means and between family-balanced vs unbalanced global-PCA clustering is in `clustering/sensitivity.csv`. These comparisons did not use victimization labels.

## 17. Limitations

- n=31 is small; even a stable k may not generalize.
- Family PCA compresses correlated biomechanics; a discarded sibling feature may be more interpretable.
- Axes remain ax1/ax2/ax3.
- No classifier or victim score was trained.

## 18. Scientific conclusion

k=2 met the pre-specified stability rule (silhouette=0.42, mean bootstrap ARI=0.75), but the partition is 27 vs 4 subjects. That is a majority/outgroup split, not two large, equally populated gait types. The n=4 group should not be promoted to a named clinical phenotype. After labels were revealed, phenotype composition was compatible with the overall 17/31 victim base rate.

This is not a claim that victimization causes gait, and it is not a predictive model.

## 19. Next steps

Phase 5 (supervised prediction) was not started. Any later predictive work must treat the 31 subjects as the independent unit and cannot reuse these labels for unsupervised k selection.

