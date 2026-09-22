# Drafter V2 Model Card

Status: no V2 model is active. Legacy remains the current engine.

Intended use: explainable Ranked draft assistance based on observed, provenance-tracked data. Not a guarantee of match outcome.

Planned model contract: `V(map, mode, patch, team_a, team_b, context) -> P(team_a wins)`, with explicit model and feature versions, uncertainty, data coverage and legal-draft constraints.

Data policy: unknown values remain unavailable; measured, derived, assumed and unknown facts are kept distinct. Synthetic fixtures are test-only and never mixed with real match data.

Promotion gate: a V2 model must beat or appropriately match baselines on frozen holdout log loss/Brier/calibration, pass leakage/symmetry/legal-pick/determinism tests, integrate without unrelated regressions, and retain Legacy rollback.

Known limitations: current data inventory and objective mechanics availability are not yet measured in this isolated environment; player-skill confounding and pick-order information may be unavailable.
