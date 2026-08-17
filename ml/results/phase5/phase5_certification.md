# Phase 5 certification

Status: **PASS WITH WARNINGS**

k choice: `{'k': None, 'method': 'hierarchical', 'reason': 'no_stable_phenotype_structure', 'criteria': {'min_cluster_size': 4, 'min_silhouette': 0.2, 'min_mean_boot_ari': 0.5}}`

- `n_victims_17`: **PASS** — n_victims=17
- `n_controls_14`: **PASS** — n_controls=14
- `n_subjects_31`: **PASS** — subject-level representation
- `perm_unit_subject`: **PASS** — similarity permutation unit=subject
- `nn_perm_unit_subject`: **PASS** — NN permutation unit=subject
- `assignments_no_label_col`: **PASS** — assignment table has no victimized column
- `representation_gait_only`: **PASS** — compact gait matrix has no label columns
- `similarity_p_present`: **PASS** — within-victim p reported
- `honest_no_subgroup`: **WARNING** — no stable victim subgroup forced
