# Drafter V2 Evaluation

Status: framework not yet implemented.

Planned frozen protocol:
- Unit of observation: deduplicated, conflict-free Ranked match with known winner.
- Time-based train/validation/holdout split; no future rows in training and no fingerprint across splits.
- Primary metrics: log loss, Brier score, calibration. AUC/accuracy are secondary.
- Baselines: B0 50/50, B1 validated skill-only if available, B2 global meta, B3 meta+mode, B4 meta+map, B5 regularized pair/synergy.
- Legacy evaluated on exactly the same holdout without changing Legacy scoring.
- Fixed seed, commit hash, feature manifest, split definition and patch window recorded in every report.
- Leakage checks cover duplicate fingerprints, future features, result-derived fields, player identity, post-match fields and sampling artifacts.

The holdout is not used for tuning or feature selection.
