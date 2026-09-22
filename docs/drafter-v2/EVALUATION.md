# Drafter V2 Evaluation

Status: Phase 2 framework implemented; current isolated database has no valid
finished Ranked matches, so no empirical model result is claimed.

Planned frozen protocol:
- Unit of observation: deduplicated, conflict-free Ranked match with known winner.
- Time-based train/validation/holdout split; no future rows in training and no fingerprint across splits.
- Primary metrics: log loss, Brier score, calibration. AUC/accuracy are secondary.
- Baselines: B0 50/50, B1 validated skill-only if available, B2 global meta, B3 meta+mode, B4 meta+map, B5 smoothed pair/synergy.
- Legacy evaluated on exactly the same holdout without changing Legacy scoring.
- Fixed seed, commit hash, feature manifest, split definition and patch window recorded in every report.
- Leakage checks cover duplicate fingerprints, future features, result-derived fields, player identity, post-match fields and sampling artifacts.

The holdout is not used for tuning or feature selection.

## Reproducer

```text
python manage.py drafter_v2_evaluate --format json
```

The command is read-only. It loads conflict-free, known-result, complete 3v3
`soloRanked` matches, sorts by `(played_at, fingerprint)`, rejects duplicate
fingerprints, and uses a 60/20/20 time split. `DATA_UNAVAILABLE` is returned
when the holdout is empty. Current isolated result: input/train/validation/
holdout all `0`; no model metrics were emitted.

The implementation is dependency-free and lives in
`drafter/services/evaluation.py`. It records skipped incomplete or unknown
rows, and reports log loss, Brier score and probability-bin calibration.

## Legacy benchmark

The command additionally evaluates the unchanged Legacy probability layer
(`DraftEngine.siegchance()`) on the identical holdout when complete catalog
references are available. It does not train, alter, or normalize Legacy
scores. With the current isolated database the holdout is empty, so Legacy
performance is `DATA_UNAVAILABLE` rather than a fabricated number.
