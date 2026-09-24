# Next independent window — REGISTERED, not started

Current D-024 registration is PROSPECTIVE_WINDOW.json; the fixed interval is
2026-09-25T00:00:00Z exclusive through 2026-10-09T00:00:00Z inclusive.
Acquisition feasibility passed with 33 eligible pilot observations. All pilot
observations remain excluded. See PROSPECTIVE_RUNBOOK.md for current rules.
Earlier preparation/history below is superseded where stated.

## Historical D-019–D-022 preparation

D-019 implements admission/membership infrastructure; D-022 schema 2 binds the verified Legacy bundle receipt. No real window has been
registered, sealed, evaluated or added to training. Example timestamps/hashes in
tests are synthetic fixtures. Do not substitute them into a real registration.
Old holdout and recorded comparisons remain permanently closed to development.

## Two independent streams

1. Opt-in shadow Praxisfall records capture user-entered drafts, both returned
   engines and actual later reports. They are unverified, self-selected and
   potentially influenced by recommendations. They support descriptive usage,
   missingness, disagreement and chosen-rank diagnostics only.
2. Future official API `soloRanked` matches from the preserved tagged frontier
   form a possible prospective outcome cohort. Trophy `ranked` never qualifies.
   This is temporal independence from development, not independent sampling of
   players: trophy-seeded graph, repeated players/teams and queried perspectives
   retain selection/dependence bias. No sampling weights are invented.

No shadow-to-Match join, player identity reconstruction, old holdout recovery,
automatic training, model search or mechanics research is part of this milestone.

## Preregistration prerequisites

Before choosing prospective start/end timestamps, freeze and archive:

- Current selected V2 artifact bytes and hash (D-016/D-017; no retraining).
- Exact code revision and development membership hash with latest development
  timestamp. All candidate/feature/hyperparameter decisions use Train/Validation
  only. Rejected opponent models remain rejected. New candidate work needs its
  own preregistered development protocol and must finish before registration.
- An independently audited **Legacy bundle with Train-only empirical inputs and frozen manual constants**, including catalog,
  provider statistics, separately labeled fixed priors, configuration, patch/map/mode resolution and source
  membership. Use the unchanged Legacy scorer/probability path. Freeze its hash
  before the future window. No online post-window aggregates may enter scoring.

The current runtime Legacy loaded-input digest is NOT such a bundle: it is a
context-specific hash, not restorable statistics nor verified Train-only lineage.
Historical Legacy aggregate timing is not repaired by labeling it frozen. D-022 has now independently verified this prerequisite; the successful receipt
is LEGACY_BUNDLE_VERIFICATION.json and artifact identities are pinned in
LEGACY_BUNDLE_ARTIFACTS.json. A runtime digest alone still cannot prove lineage. `register()` is a low-level contract called only after that
independent bundle audit. Schema 2 requires the independently verified bundle receipt, bound to its
content hash, under `train_empirical_frozen_manual_constants_v1`. Manual priors
are algorithmic constants, never Train-derived observations. No real registration call has been made. Bundle readiness is established within
its documented frozen context; prospective dates, acquisition and common-context/
patch eligibility rules still need to be pinned before opening a window.

After prerequisites, choose a fixed prospective calendar window (planned 14 days)
strictly after registration and every development observation. Freeze dates and
policy in version control before the start; pin canonical protocol digest in the
run record. Do not move the window, replace insufficient results or extend it after
looking at predictions/outcomes. Another window requires a new prospective protocol.
At least 1,000 eligible observations are required to seal under this version:
this is a disclosed operational floor, NOT a power calculation or guarantee of
useful precision. Insufficient data is DATA_UNAVAILABLE, not permission to tune.

## Implemented admission/membership contract

`v2_future_window.register()` validates temporal ordering, version/policy and
required SHA-256 identifiers. `publish()` atomically creates complete files via
exclusive link publication and refuses replacement. Pin `digest(protocol)` in the
preregistration commit/run record, independent of the file later supplied.

`manage.py drafter_v2_future_window --protocol PATH
 --expected-protocol-sha256 DIGEST` reads only the registered future interval in a
repeatable-read, read-only transaction. Its default output is operational counts,
not win rates, predictions or metrics. No historical rows are selected. Sealing
with `--seal-output NEW_PATH` requires the fixed window to be closed and the floor
met. Admission requires official API soloRanked, known non-conflicting result,
known map/mode, complete unique known-brawler 3v3 teams and observed API battlelog
provenance from tagged_frontier_v1 with a CollectorRun, content hash and plausible
fetch timestamp. Missing player tags are never reconstructed or exported.

Membership stores original and reconstructed match fingerprints, played-at,
content hash of outcome/context/composition (no outcome value in manifest), raw
content hashes, source/sampling/run provenance, exclusions, protocol hash and
membership hash. Duplicate fingerprints fail closed; dedup problems must be
resolved without deleting raw payloads. Exact match inclusion is immutable after
seal. Records rejected for missing/conflicting evidence are not silently promoted
later. Additional matches arriving after seal remain excluded.

`--verify-membership PATH` verifies the original content and source evidence;
additional raw sightings are allowed but never alter the seal. Changed outcomes,
teams, context, eligibility, disappeared records or source evidence fail closed.
An operator must retain the original seal digest/commit independently; filesystem
publication/digests do not prevent privileged manual file or database edits.
There is no evaluation or model fitting entrypoint in this command.

## Fair paired evaluation (future, not run)

After one-time sealing, evaluate the frozen candidates without any retuning.
Use complete observed 3v3 compositions on the same common eligible matches;
Legacy `DraftEngine.siegchance()` provides its existing probability mapping.
Do not divide recommendation heuristic scores by 100. V2 uses its complete-team
probability, never a First/Mid hypothetical search leaf. Pin canonical side A/B
orientation, patch/context handling and probability clipping from the existing
metric implementation. Report each model's full coverage and every common-subset
exclusion. Unknown maps/players/builds/skills cannot be filled by guesswork.

Primary metrics: paired LogLoss and Brier differences, plus calibration in ten
fixed equal-width probability bins with counts, mean prediction and observed
frequency. Report sample size, dates, source cohort, patch mix and coverage.
Use the existing B0 50/50 comparison. Any uncertainty analysis must account for
repeated-player/time dependence and state its assumptions; no independent-match
significance claim or fabricated confidence interval. Raw player tags stay private.
No threshold or calibration fitting on test outcomes; no promotion from rank
agreement or merely crossing the operational sample floor.

Ranking diagnostics are descriptive where actual draft order, bans, legal pool
and chosen pick were observed: top-k overlap, chosen rank, unknown-pick coverage
and phase-stratified disagreement. Match battlelogs alone do not establish draft
order or legal alternatives. A chosen pick is not a ground-truth optimal pick;
nonchosen counterfactual outcomes remain unknown. Early-phase search evaluation
requires actually observed continuations. No recommendation regret/NDCG/causal
benefit is asserted without defensible labels. Shadow win rates stay separate
from this independent API cohort and cannot supply missing test outcomes.

## Collection readiness and resume

Read-only audit at 2026-09-23T21:51:32Z: three preserved frontier players, zero due,
next stored cooldown minimum 2026-09-23T23:39:17Z. Zero API soloRanked observations
after the existing cutoff; 125 trophy ranked observations are not Ranked evidence.
No collection was attempted, credentials were not loaded, and no cooldown changed.
Reproducer: `shadow_frontier_readiness.py`; measured counts:
`SHADOW_FRONTIER_READINESS.json`. Zero real shadow snapshots currently exist.

Once due, a new bounded revisit may use zero ranking seeds, at most five battlelog
HTTP attempts including retries, depth at most one, unchanged six-hour claims,
backoff/rate-limit/lock rules and raw persistence. Record code revision, request
budget, genuine eligible soloRanked counts and retained provenance. Do not repeat
bootstrap, force timestamps, expand sources or set up a recurring collector.
Use existing COLLECTION_RUNBOOK.md and command; no API call is made by readiness.
Import cutoff protection remains unchanged; future admission separately enforces
its own preregistered dates. No qualifying observations means stop that bounded
run, record DATA_UNAVAILABLE and retain evidence rather than immediately retrying.

Validation: 46 combined future-contract/shadow/frontier tests passed (4.443 s),
then eight focused future tests including SQL-boundary, content-change and
true-development-end coverage passed (1.027 s). Fixtures are explicitly synthetic, not evidence accumulation.


D-021 prerequisite audit: current exact Legacy overlay has 137 demo priors, including all 137 resolved for Hideout. Train content verified independently, but an exact all-inputs-Train-only bundle is scientifically blocked. No real register() call is allowed. LEGACY_TRAIN_BUNDLE.md records the input-policy decision needed; no silent conversion/removal of priors.


## D-022 authorized baseline policy
The exact 20 Brawler/90 Counter/27 Synergy priors are now permitted as frozen
pre-existing B constants. All empirical statistics must be rebuilt solely from
pinned Train. This supersedes the D-021 all-inputs-Train-only blocker, preserving
its historical audit. Operational build, independent raw-count verification,
archive-only exact-path replay, A/B/C classification and freeze clock are in
LEGACY_BUNDLE_RUNBOOK.md. No production/default scoring or V2 change.

Registration schema 2 rejects missing/failed receipts, mismatched bundle hashes,
required unknown inputs, missing verification checks and a freeze later than
registration. Keep the original receipt and digest pinned outside the bundle;
receipts are evidence from the verifier, not a trusted claim merely because a
caller supplies a JSON object. No real registration occurs as part of bundle
construction. Current evidence still contains zero independent new soloRanked;
no collector retry is authorized in D-022.


## D-022 verification result

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


## D-023 acquisition gate (supersedes earlier collection-readiness instructions)

Before prospective registration, establish actual acquisition feasibility using
the separately preregistered single discovery pilot. Query eligibility accepts
real directly observed official team tags, including trophy discoveries; Ranked
evidence still requires eligible soloRanked. See DISCOVERY_PILOT.md and its pinned
protocol. D-022 remains frozen and verified; no rebuild is needed.

Pilot observations are pre-registration/development only. Their sampling marker
is explicitly rejected even if an additional accepted raw origin later appears.
Future start must be strictly after pilot completion and registration. Zero
eligible yield means DATA_UNAVAILABLE and diagnosis, not immediate retry or
registration. A successful pilot still requires a frozen prospective acquisition
policy, dates, retention plan, code/V2/D-022 pins and exact map/mode/Brawler/patch
common-subset exclusions. No real window is currently registered.


## D-024 schema 3 and frozen prospective acquisition

D-023 demonstrated access to 33 genuinely new eligible soloRanked observations.
The independently audited preflight places all 33 in the exact frozen common
subset. Schema 3 supersedes unregistered schema-2 preparation: it requires the
positive pilot receipt/hash, completion before registration, frozen acquisition
policy/implementation, exact common catalog and the D-022 verification receipt.
Prospective provenance must bind purpose, code and protocol digest. Full rules,
patch-convention limitations and bounded commands: PROSPECTIVE_RUNBOOK.md.
Actual game patch remains UNKNOWN; Demo-Patch is the unchanged verified Legacy
algorithmic input, not fabricated patch evidence. Pilot observations are excluded.


D-024 REGISTERED_NOT_STARTED. Fixed interval: (2026-09-25T00:00:00Z, 2026-10-09T00:00:00Z]. Registration: 2026-09-24T16:37:53.358317Z. Protocol digest 70e55f3dde205e15b232814f98b4e00c34fac8238f2fe5bc8b190608891adac8; implementation revision e9e6e7714409b566e86197abf01ddbe0957eaa9f. D-022 bundle and V2 artifact remain byte-identical. Fifty-nine combined tests passed (8.696 s). Real read-only pre-start collector check rejected before HTTP/run creation; inventory is zero. No predictions, metrics, training, promotion or recurring collector.
