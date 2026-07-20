# Parser Readiness Report

Generated: 2026-07-14T17:52:47.548923

## Dataset Consistency

- **Subject Consistency**: PASS
- **Marker Consistency**: PASS
- **Joint Angle Consistency**: PASS
- **Session Count Consistency**: WARNING

## Frame Count Extraction (Corrected)

Frame counts are derived by detecting the XYZ axis (dimension of size 3) and using the remaining dimension as time. Supported layouts: `(N, 3)` and `(3, N)`. Ambiguous shapes `(3, 3)` or arrays with neither dimension equal to 3 leave `frame_count` as null and emit a warning — no guessing.

- **Min Frames**: 11
- **Max Frames**: 460
- **Mean Frames**: 270.65
- **Std Dev Frames**: 88.60
- **Resolved Sessions**: 301
- **Unresolved Sessions**: 0

- **STATUS**: Frame counts are not stuck at XYZ size 3 (prior axis-swap bug is not present in these statistics).

## Remaining Ambiguities

### Session Naming

- Multiple session naming conventions detected (WU##, WK##, WU#, Copy variants)
- Original names are preserved; see `session_types.csv` for semantic labels
- Classification categories: Walking, Calibration, Walking Copy, Calibration Copy, Alternate Walking, Unknown
- Inventory is not constrained to WU01–WU09

### Variable Units

- Units are **Unknown** for all categories in this dataset
- Reason: no unit metadata fields were found in the MATLAB structure
- Millimeters / degrees must **not** be assumed by the parser
- Authoritative source: `units.json`

## Structural Risks

- **HIGH**: Inconsistent session counts across subjects
  - Parser must handle missing sessions gracefully
  - Prefer semantic classification over requiring identical session sets

- **MEDIUM**: Variable frame counts (std=88.60)
  - Parser must handle variable-length trajectories

- **LOW**: No temporal gait events in dataset
  - Parser should not expect KinFC, KinFO, Midsvnt
  - Clinical metrics available instead

## Recommended Parser Assumptions

### Data Structure

1. All subjects follow the same hierarchical structure
2. Marker trajectories are 2D arrays with one axis of size 3 (XYZ)
3. Detect layout automatically: if `shape[1] == 3` and `shape[0] != 3` -> `(N, 3)`; if `shape[0] == 3` and `shape[1] != 3` -> `(3, N)`
4. Frame count = the non-coordinate dimension; never hardcode `shape[0]` or `shape[1]`
5. If layout cannot be determined, leave frame count unset and warn — do not guess

### Session Handling

1. Classify sessions by naming pattern into the six semantic categories above
2. Preserve original session names; classification is a label only
3. Do not require all subjects to have identical session sets
4. Handle missing sessions gracefully (skip or warn)
5. Treat Copy sessions as duplicates for optional exclusion

### Variable Access

1. Use variable catalog for semantic categorization
2. Do not hardcode variable names
3. Handle missing variables gracefully
4. Clinical metrics are in Res field; they are not XYZ time series

### Units and Scaling

1. Treat all category units as Unknown unless `units.json` reports explicit values
2. Do not assume millimeters for markers/COM or degrees for angles
3. Obtain units only from dataset metadata or external authoritative documentation
4. See `units.json` for per-category unit status and the reason they are unknown

## Variable Summary

- **Total Variables**: 96
- **center_of_mass**: 2 variables
- **clinical_metric**: 10 variables
- **joint_angles**: 26 variables
- **joint_centers**: 6 variables
- **markers**: 37 variables
- **segment_com**: 15 variables
