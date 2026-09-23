RESUME FROM: Phase 12B complete. Bounded bootstrap run 5 (code 8661c29) is finished and must not be repeated as unfinished work. DATA_UNAVAILABLE: zero genuinely newer eligible soloRanked matches. Next independent task is Phase 5A source/coverage inventory under D-006; no more collection, model tuning, freeze or evaluation in this experiment. Inspect this status, the committed BOOTSTRAP_EXPERIMENT_2026-09-23.json and the local tree before resuming.

# Drafter V2 Status

Overall:
- Active/default engine: frozen Legacy `3a565bd`; no runtime/API/UI switch.
- Started this task from clean `b818313`; implementation milestone `8661c29`
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
1. Do not rerun completed bootstrap 5 or the empty broad run 4. Retain
   DATA_UNAVAILABLE for new Ranked/model evidence; trophy tags cannot fill that gap.
2. Continue independent Phase 5A allowed-source and mechanics coverage inventory
   under D-006 and PLAN. Establish actual source/patch/condition coverage before
   schema/features; no hand ratings, LLM-filled mechanics or historical loadout guesses.
3. Any future collection experiment needs a documented bounded plan (sample, timing,
   request/depth budget, cooldowns and stop conditions). Preserve the current frontier.
4. Before any model experiment, preregister immutable new temporal membership and
   training-only statistical inputs. Historical holdout/shared subset remain closed.
