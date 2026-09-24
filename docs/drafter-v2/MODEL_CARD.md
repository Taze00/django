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

D-014: the same experimental V now supports First/Mid/Last decisions. Early
search is bounded minimax with width-three Train-appearance shortlists. Current
opponent pick probabilities, search regret and tactical completeness are UNKNOWN.
Root candidates remain exhaustive over supported legal catalog entries.

D-015 adds side-by-side Legacy output with separate score semantics. Versioned
snapshots preserve actual experimental predictions and are explicitly ineligible
for automatic training; selection bias and self-reported outcome provenance remain.

## Final experimental configuration (D-016)

Selected runtime artifact byte digest:
`92e0b427bf9abce62e047419ea1008f740c9ee7b39b1458ae15692402b7cf52d`.
Model: `v2-composition-logit-1`, Train 6,094 / Validation 2,031. Last exhaustive;
Mid/First bounded minimax. 28 Train-derived map-context mappings; current selectable
intersection shown in UI. Eligibility/uncertainty remain explicit. Opponent-term
candidate rejected. No mechanics features or active/default-engine change.

Status: usable opt-in experimental Challenger, **NOT PROMOTED**. Full product,
metrics, testing limits, provenance, logging bias and next evidence requirements:
CHALLENGER_REPORT.md. Local preview is development-only; no live deployment.


## D-017 explanation scope
Active artifact and predictions remain unchanged. Runtime diagnostics separate
candidate individual/mode/map/team terms from shared whole-draft background.
Enemy-specific interaction is inactive in selected V; fixed Last-Pick enemies
cannot explain candidate ordering beyond legality under this additive model.
Earlier-phase background can differ through hypothetical search continuations.
UI exposes UNKNOWN missing terms/uncertainty and additive-only explanation limits.
See HIDEOUT_DIAGNOSTIC.md for measured Wendy/Gus/Belle decomposition; no causal
anti-tank/control/role story or family-level validation claim.


D-018: models unchanged. Optional shadow requests preserve both responses before choice; later reports are unverified and excluded from training. No promotion or quality claim.


D-019: active V unchanged; opponent feature rejection retained. Shadow and future membership code do not fit models or promote candidates. Future fair comparison requires a genuinely frozen Train-only Legacy input bundle; current runtime hashes do not establish it.


D-021 active V2 artifact byte hash unchanged; no training or model search. Exact Legacy Train-only bundle remains blocked on curated demo priors. Default Legacy provider/scorer unchanged.


D-022: V2 artifact unchanged. Fair future Legacy comparison permits frozen pre-existing manual constants alongside empirical Train-only statistics. No model fitting, tuning, activation or default change.


D-022 result: VERIFIED bundle 23069ec9ec9cbbc8b7475e590c18e9548c4666395834886e12c0cd8436830527. 94,302 empirical rows from 6,094 Train; 137 identical B priors; two identical builds, independent all-row counts/membership and 28 archive-only scoring replays passed. 20 focused tests passed (4.342 s). No future window registered; independent soloRanked evidence remains unavailable in the latest collection report. Exact contracts/limits: LEGACY_BUNDLE_RUNBOOK.md and verification/artifact JSONs.


D-023 preserves model weights and Legacy default. Discovery/query frontier expansion is an acquisition test only; trophy discoveries are not Ranked model evidence and pilot matches are not future test membership.


D-024: future baseline uses unchanged verified D-022 scoring clock/configuration and algorithmic patch ID 1. Actual prospective game patch remains UNKNOWN. 33 pilot matches demonstrate acquisition only; no quality/promotional claim or model change.
