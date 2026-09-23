RESUME FROM: Phase 12 / obtain independently sourced tagged soloRanked provenance, verify broad_high_rank candidates with the read-only queue audit, then run one bounded collection only if eligible. Phase 5A source/coverage inventory is the next independent architecture task; no speculative mechanics implementation or sealed evaluation.

# Drafter V2 Status

Overall:
- Active/default engine: frozen Legacy `3a565bd`; no runtime/API/UI switch.
- Completed: user architecture clarification integrated into master sections 12/13/15, PLAN and DECISIONS D-006; no speculative mechanics implemented.
- Completed collection: run 4 started `2026-09-22T18:13:43.707390Z` at code revision `cd6481e`, finished with zero battlelogs/requests/new matches. The authorized mode-600 isolated credential loaded only for that process; no secret was exposed. Remote credential validity was not exercised.
- Genuine data blocker: anonymized Ranked player rows have no tags, so broad_high_rank has zero qualifying candidates. This supersedes the old credential-inheritance blocker; cooldown bypass cannot solve it (D-007).
- Growth status: DATA_UNAVAILABLE; zero eligible API soloRanked matches played after `2026-09-18T15:04:42Z`.
- Worktree: `/home/alex/alex-django-drafter-v2`, branch `feature/drafter-v2`. Live checkout and database remain out of scope.

Latest validation:
- Read-only post-run inventory: 18,322 matches, 112,776 match players, 877 payload rows, 205 tracked players, four collector runs and 98 maps.
- Ranked: 10,191 total / 10,162 countable; zero conflicts and reconstructed-fingerprint duplicates.
- Growth: 76 newer API matches (75 trophy ranked, one friendly), zero newer soloRanked. Latest API Ranked time remains `2026-09-18T15:04:42Z`.
- Queue diagnosis at `2026-09-22T18:15:25.024440Z`: 61,146 Ranked player rows, zero with tags, zero broad-qualified players; 205 active tracked depth<=1, 200 due, zero due broad-qualified. Counts are from that audit time, not a promise of future cooldown state.
- Reproduction on `2026-09-23T17:11:57.566647Z`: 205 players now due, still zero tagged Ranked rows and zero broad-qualified candidates; waiting did not resolve the prerequisite. Output: `/tmp/drafter-v2-queue-reproduced.json`.
- Reproducer: `docs/drafter-v2/collection_queue_audit.py` via the read-only command in COLLECTION_RUNBOOK.md. Reports: `/tmp/drafter-v2-bounded-{audit,growth,queue}.json`.
- Current regressions: 94 isolated collector/API-client/sampling/UNKNOWN/growth/search/model/Praxisfall tests passed, zero failures, 13.401 s test runtime; normal settings, system check clean, no API credential loaded for tests.
- Historical validation: prior 66-test targeted suite passed; prior agent's full suites 692 Drafter (four skipped) and 253 Fitness passed. These historical runs are not new results.
- Architecture validation: all nine requested clarifications mapped to master/plan acceptance gates. Prospective mechanics tests are not yet implemented or claimed as passed.

Sealed evaluation (final, unchanged):
- Manifest `v2-dataset-freeze-1`, digest `2bb8222b9025a5da7daadea8b9a252c39b16bcda8b07b9bc2df69315ea4dcf9e`.
- 10,158 eligible historical examples: train 6,094 / validation 2,031 / holdout 2,033.
- Final shared subset n=1,956: Legacy LogLoss/Brier 0.689749/0.248301; V2 0.692600/0.249725.
- Full V2 holdout n=2,033: 0.692603/0.249727; 77 duplicate-Brawler rows are ineligible for unchanged Legacy.
- No historical training, re-evaluation, new split, feature tuning or ranking adjustment during this resume.
- Provenance limitation: Legacy benchmark uses stored aggregates without enforcing train-only input. See EVALUATION.md; final numbers retained, not treated as proof of leakage-free generalization.

Data integrity:
- No invented observations, mechanics, API fields, identity linkage or historical loadouts; UNKNOWN remains UNKNOWN.
- Only an isolated CollectorRun record was added by run 4; no API request, raw import, reaggregation, schema change or data deletion. Existing snapshots and prior notes preserved.
- No live credential/checkout/database access, service restart, sealed-holdout rerun, tuning, or Legacy engine change.

Next:
1. Resolve missing tagged Ranked provenance using independently supplied genuine payloads and the normal isolated importer. Re-run the read-only queue diagnostic; do not reconstruct redacted identities, reset timestamps, weaken deduplication or silently change strategy.
2. Once broad-qualified due players exist, load the authorized isolated credential only for one run with at most five battlelogs, depth 1 and six-hour spacing. Audit growth against the unchanged cutoff afterward; zero evidence remains DATA_UNAVAILABLE. Do not repeat the already completed empty run.
3. Independently, Phase 5A may inventory allowed sources and mechanics coverage. Establish actual source/patch/condition coverage before implementing a schema or derived features. D-006 and PLAN define the new contracts; no hand ratings or modern-value backfills.
4. Before any model experiment, preregister new immutable split membership and train-only statistical inputs. Keep the historical holdout/shared subset closed; V2 search/explanations remain offline until validated.
