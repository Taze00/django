# Drafter V2 Model Card

Status: V2 architecture is trainable but no V2 model is active. Legacy remains
the current engine pending the sealed comparison and all promotion gates.

Intended use: explainable Ranked draft assistance based on observed, provenance-tracked data. Not a guarantee of match outcome.

Implemented candidate contract: `V(map, mode, patch, team_a, team_b, context) -> P(team_a wins)`.
The current candidate is a dependency-free L2-regularized logistic model with
signed brawler, mode/brawler, map/brawler and within-team pair features. It has
no intercept, so swapping teams negates the logit exactly. Feature and model
versions plus the manifest are persisted in an explicit JSON artifact only when
the training command receives `--model-path`.

Data policy: unknown values remain unavailable; measured, derived, assumed and unknown facts are kept distinct. Synthetic fixtures are test-only and never mixed with real match data.

Promotion gate: a V2 model must beat or appropriately match baselines on frozen holdout log loss/Brier/calibration, pass leakage/symmetry/legal-pick/determinism tests, integrate without unrelated regressions, and retain Legacy rollback. Current status: not promoted. Legacy holdout Log Loss 0.689749 / Brier 0.248301 beats V2 0.692603 / 0.249727; Legacy remains default.

Known limitations: objective mechanics are still only partially sourced; player-skill confounding, pick-order, bans, builds and objective combat fields remain unavailable. Historical rows can contain duplicate Brawlers and are valid for V2 but ineligible for the unchanged Legacy DraftContext contract.
