# Drafter V2 Model Card

Status: V2 architecture is trainable but no V2 model is active. Legacy remains
the current engine because the isolated worktree contains no historical matches.

Intended use: explainable Ranked draft assistance based on observed, provenance-tracked data. Not a guarantee of match outcome.

Implemented candidate contract: `V(map, mode, patch, team_a, team_b, context) -> P(team_a wins)`.
The current candidate is a dependency-free L2-regularized logistic model with
signed brawler, mode/brawler, map/brawler and within-team pair features. It has
no intercept, so swapping teams negates the logit exactly. Feature and model
versions plus the manifest are persisted in an explicit JSON artifact only when
the training command receives `--model-path`.

Data policy: unknown values remain unavailable; measured, derived, assumed and unknown facts are kept distinct. Synthetic fixtures are test-only and never mixed with real match data.

Promotion gate: a V2 model must beat or appropriately match baselines on frozen holdout log loss/Brier/calibration, pass leakage/symmetry/legal-pick/determinism tests, integrate without unrelated regressions, and retain Legacy rollback. Current status: not promotable; holdout is unavailable.

Known limitations: current data inventory and objective mechanics availability are not yet measured in this isolated environment; player-skill confounding and pick-order information may be unavailable.
