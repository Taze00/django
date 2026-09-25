RESUME FROM: D-026 10k milestone VERIFIED. Batch 04 still RUNNING, eight cycles, /tmp/development-batch-04.log (run 25 active at audit; do not restart). Continue bounded acquisition toward 25k/50k while safety signals allow. No more September-25 fitting; D-028 forward check only after September 28 UTC.

Immutable snapshot 006: 10,180 strict new eligible soloRanked + 6,094 verified original Train; 1,803 older new and 8,377 September-25 observations. Dataset hash 6487f562543ffc35569853f808af75c48e7805739e4d2b4688cc6cfe7b0dbdc3. Coverage: 26 maps, six modes, five days; actual patch UNKNOWN. 130 strict exclusions. Separate as-of audit: completed runs 9–24, 800 HTTP 200, 9,643 newly eligible, 2,113 duplicate sightings, zero retries/429/conflicts, all raw hashes verified. Active run 25 is explicitly outside the completed raw audit. Sampling audit has 15,828 unique observed player tags, maximum 52 matches/player, no missing tags; no independence claim. See DEVELOPMENT_10K_DATASET.json / AUDIT.json. No quality metrics or new training at this milestone; original Train and working V2 integrity checks pass.

RESUME FROM: batch 03 complete (runs 17–20), 200 HTTP 200 / 2,378 eligible new soloRanked, no retries/429/conflicts. Batch 04 RUNNING: eight finite cycles, each <=50 attempts, /tmp/development-batch-04.log, revision b34d114. Do not restart active collector. Audit immutable membership and all completed raw at 10k. Cumulative completed development runs: 600 attempts / 7,258 strict new, plus 33 pilot (subject to current inventory audit). D-027 frozen; no refitting on September 25. D-028 waits until September 28 UTC; collection continues safely.

D-028 executable forward check complete: rejects scoring before fixed close, verifies frozen candidate/control hashes, preserves exact as-of membership and fails DATA_UNAVAILABLE below 1,000. Fifteen collector/experiment/forward regressions passed (4.081 s). No actual forward evaluation performed. Batch 03 remains active (runs 17/18 complete, 19 running at checkpoint); continue acquisition safely.

RESUME FROM: 5k milestone and D-027 first chronological experiment complete. Batch 03 RUNNING (four bounded 50-attempt cycles), /tmp/development-batch-03.log; do not restart. Continue safe acquisition toward 10k/25k/50k. Do not repeat fitting on the September-25 slice. Fixed DEVELOPMENT forward confirmation is preregistered for September 26–27 UTC, only after close, at least 1,000 eligible; no final test.

Immutable 5k snapshot: 5,212 eligible new soloRanked, plus verified 6,094 original Train; 840 older new / 4,372 latest-day observations. Completed runs 9–16: 400 HTTP 200, 4,880 strict new, zero retries/429/conflicts; raw hashes verified. Active run 17 contributes only to separately timestamped current coverage. See DEVELOPMENT_5K_DATASET.json / AUDIT.json.

D-027 used the FIRST qualifying completed-batch snapshot 004: 6,891 Train / 4,116 chronological Validation. Selected opponent_l2_10: LogLoss 0.689222, Brier 0.248044 versus frozen V2 0.690438 / 0.248649 and retrained team 0.689553 / 0.248209. Small DEVELOPMENT gains only; repeated-player bias, no independent-test claim. Previous negative opponent result preserved. Private frozen candidate archive hash 7468806d5cbeaab580ddd43d0b2ac2932ff64e0ad7fe97b563284ae4633b7c76. Working V2 hash unchanged; Legacy untouched/default. No Legacy metrics or old holdout access. Product/development tests 50 passed; final coverage tests four passed.

D-027 pre-fit reporting completed: active unknown-feature occurrence fraction and explicit Brawler main-effect coverage, in addition to row coverage and measured latency. Four synthetic experiment tests passed. No fit/quality results yet; grid, data gates and selection unchanged. Batch 02 remains active; do not restart it.

RESUME FROM: D-026 batch 01 complete (runs 9–12). Batch 02 is RUNNING, four bounded 50-attempt cycles, /tmp/development-batch-02.log. Do not restart active collection. Snapshot 003 has 2,485 new eligible matches but only 489 older-day Train examples: D-027 gate remains unmet, no fitting. At batch 02 completion create an immutable snapshot and apply the unchanged gates.

Product and development regression suite: 50 passed (7.888 s), including Challenger, planning, exact Legacy comparison, explanations, shadow, collector and experiment selection.

Batch 01: 200 HTTP 200, zero retries/429/conflicts, 2,452 new eligible soloRanked, 484 duplicate sightings, 11,574 authentic discovered tags. Raw integrity verified for all 200 responses. Snapshot includes 33 pilot observations, 26 maps, six modes; actual patch UNKNOWN. See DEVELOPMENT_BATCH_01_DATASET.json and DEVELOPMENT_BATCH_01_AUDIT.json (audit includes early batch-02 progress, explicitly separated). No final test; original registration preserved and aborted; working V2 and Legacy unchanged.

RESUME FROM: D-026 1k milestone verified; collection continues in batch 01 (/tmp/development-batch-01.log), runs 9/10 finished, 11 active at checkpoint. Do not stop or restart the active job. After its four cycles finish, snapshot again; if chronological gates pass, run the committed D-027 fixed experiment, otherwise keep collecting. No final test or working-artifact change.

D-026 1k milestone independently inventoried: 1,447 strict new eligible soloRanked, plus 6,094 verified original Train examples in immutable private snapshot development-20260925-002-1k.json (dataset 22c3542229a481f386df0718c6da6705256d4404af55d7541ebc687ab96ff7da). Coverage: 26 maps, six modes, 21–25 September; actual patch UNKNOWN (imported context ID 1). 46 observations excluded by strict completeness/context/uniqueness rules. No duplicate reconstructed identities or outcome conflicts. Graph bias is measurable: 3,026 observed player tags across 8,682 occurrences; one tag appears in 33 matches. No independence claim. Closed runs 9/10: 100 HTTP 200, no retries/429, 1,130 new eligible and 211 deduplicated sightings. Snapshot also includes committed run-11 progress.

D-027 runner tests: 11 passed (3.063 s). At the 1k snapshot only 446 earlier-day new examples were available, below the 500 new-Train gate; no fitting performed.

RESUME FROM: D-026 repeated development acquisition RUNNING, finite batch 01 (four cycles of at most 50 attempts), log /tmp/development-batch-01.log. Cycle/run 9 completed: 50 HTTP 200, no retries/429/conflicts, 542 strict new eligible soloRanked (563 imported; strict dataset exclusions apply). Subsequent cycles continue automatically. Initial immutable private snapshot development-20260925-001.json verified 6,094 original Train and captured 82 new eligible observations at its earlier timestamp. No quality metrics computed. Before training, use DEVELOPMENT_EXPERIMENT_001_PROTOCOL.json and volume/chronological gates; working V2 unchanged.

RESUME FROM: D-026 collector/dataset tests passed: 43 combined (6.222 s), 20 safety/lifecycle (3.641 s), final 8 development/recovery (2.056 s). Commit/push implementation, then collect repeated 50-attempt bounded development cycles and snapshot/audit at 1k/5k/etc. No model fitting or new final test yet. Original registration is aborted, preserved unchanged.

RESUME FROM: D-026 test and commit sustainable development collection, then start repeated bounded cycles. D-025 aborted evaluation is preserved and blocked; no final window. D-026: sustainable development collector/dataset implementation complete, validation pending. Ranked activity priority with one broader exploration query per five, 50-attempt cycles, unchanged per-player cooldown/client safeguards, global pause on quota signals, durable raw/checkpoints and replay without HTTP. New trophy entries remain raw/discovery-only. Versioned dataset includes verified original Train plus eligible recent development data; no old holdout or protected future final origins. Model development waits for preregistered chronological volume gates. See DEVELOPMENT_COLLECTION.md.

RESUME FROM: D-025 user priority change — prospective evaluation ABORTED_FOR_DEVELOPMENT_BEFORE_EVALUATION. Registration/runs/raw/audits preserved unchanged. Pilot and aborted-window observations are permanently DEVELOPMENT, never a future final test. Abort lifecycle guard and 12 regressions passed (2.124 s). Build sustainable resumable development collection; no new final registration or performance evaluation of the aborted window. Old holdout stays closed; Legacy remains default.

RESUME FROM: D-024 window OPEN; authorized prospective run 8 completed, zero eligible soloRanked. No immediate retry. Next global run gate is 2026-09-25T20:12:18.440952+00:00 (25 September 22:12:18 Europe/Berlin), additionally subject to player cooldowns and remaining protocol budget. Fixed end remains 2026-10-09T00:00:00Z. No quality evaluation before close.

Run 8 completed 2026-09-25T14:12:18.440952+00:00–2026-09-25T14:16:42.334100+00:00: ten battlelog HTTP 200, zero retries/ranking requests, 250 raw entries (233 trophy ranked, one friendly, 16 UNKNOWN). No raw soloRanked and no newly eligible prospective observations: DATA_UNAVAILABLE for this run, not a final window verdict. 94 pre-start entries retained raw-only; 33 unsupported entries skipped. 105 new matches (104 trophy, one friendly), 18 trophy duplicates, zero conflicts. All 105 current-window rows are excluded as non-soloRanked. Current admissible prospective count is zero; no membership sealed.

1,294 new query-eligible tags; discovery frontier 2,665. The cumulative Ranked-evidence frontier remains 56 tags/33 matches from the excluded pilot; these are not prospective observations. All ten raw content hashes, frozen implementation/artifacts and catalog identities verified. Preflight found 1,371 due existing tags and no earlier prospective run. Fourteen focused prospective/future-window regressions passed (3.759 s) on synthetic data.

Evidence: PROSPECTIVE_RUN_008_2026-09-25.json; read-only reproducer: prospective_acquisition_audit.py. Budget consumed: 1 of 56 runs, 10 of 560 HTTP attempts. Protocol digest unchanged: 70e55f3dde205e15b232814f98b4e00c34fac8238f2fe5bc8b190608891adac8. Legacy default, V2 weights, D-022 bundle, registered dates/policy and closed old holdout remain unchanged. No predictions, model-performance metrics, training, catalog refresh, seal or recurring collector.

Next: wait for the registered six-hour run gate; a later due bounded continuation may use the same frozen command and existing frontier. Do not select a different population or change policy based on this zero-yield run. These finite logs lack soloRanked; they do not show that players never play Ranked or negate the earlier acquisition feasibility result. No further immediate collection or model milestone is permitted. Historical resume lines below are superseded.

RESUME FROM: D-024 prospective window REGISTERED; external temporal gate until strictly after 2026-09-25 00:00 UTC (02:00 Europe/Berlin). Do not move dates, repeat pilot, rebuild D-022 or tune either engine. Acquisition feasibility passed with 33 new eligible soloRanked. Current task is waiting for genuinely future observations, not more mechanics/model search.

D-024 REGISTERED_NOT_STARTED. Fixed interval: (2026-09-25T00:00:00Z, 2026-10-09T00:00:00Z]. Registration: 2026-09-24T16:37:53.358317Z. Protocol digest 70e55f3dde205e15b232814f98b4e00c34fac8238f2fe5bc8b190608891adac8; implementation revision e9e6e7714409b566e86197abf01ddbe0957eaa9f. D-022 bundle and V2 artifact remain byte-identical. Fifty-nine combined tests passed (8.696 s). Real read-only pre-start collector check rejected before HTTP/run creation; inventory is zero. No predictions, metrics, training, promotion or recurring collector.

Next authorized action, only inside the fixed interval and when six-hour run/player cooldowns permit: one bounded `collect_prospective_frontier` invocation using PROSPECTIVE_WINDOW.json and the pinned digest above, through the existing isolated Compose/credential pattern. Ten HTTP attempts including retries, depth one, zero ranking requests; maximum 56 runs/560 attempts in the entire window. No automatic recurring collector. Read PROSPECTIVE_RUNBOOK.md first. Do not read performance metrics before close; sealing requires 1,000 eligible common-subset observations, otherwise DATA_UNAVAILABLE without extension. Pilot observations are permanently excluded. Actual game patch remains UNKNOWN; frozen Demo-Patch is only the D-022 algorithmic context.

Registration files and operational check: PROSPECTIVE_REGISTRATION.json, PROSPECTIVE_REGISTRATION_CHECK.json. No prospective collection has occurred. Stop condition: the fixed prospective start has not arrived; no authorized evidence collection or model work can advance the evaluation now. Historical resume instructions below are superseded.

RESUME FROM: D-024 prospective policy implementation/preflight complete; 59 combined regressions passed (8.696 s); commit the implementation and then publish the real prospective registration before its future start. D-023 yielded 33 eligible soloRanked and all 33 fit the frozen common subset. Preserve the completed single-use pilot. Read PROSPECTIVE_RUNBOOK.md.

RESUME FROM: D-023 acquisition gate PASSED; next freeze prospective acquisition policy and exact common-context/patch exclusions, pin D-022/V2/code, then register strictly future dates. Future window is still NOT REGISTERED. Do not rerun the completed single-use pilot. D-022 and V2 remain unchanged.

D-023 pilot completed (run 7, 2026-09-24T16:22:13Z–16:24:00Z): acquisition feasibility demonstrated. Ten battlelog HTTP 200, zero retries/ranking requests. 340 authentic observed query roots; 250 raw entries: 201 trophy ranked, 33 soloRanked, 16 type UNKNOWN. Parser retained all 33 soloRanked; 60 unsupported/non-3v3 entries skipped, zero parser errors or future-dated records. 185 newly imported matches: 152 trophy and 33 eligible soloRanked; five trophy duplicates, zero conflicts. 1,031 additional query tags; discovery frontier 1,371, eligible Ranked-evidence frontier 56. Independent raw/parser/import audit agrees. Pilot matches remain permanently excluded from future test membership and automatic training.

Read DISCOVERY_PILOT_RESULT.json and DISCOVERY_PILOT.md. The earlier three-seed restriction was not an API-wide absence of soloRanked. Sustained throughput and population representativeness remain UNKNOWN. 50 combined tests and 11 final discovery tests passed; additive migration applied only to isolated DB.

RESUME FROM: D-023 discovery/query frontier design implemented and preregistered; single pilot still PENDING. Run DISCOVERY_PILOT_PROTOCOL.json exactly once after the committed checks, using the isolated credential, ten total battlelog attempts, no rankings, depth one. D-022/V2 byte hashes verified unchanged; no bundle rebuild. Future evaluation remains NOT REGISTERED. See DISCOVERY_PILOT.md. Earlier collection prohibitions apply to completed D-020–D-022 tasks, not this newly authorized pilot.

Validation: 50 combined discovery/old-frontier/growth/future-window tests passed (6.084 s). Final 11 discovery/command/cutoff tests passed (1.948 s). Separate discovery tables retain raw pointers, graph edges and battle types; the old frontier is not silently broadened. A linked eligible soloRanked match is required for Ranked-evidence membership. Pilot provenance is excluded from prospective membership even with later accepted sightings. No real API call made yet.

RESUME FROM: D-022 VERIFIED frozen Legacy evaluation bundle. The manual-prior policy blocker is resolved; empirical inputs are rebuilt strictly from Train and priors are frozen B constants. Future window remains NOT REGISTERED. Latest collection evidence is still DATA_UNAVAILABLE (run 6); no collector retry authorized or performed in this task. Read LEGACY_BUNDLE_RUNBOOK.md and FUTURE_EVALUATION_PROTOCOL.md.

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

Next valid continuation: pin the successful receipt/code/V2 hashes and preregister the prospective acquisition/retention plan, fixed dates and exact common-context/patch exclusion rules before any future test window starts. Eligibility requires genuine independent soloRanked; shadow reports/trophy matches cannot replace it. No collection may run under this completed task. Continue using the existing Challenger with Legacy default while evidence is unavailable. Historical resume lines below are superseded.

RESUME FROM: D-021 BLOCKED_PRIOR_LINEAGE. Exact Legacy overlay resolves 137 demo priors (20 Brawler/90 Counter/27 Synergy), which cannot be certified Train-only. All 6,094 Train examples independently match the pinned content hash. No verified bundle built/published; no window registered. Read LEGACY_TRAIN_BUNDLE.md for the precise prerequisite conflict. Resolving it requires an explicit comparison-input policy decision, not another collector retry or fabricated lineage.

Latest validation: 14 bundle/Legacy-parity/future-window regressions passed (5.024 s); read-only real Train/prior audit reproduced. Collection run 6 is complete: three HTTP 200, zero ranking requests/retries, 50 new trophy matches, zero eligible soloRanked (DATA_UNAVAILABLE). 31 collector/growth tests passed (12.849 s). No immediate collection retry. Legacy, V2 weights, live data and closed holdout unchanged. Worktree artifacts: FRONTIER_REVISIT_2026-09-24.json and LEGACY_TRAIN_BUNDLE_PREFLIGHT.json.

Earlier resume lines below are historical checkpoints.

RESUME FROM: D-020 single frontier revisit complete (run 6): three battlelog HTTP 200, zero ranking requests/retries, 50 new trophy ranked matches, zero eligible soloRanked; DATA_UNAVAILABLE. Do not retry. Continue Train-only Legacy bundle provenance verification. 31 collector/growth tests passed (12.849 s).

RESUME FROM: D-019 future-window preparation complete, not registered or evaluated. Shadow capture is usable. External collection gate: zero frontier players due at 2026-09-23T21:51:32Z; earliest stored cooldown 23:39:17Z. Scientific gate: no new eligible soloRanked evidence. Read FUTURE_EVALUATION_PROTOCOL.md before registration; a verified frozen Train-only Legacy input bundle remains required. No old-holdout/model work.

Latest D-019 validation: 46 combined future/shadow/frontier tests passed (4.443 s); eight final future SQL/content/temporal tests passed (1.027 s). Real read-only readiness found three preserved frontier players, zero due, zero new soloRanked, zero real shadow snapshots. Local HTTP/CSRF/static/First/Mid/Last smoke passed after preview reload. Model artifact hash unchanged. No collector request, credentials, model fit, new seal or outcome evaluation.

Current next actions: use opt-in shadow capture while data accumulates; after due time, audit readiness and perform at most one authorized bounded zero-ranking-seed revisit under unchanged safeguards. Before a new test window, archive/audit Train-only Legacy inputs and pin prospective dates/model/code/membership; never use runtime aggregate hashes as proof of train-only lineage. See SHADOW_EVALUATION.md and FUTURE_EVALUATION_PROTOCOL.md. Earlier resume lines below are historical checkpoints.

RESUME FROM: D-018 shadow capture complete; next implement future-window protocol and immutable membership safeguards. Earlier independent-evidence gate still applies to quality claims, not this authorized infrastructure work.

RESUME FROM: D-017 Hideout diagnostic and exact Legacy adapter complete. See HIDEOUT_DIAGNOSTIC.md. D-016 autonomous experimental product checkpoint remains complete. Working First/Mid/Last Challenger, side-by-side Legacy and versioned snapshots are implemented. Remaining stop is scientific: independent future Ranked evaluation evidence unavailable; fixed opponent-interaction experiment failed Validation. Do not reopen old holdout, repeat completed mechanics research or promote by assumption. Full report: CHALLENGER_REPORT.md; operations: CHALLENGER_RUNBOOK.md.

# Drafter V2 Status

Overall:
- D-012–D-016 experimental product milestones complete. Legacy remains default.
- Last Pick ranks complete compositions; Mid/First use disclosed bounded minimax.
- Optional Legacy comparison and private signed Praxisfall snapshots are usable.
- Current phase: independent-evidence/promotion gate, not another infrastructure task.
- Blocker: no independent eligible future test window in completed collection evidence;
  no observed Validation improvement from the preregistered opponent feature grid.
- No current-patch, calibrated-uncertainty or superior-draft-quality claim.

Latest D-018 validation: 19 focused tests passed (3.063 s), V8 parse passed.
Opt-in pre-choice capture, audited later pick/result reporting, both-engine replay and bias provenance implemented. No model/data collection/holdout changes. See SHADOW_EVALUATION.md.

Latest validation (D-017):
- 52 focused tests passed (9.145 s); real read-only Hideout endpoint parity passed.
- V2 probabilities and artifact unchanged; exact additive diagnostic now visible.
- Legacy comparison uses normal als_dict path with full context/data receipt.
- Reported Sprout/Carl/Gray order remains unreproduced; other session inputs UNKNOWN.
- V8 parse and local HTTP/CSRF/static/First/Mid/Last smoke passed.

Previous D-016 validation:
- Full Drafter: 774 tests, four existing skips, no failures (336.643 s).
- Protected Fitness: 253 tests passed (138.720 s).
- Final focused Challenger/content/UX: 13 passed (2.517 s); overlaps full suite.
- JavaScript parsed in V8; real localhost HTTP/static/CSRF/model-info and all three
  phases with comparison passed. No automated rendered-browser/visual test.
- Migration drift clean; additive 0020 applied only to isolated DB. Existing
  isolated Praxisfall count was zero; before/after legacy-field hashes match.
- Legacy scorer, scoring and probability files unchanged from frozen 3a565bd.
- Train/Validation content digests reverified read-only; no new model fit for that
  final integrity check. No held-out examples, labels or predictions loaded.

Runtime:
- Preview: http://127.0.0.1:18080/draft/challenger/
- Container: drafter-v2-challenger-preview; loopback only; Traefik disabled;
  isolated DB and test-only configuration. No live checkout/service rollout.
- Selected model: v2-composition-logit-1, epochs 300/L2 1.0, Train 6,094 /
  Validation 2,031. Validation LogLoss 0.6886038069604661, Brier 0.24774078927297735.
- Artifact: data/brawl_reports/v2_challenger.json (ignored, preserved locally).
  Byte SHA-256 92e0b427bf9abce62e047419ea1008f740c9ee7b39b1458ae15692402b7cf52d.
- Opponent candidates L2 1/10/100 all worse on Validation; not activated.
- Known context mappings: 28; UI uses intersection with selectable catalog maps.
- Initial V2-only smoke First/Mid/Last: 770.071/92.893/44.313 ms; final optional
  comparison HTTP: 3129.532/2457.807/2435.857 ms. Single observations, not percentiles.

Data integrity:
- No fabricated values, raw payload deletion, historical row modification,
  collection, old-holdout evaluation, feature promotion or default-engine switch.
- Membership plus canonical Train/Validation content pinned. Artifact byte digest
  and canonical JSON-content digest are separate fields in committed reports.
- Snapshot outcomes are unverified user reports and not automatic training inputs.
- Historical research, source claims, collector runs 1–5 and sealed reports preserved.

Commits before this final checkpoint (all pushed to existing alex upstream):
- 7229fd9: usable Last Pick and development-only model recovery.
- bf91990: fixed opponent-interaction Validation experiment.
- ec245e9: complete-composition Mid/First planning.
- 356193e: opt-in Legacy comparison and signed snapshots.
- D-016 final UX/integrity/report changes are committed together with this status.

Next valid continuation:
1. Use the experimental product; keep Legacy as default and retain model/log files.
2. To support a scientific quality/promotion claim, obtain independently observed
   eligible future Ranked data under a preregistered temporal/evaluation protocol,
   with training-only statistical inputs. Do not silently reuse the old holdout.
3. Preserve the bounded negative result; no expanded search grid or made-up
   mechanics merely to force an improvement. New data alone does not imply promotion.
4. Restart/stop only the named preview using CHALLENGER_RUNBOOK.md. No production
   operation is needed to use the isolated preview. Keep snapshot metadata on rollback.

## Historical milestone record

The earlier resume/next statements below record prior scopes; the active state
and latest user-authorized product continuation above supersede those pauses.


D-015 complete: explicit Legacy comparison, authenticated signed decision
snapshots, idempotent save/private replay/later user-result controls. Migration
0020 isolated only, no drift. 55 focused tests plus 12 final tests passed.

D-014 complete: 15 tests passed; real isolated First/Mid/Last API smoke 200 each,
770.071/92.893/44.313 ms. First/Mid bounded, complete-team minimax with visible
shortlist limitations. Legacy/default and model artifact unchanged.

D-013 complete: 12 focused tests passed; fixed three-candidate experiment failed
to improve validation. Existing model stays selected. Full report in
CHALLENGER_OPPONENT_EXPERIMENT.json; no held-out evaluation.

D-012 complete: experimental Last-Pick UI/API, validated model loader and
Train/Validation-only trainer. 35 focused tests passed; isolated real page/API
smoke 200/200, 100 legal recommendations, 43.606 ms. Artifact local at
`data/brawl_reports/v2_challenger.json`; no production deployment. Baseline report
committed in CHALLENGER_BASELINE.json. Next D-013 per CHALLENGER_PROTOCOL.md.


Latest completed milestone — D-011 reviewed annotation archive:
- Continued from clean 894148b after user instruction to continue.
- Added standard-library offline archive/CLI for the four D-010 claims; exact
  reviewed artifact SHA-256 required. Source response digests/URLs/sections,
  observed-at, requirements, limitations and null validity survive unchanged.
- Atomic no-replace publication, idempotent import, corrupt/changed artifacts
  rejected for review. No source body availability claim or current revalidation.
- Explanations explicitly describe archived source statements, with unknown
  equipment/activation/current validity. Numeric/historical/current-use requests
  fail closed. No Django schema, runtime/API/UI integration or patch applicator.
- Validation: 7 new tests plus 24 existing offline contracts, 31 passed (0.075 s).
  CLI archive/read replay also checked. No DB/network/credentials accessed.
- Next evidence-dependent step: preregister bounded official-source revalidation
  and define reviewed revision/conflict records before any present-day consumer.
  The fixed-digest archive intentionally cannot ingest arbitrary new evidence.


Latest completed milestone — bounded source follow-up (2026-09-23, D-010):
- Started from clean 33c570c in isolated feature/drafter-v2 worktree. Previous
  5A catalog/identity/probe/inventory JSONs preserved; no repeated roster audit.
- Protocol recorded before fetching: at most 24 public calls, 3 MB per body,
  12 MB retained total, no retries. Actual: 21 top-level fetches, 20 final 200,
  one 404, 3,542,689 bytes. One observed redirect; helper did not instrument
  intermediate redirect hops, so exact wire-attempt count UNKNOWN. This budget
  accounting limitation is documented; future fetchers must count/disable redirects.
- Eight search queries/eight targeted opens separately bounded. Retained old
  bodies verified by hash. No DB opened, API credential loaded or player request.
- Latest mirror head/only branch remains cc307ffd; no newer snapshot found in
  inspected sources. Folder 69.230 versus fingerprint 69.229.1 is an unresolved
  version-label conflict, not an effective patch interval. No claim of global
  impossibility or proof that no unlisted/server hotfix exists.
- Ten missing tables inspected; 12 bounded graph roots, max six edges/400 nodes
  per root. Named links and AND connective are structurally representable.
  Continuation cells preserve order/positions; blanks never become zero/false.
  Only 1/57 components has ValueNames. No opcode, tick-rate or effect interpreter.
- Bolt identity links explicitly translate Rock→BOLT, RocketGirl→BROCK. Selected
  character/gadget row-ID claims are stable in 68.250/69.230. Public Bolt detail
  still includes Brock-target gadget IDs. Kit quarantine remains; no manual repair.
- Units: directly documented seconds/HP/tiles and explicitly millisecond fields
  can retain their stated units; no general power, distance, speed, generic
  cooldown/reload or tick conversion was established.
- Gate A CONDITIONAL allowlist: Shield gear capacity, its full-health regeneration
  duration, Speed gear movement/bush condition, Gene gear range increment. Source,
  observed-at, equipment/context and unknown mode overrides are preserved. This
  permits factual attributed explanations only, not numeric team features/scoring.
  It does not require historical completeness. Revalidate against newer source
  evidence before later reuse; no perpetual validity window is invented.
- Computed current mechanics remain PARTIAL / NOT PASSED on their own current
  evidence. Gate B remains UNAVAILABLE / NOT PASSED: no effective UTC intervals
  or historical equipped loadouts. No old-match join, training or promotion.
- Six reviewed patch-change examples and a minimal provenance/condition/temporal
  contract are documented, not implemented as schema/applicator. Relative-only
  changes retain unknown absolute values; raw snapshots are not overwritten.
- Validation: nine new source-structure tests plus all 15 existing 5A contracts,
  24 total passed (0.006 s). Focused evidence replay byte-identical. No Django
  runtime change or DB test run needed for these standard-library offline tools.
- Durable files: MECHANICS_FOLLOWUP.md, FOLLOWUP_PROBE/METADATA/EVIDENCE JSON,
  CURRENT_CLAIMS and PATCH_EVENTS JSON. Exact resume/replay and source limitations
  are committed under docs/drafter-v2; mutable public metadata has a minimized
  hash-bound projection, so replay does not require it to stay unchanged.

Previous completed milestone — Phase 5A (2026-09-23):
- Started from clean a0242b9 on feature/drafter-v2; preserved 8661c29/run-5 work.
- Fixed catalog: 108 Brawlers / 106 Ranked-available. Read-only isolated queries;
  no live checkout/DB/credential access, collector requests or model experiment.
- 26 bounded public unauthenticated GETs, all HTTP 200, no retries; 12,441,891
  total response bytes. Six relevant mechanics tables, metadata, official docs,
  release pages and one older character snapshot; no bulk game archive import.
- 47-category reproducible coverage plus every Brawler, exact scoped field
  witnesses, source distribution, UNKNOWNs and patch qualification. Offline
  standard-library audit reads pinned CSV/minimized identities, writes stdout.
- 107 corroborated source identity/ability mappings. Bolt remains quarantined:
  two public gadget IDs target RocketGirl instead of Rock. No inferred repair.
- Native CSV distinguishes missing from explicit false/zero; public JSON loses
  that distinction. Base/Super/equipment/Hypercharge/Buffy/Nano/form/summon scopes
  remain separate. Opaque opcodes/dependencies are not decoded into game facts.
- Candidate kit references: gadgets/SP 107 each, Hypercharge/NanoPower 105 each,
  Buffy 27, other trait/event-deck 97. These are source fragments, not known
  equipped, current or Ranked-effective mechanics. Full counts in coverage JSON.
- Four cells remain at values preceding official September-16 changes. No
  source establishes a complete current patch or historical validity join;
  all qualified current-patch field counts remain 0/108 under this audit contract.
- Small verification sample spans ranged/percentage damage, healing, wallbreak,
  mobility, CC, conditional kits, transformation, summon and identity conflict.
- Phase 5B NOT PASSED. Minimal future observation/identity/condition/temporal
  contract proposed only; no schema, feature/formula or strategic rating added.
- Validation: 73 combined mechanics/catalog/identity/provenance/frontier tests
  passed in isolated Django test DB (10.747 s), system check clean. Final 15
  offline audit tests passed (0.012 s), including subsequently added hash replay
  test. Counts overlap; not 88 distinct tests. No API credential loaded.
- Exact reproduction, immutable URLs/digests, frozen catalog, minimized source
  identities and generated results are durable in docs/drafter-v2. Six pinned
  CSVs can be re-fetched explicitly if /tmp is lost; mutable-page replay may fail
  its historical hash. Such failure is documented, never patched with new values.

Previous completed Phase 12B milestone:
- Active/default engine: frozen Legacy `3a565bd`; no runtime/API/UI switch.
- Phase 12B started from clean `b818313`; implementation milestone `8661c29`
  committed and pushed to feature/drafter-v2 before the real experiment.
- Completed D-008: persistent tagged frontier, official-ranking seed provenance,
  observed soloRanked graph-edge support, shared cooldowns and strict HTTP budgets.
- Additive migration 0019 applied only to isolated DB: TaggedPlayer and
  TaggedPlayerObservation. No historical tag migration, deletion or reaggregation.
- Distinct sampling `tagged_frontier_v1`; broad_high_rank selection is unchanged.
- Membership requires fresh raw evidence. Ranking and query observations coexist;
  first source is preserved, subsequent sightings never reset fetch timestamps.
- The official rankings endpoint supplied usable tags. Its trophy position and
  trophies are not Ranked/skill labels. Missing skill/loadout fields stay UNKNOWN.
- Root cause remains irreversible: all 61,146 historical Ranked player rows
  still lack tags. No reconstruction or inferred identity linkage was attempted.
- Worktree: `/home/alex/alex-django-drafter-v2`, branch `feature/drafter-v2`.
  Live checkout, live credential and live database remain out of scope.

Completed bounded experiment:
- Run 5, `2026-09-23T17:39:14.691736Z` to `17:39:20.965188Z`, finished.
- Exact source revision: `8661c291af4ced3e29e12522a34fc0f2ca1356dd`.
- One ranking HTTP attempt, 200 distinct valid returned tag strings, three
  admitted seeds, all three due under existing shared cooldowns.
- Three battlelogs / 75 entries queried; four total HTTP 200 responses,
  zero retries/errors/rate-limit headers. Budget was at most five battlelog
  HTTP attempts including retries, one new request hop; unused budget not spent.
- All 75 entries were trophy `ranked`. Fifty newer unique matches imported;
  25 entries at/before the cutoff retained raw only. Zero imported duplicates
  or conflicts. Zero new eligible soloRanked matches and zero discovered frontier tags.
- Frontier persists three ranking seeds, three ranking observations and three
  query observations. The raw battlelogs preserve 393 distinct observed team tags;
  trophy-only neighbors were not promoted into the Ranked discovery frontier.
- Four complete RawPayloads retained (IDs 925–928). Hashes, schema, run parameters
  and all counts are committed in BOOTSTRAP_EXPERIMENT_2026-09-23.json; no raw
  bodies, player identifiers or credential values committed.
- Isolated credential file loaded only in the bounded collection subprocess.
  HTTP 200 establishes acceptance for this run, not future validity or quota.

Latest read-only validation:
- Post-run frontier audit at `2026-09-23T17:40:46.697857Z`: three frontier members,
  zero due, all historical Ranked tags still blank. Six-hour cooldown retained.
- Isolated inventory: 18,372 matches, 113,276 match players, 881 payload rows,
  205 tracked players, five collector runs, 98 maps. Ranked remains 10,191
  total / 10,162 countable. Zero conflicts/reconstructed-fingerprint duplicates.
- Growth against unchanged exclusive cutoff `2026-09-18T15:04:42Z`: 126 newer
  API matches (125 trophy ranked, one friendly), zero soloRanked, DATA_UNAVAILABLE.
- Tests: expanded 138 collector/API/parser/sampling/UNKNOWN/growth/search/model/
  Praxisfall regressions passed (16.146 s); 38 existing importer/robustness tests
  passed (5.123 s); final 24 frontier tests passed (2.835 s), including frozen-row
  fingerprint collision protection. Normal isolated settings; no API credential
  loaded for tests; system check clean. Migration drift check passed.
- Discovery through actual soloRanked graph edges was NOT observed in this small
  real run. That branch has synthetic regression coverage, not an empirical growth
  claim. No model-level quality improvement or sampling correction is established.
- Earlier full suites (692 Drafter/four skipped; 253 Fitness) are historical,
  not newly run for this patch. Completed runs 1–4 are retained in DATA_AUDIT.

Sealed evaluation (final, unchanged):
- Manifest `v2-dataset-freeze-1`, digest `2bb8222b9025a5da7daadea8b9a252c39b16bcda8b07b9bc2df69315ea4dcf9e`.
- 10,158 eligible historical examples: train 6,094 / validation 2,031 / holdout 2,033.
- Final shared subset n=1,956: Legacy LogLoss/Brier 0.689749/0.248301; V2 0.692600/0.249725.
- Full V2 holdout n=2,033: 0.692603/0.249727; 77 duplicate-Brawler rows are ineligible for unchanged Legacy.
- No historical training, re-evaluation, new split, feature tuning or ranking adjustment during this resume.
- Provenance limitation: Legacy benchmark uses stored aggregates without enforcing train-only input. See EVALUATION.md; final numbers retained, not treated as proof of leakage-free generalization.

Data integrity and recovery:
- Raw responses persist before parsing; exact JSON pointers/run/query provenance
  are durable. Records at/before the cutoff and newer sightings colliding with
  frozen rows remain raw-only. Historical labels, links and player tags stay intact.
- No live access, Legacy modification, sealed-holdout evaluation, model training,
  aggregate update, unbounded recursion, forced timestamps or recurring job.
- Future revisits are supported with ranking-seeds 0 and unchanged six-hour gates,
  but no further run is started by this completed experiment. Concurrent frontier
  runs are locked; failed claims/payloads survive interruption.
- All important evidence is committed in docs/drafter-v2 and persisted in the
  isolated CollectorRun/RawPayload/frontier, not dependent on /tmp files.

Next:
1. Preserve completed 5A/follow-up artifacts and bootstrap runs 1–5. Do not repeat
   inventory, source probes, failed old documentation URLs or collector runs.
2. A subsequent narrowly scoped implementation may store reviewed current claims
   with source snapshots, explicit conditions, as-of attribution and quarantine,
   using the four D-010 allowlisted statements. No automatic implementation in
   this completed research task; no change to active/default Legacy behavior.
3. Broader computed current mechanics require verified current source values,
   units and execution/dependency semantics. Historical completeness is not a
   prerequisite for an independently supported current subset. Do not guess missing
   values or demand all-roster coverage before considering such a bounded subset.
4. Historical mechanics still require valid time boundaries and equipped-loadout
   evidence. Null dates are UNKNOWN, not UTC midnight/open-ended validity.
   Current support or patch announcements never enter old training rows by default.
5. New soloRanked/model evidence remains DATA_UNAVAILABLE. Any future collection
   requires its own bounded plan and cooldowns; none is authorized by this source
   task. The sealed evaluation/shared-subset comparison remains final; new model
   work would require independent preregistered data and train-only statistics.
