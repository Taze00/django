# Drafter V2 experimental product report

## Delivered

The inherited V2 was a trainable prototype without a working product surface.
The branch now provides `/draft/challenger/`: Last-Pick ranking, bounded Mid/First
planning, actual model explanations, optional side-by-side Legacy rankings and
private, versioned decision snapshots with later user-reported outcomes.
Legacy remains default at `/draft/`; no production deployment was performed.
The local isolated preview is at `http://127.0.0.1:18080/draft/challenger/`.

## Evidence and selected V

The historical ordered membership digest was verified using structural metadata.
Only 6,094 Train and 2,031 Validation outcomes/compositions were loaded. Their
canonical content hashes are now enforced as well as membership. No held-out
composition, outcome or prediction was loaded, and no new split was made.
The model vocabulary, support counts and all fitted weights use Train only.

The selected `v2-composition-logit-1` has signed Brawler, mode/Brawler,
map/Brawler and within-team pair terms, no intercept, and exact team-swap
symmetry. It uses the previous 300 epochs/L2 1.0 configuration. No mechanics,
player skill, loadouts or current-patch facts are inferred.

| Measured on Validation, n=2,031 | LogLoss | Brier |
|---|---:|---:|
| B0 50/50 | 0.693147181 | 0.250000000 |
| Selected existing V | 0.688603807 | 0.247740789 |
| Opponent interactions, L2 1 | 0.688671923 | 0.247772212 |
| Opponent interactions, L2 10 | 0.688677816 | 0.247775099 |
| Opponent interactions, L2 100 | 0.688765489 | 0.247818086 |

The fixed, preregistered opponent-interaction experiment failed to improve either
metric. These plausible terms were rejected for runtime use. The model as a whole
outperformed B0 on Validation; this experiment does not establish individual
baseline-feature benefit or a generalization/promotion claim. Full calibration,
fit times and provenance: CHALLENGER_BASELINE.json and
CHALLENGER_OPPONENT_EXPERIMENT.json. Byte-level artifact hashes are distinguished
from canonical-content hashes; changing JSON whitespace is not a new fitted model.

The old sealed comparison remains a **previously recorded** result only: shared
n=1,956, Legacy LogLoss/Brier 0.689749/0.248301, V2 0.692600/0.249725.
No rerun occurred. Its Legacy aggregates lack a demonstrated train-only boundary;
the result is not proof of leakage-free superiority. Prior B0-B5 and full V2
sealed numbers remain in EVALUATION.md, not used to choose this continuation.

## Decision behavior

Last Pick evaluates every supported legal candidate after completing both teams.
No hand-weighted candidate bonuses, role heuristics or field rescaling were added.
Missing candidate main-effect evidence is reported unavailable. Context mappings
come from Train; the UI exposes only currently selectable maps with known model
contexts (28 mappings in the artifact, not a claim about current game rotation).

First/Mid use the same V, explicit UI first-pick side and existing 1-2-2-1 order.
All evaluations are complete 3v3 compositions. Every supported root candidate is
considered; future turns use width-three shortlists ordered by Train appearances.
This is an **assumed search approximation**, not measured opponent pick probability.
Own turns maximize and opponent turns minimize inside the bounded tree. Memoization
and a 30,000-leaf cap bound work; invalid orders or an exceeded budget fail closed.
The response reports its actual hypothetical continuation and omitted branches.
It does not claim the strongest possible reply or measured search regret.

Explanations are **derived from fitted model terms and search states**. They retain
signed logit contributions, readable Brawler names, feature support counts and
unseen features. Early-phase contributions describe the hypothetical finished
composition. They are associations, not causal tactical/terrain claims. Confidence
intervals, current patch applicability, skill and loadouts remain **UNKNOWN**.

## Runtime and logging

The model is an explicit local, ignored JSON artifact with validated schema,
finite weights, support/manifest alignment, context mapping and catalog identity.
Missing/incompatible artifacts return 503; no silent fallback. The old Legacy
endpoint and frozen scorer files are unchanged. Side-by-side Legacy values are
labeled heuristic scores rather than probabilities; rank agreement is not quality.

A signed, owner-bound response can be saved for two hours. Additive migration 0020
extends Praxisfall with metadata and an idempotency key; original fields remain.
Saving retains the exact response, model version/hash, state, choice and rank even
if the current model changes. Only the owner can replay it or update the reported
outcome. Recommendations remain fixed, Legacy integer score is null for V2, and
these self-selected records do not feed training or aggregates. CSRF remains active.

## Validation and operational limits

Full Drafter regression: 774 tests, four existing skips, 336.643 s, no failures.
Protected Fitness: 253 tests passed (138.720 s). Additional final focused
content/UX test results are recorded in STATUS. Migration drift check passed; 0020 applied only in isolation.
Legacy scorer/score/probability files match frozen 3a565bd. The isolated database
had zero existing Praxisfall records; legacy-field hashes matched before/after.
Populated historical snapshot preservation is covered by regression fixtures.

Real localhost HTTP, CSRF and static delivery passed. With optional Legacy compare,
one request each took First 3,129.532 ms, Mid 2,457.807 ms, Last 2,435.857 ms.
V2-only service smoke was First 770.071 ms / 8,452 evaluated leaves, Mid 92.893 ms /
900, Last 44.313 ms / 100. These are individual constructed-draft observations,
not production percentiles or quality evidence. See CHALLENGER_HTTP_SMOKE.json.
Final JavaScript parsed successfully in V8. No browser DOM/visual automation was
available; HTTP/static success is not described as a rendered-browser test.

## Remaining scientific gate and resume point

A usable experimental Challenger is delivered, not a validated replacement.
Independent, eligible future Ranked outcome data remains unavailable in the
completed collection evidence. The attempted evaluator extension did not improve
Validation. Promotion or claims of better real drafting/search now require a
preregistered independent future test window and train-only comparison inputs.
The old holdout cannot supply that evidence; sampled user logs cannot be assumed
unbiased; missing mechanics cannot be guessed. This is the remaining scientific
stop condition, not a request for approval between normal phases.

Next useful evidence is authentic, provenance-preserved new soloRanked matches
with a new temporal protocol, ideally explicit draft choices/skill/build context
when actually observed. Do not repeat the completed empty/trophy-only collector
experiments or mechanics inventory. Preserve completed artifacts and snapshot
history. No new model is automatically activated by acquiring additional rows.

## Reproduction, commits and rollback

D-012 `7229fd9`: experimental Last-Pick product and development-only trainer.
D-013 `bf91990`: bounded opponent-interaction comparison (negative result).
D-014 `ec245e9`: complete-state Mid/First planning.
D-015 `356193e`: side-by-side and signed versioned snapshots.
D-016: final context/label UX, content-hash guards and this report, committed together.
All milestones are pushed to the existing `alex/feature/drafter-v2` upstream.

Commands, preview start/stop and model rollback: CHALLENGER_RUNBOOK.md. Never run
the old historical train/evaluate/freeze commands for further selection. Return
to `/draft/` for Legacy; no model migration is needed. Disable/remove the configured
experimental model path to fail closed, preserving prior artifacts. Keep additive
snapshot fields/data when rolling code back; do not drop logs to switch engines.


## D-018/D-019 follow-up
Opt-in pre-choice shadow capture now preserves both responses and explicit bias;
later choice/outcome corrections append owner-bound report history. Unsupported
legal picks may be recorded without an invented V2 rank. No automatic training.
Future-window admission/sealing infrastructure and protocol are prepared, not a
registered/evaluated test. Current data/cooldown evidence and prerequisites:
SHADOW_EVALUATION.md, FUTURE_EVALUATION_PROTOCOL.md and STATUS.md.


## D-022 frozen comparison baseline

D-022 verification complete. Two fresh builds produced identical canonical content
SHA-256 `23069ec9ec9cbbc8b7475e590c18e9548c4666395834886e12c0cd8436830527`.
6,094 pinned Train matches produced 94,302 empirical rows: 10,772 Brawler,
45,698 Counter and 37,832 Synergy; zero empirical Build rows. All 137 prior
records remain content-identical. Independent raw-count/membership verification
passed for every empirical row; archive-only replay passed all 28 complete-team
probability/Last-Pick ranking contexts with zero Match and RawPayload rows.

The verified artifact is persisted privately as
`data/brawl_reports/legacy-evaluation-23069ec9ec9cbbc8b7475e590c18e9548c4666395834886e12c0cd8436830527.json.gz`
(4,728,874 compressed bytes). Input archive, second rebuild and replay receipt are
also retained. `LEGACY_BUNDLE_ARTIFACTS.json` pins their byte/content hashes and
builder hashes; `LEGACY_BUNDLE_VERIFICATION.json` is the independent successful
receipt. `LEGACY_BUNDLE_CLASSIFICATION.json` records field-level A/B classification
and explicit optional unknowns; required unknown inputs are absent within the
verified scoring scope. Runtime aggregate hashes were not used as lineage proof.

Final focused tests: 20 passed (4.342 s), covering archive tampering, metadata-only
provenance queries, Train tampering, exact Legacy parity, verification failure
guards and schema-2 prospective registration gates. Legacy implementation,
aggregator formulas, default runtime and V2 artifact are unchanged. No model fit,
quality evaluation, mechanics research, collector retry or real window registration.
The initial unused shared-raw-body prefetch and its corrected export are disclosed
in LEGACY_BUNDLE_RUNBOOK.md; no non-Train observations entered empirical aggregates.
