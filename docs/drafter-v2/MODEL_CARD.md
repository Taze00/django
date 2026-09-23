# Drafter V2 Model Card

Status: V2 architecture is trainable but no V2 model is active. Legacy remains
the active/default engine. The sealed shared-subset comparison is final; no further tuning uses that holdout.

Intended use: explainable Ranked draft assistance based on observed, provenance-tracked data. Not a guarantee of match outcome.

Implemented candidate contract: `V(map, mode, patch, team_a, team_b, context) -> P(team_a wins)`.
The current candidate is a dependency-free L2-regularized logistic model with
signed brawler, mode/brawler, map/brawler and within-team pair features. It has
no intercept, so swapping teams negates the logit exactly. Feature and model
versions plus the manifest are persisted in an explicit JSON artifact only when
the training command receives `--model-path`.

Data policy: unknown values remain unavailable; measured, derived, assumed and unknown facts are kept distinct. Synthetic fixtures are test-only and never mixed with real match data.

Promotion gate: a V2 model must beat or appropriately match baselines on frozen holdout log loss/Brier/calibration, pass leakage/symmetry/legal-pick/determinism tests, integrate without unrelated regressions, and retain Legacy rollback. Current status: not promoted. Final shared subset (n=1,956): Legacy Log Loss 0.689749 / Brier 0.248301; V2 0.692600 / 0.249725. Full V2 coverage remains n=2,033 (0.692603 / 0.249727). These recorded results are unchanged; see the benchmark provenance limitation in EVALUATION.md. Legacy remains default.

Known limitations: objective mechanics are still only partially sourced; player-skill confounding, pick-order, bans, builds and objective combat fields remain unavailable. Historical rows can contain duplicate Brawlers and are valid for V2 but ineligible for the unchanged Legacy DraftContext contract. The snapshot covers 2026-08-29 through 2026-09-18 UTC and may not represent later meta changes.

## D-011 annotation archive

The offline claim archive has no connection to model inputs, training, predictions
or ranking. Dated explanations do not establish present-day applicability or
predictive benefit. Legacy remains the active/default scorer; model gates unchanged.

## D-012 experimental runtime

An opt-in Last-Pick Challenger now loads the existing composition model from an
explicit local artifact; Legacy remains default. This supersedes “no V2 model is
active” only for the experimental surface, not production promotion. Training:
6,094 examples through 2026-09-17T21:43:04Z; validation: 2,031 through
2026-09-18T08:34:00Z. Actual matchup uncertainty/current patch applicability remain
UNKNOWN. Candidate features without training support are exposed, not fabricated.

D-013: jointly fitted opponent interactions failed the fixed validation comparison.
The opt-in runtime retains `v2-composition-logit-1`; no feature activation. This
negative result does not establish all possible interaction models are useless.
