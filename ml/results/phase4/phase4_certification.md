# Phase 4 certification

Status: **PASS WITH WARNINGS**

k choice: `{'k': 2, 'method': 'hierarchical', 'reason': 'max_bootstrap_ari_among_stable_hierarchical', 'silhouette': 0.41503306618271296, 'mean_boot_ari': 0.7546071898190309, 'min_size': 4, 'criteria': {'min_cluster_size': 4, 'min_silhouette': 0.2, 'min_mean_boot_ari': 0.5}}`

- `n_subjects_31`: **PASS** — n=31
- `assignments_have_no_labels`: **PASS** — assignment table is label-free
- `representation_label_free`: **PASS** — compact matrix has no label columns
- `pca_present`: **PASS** — PCA summary written
- `cluster_metrics_present`: **PASS** — k grid evaluated
- `stability_subject_unit`: **PASS** — stability unit=subject
- `k_not_from_labels`: **PASS** — selection payload has no victim criterion
- `sensitivity_present`: **PASS** — algorithm/representation ARI table
- `characterization_present`: **PASS** — label-blind profiles
- `trajectories_present`: **PASS** — phenotype trajectories
- `enrichment_subject_perm`: **PASS** — permutation unit=subject
- `confounding_present`: **PASS** — anthropometry vs phenotype
- `labels_post_discovery`: **PASS** — labels joined after freeze
- `not_two_large_phenotypes`: **WARNING** — sizes={1: np.int64(27), 2: np.int64(4)}; majority/outgroup split — do not over-interpret as two gait types
- `height_association`: **WARNING** — height Kruskal p=0.0499; phenotype may partly track stature
