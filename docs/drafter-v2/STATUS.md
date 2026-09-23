RESUME FROM: Phase 12B / implementation tested; inspect latest CollectorRun and migration state, apply additive 0019 only to isolation if pending, then execute exactly one authorized tagged-frontier bootstrap from COLLECTION_RUNBOOK.md (three ranking seeds, one ranking HTTP attempt, five battlelog HTTP attempts including retries, one new request hop). No real bootstrap request has run yet at this milestone. Audit new growth against the fixed cutoff, record evidence, commit and push; do not repeat runs 1–4 or reopen evaluation.

# Drafter V2 Status

Overall:
- Active/default engine: frozen Legacy `3a565bd`; no runtime/API/UI switch.
- Starting revision for this task: `b818313`, clean isolated feature/drafter-v2 worktree.
- Implemented D-008: persistent tagged frontier, official ranking seed provenance,
  observed soloRanked graph edges, shared player cooldowns and bounded request budget.
- Additive migration 0019 creates only TaggedPlayer and TaggedPlayerObservation;
  no data migration, historical tag backfill, deletion, aggregation or model change.
- Distinct sampling `tagged_frontier_v1`; no change to broad_high_rank selection.
- Frontier admission needs new raw evidence; the existing 205 queue entries are
  not silently adopted. Each source has exact raw JSON/run/parent provenance.
- Six-hour revisit and durable pre-request claim; depth bounds new request hops
  within a run, while boundary discoveries persist for future runs. No scheduler.
- Master/PLAN/DECISIONS/runbook describe the explicit revised bootstrap authorization.
- The root cause remains established: all 61,146 historical Ranked player rows
  lack tags. Their identities remain UNKNOWN and will never be reconstructed.
- Worktree: `/home/alex/alex-django-drafter-v2`, branch `feature/drafter-v2`.
  Live checkout, live credential and live database remain out of scope.

Pre-experiment validation:
- Focused initial 74 tests passed (7.214 s); expanded 138 collector, API, parser,
  sampling, UNKNOWN, growth, V2 search/model and Praxisfall regressions passed
  (16.146 s). Synthetic test data only, normal settings, system check clean.
- Additional 38 existing importer/robustness tests passed (5.123 s); final
  24 frontier tests passed (2.835 s), including frozen-boundary fingerprint
  collision protection. Migration drift check passed; migration plan contains
  only the two new tables. Migration remains unapplied before the experiment.
- No API credential loaded for tests; only disposable isolated test_postgres used.
- The existing API client documents verified global trophy-ranking tag responses;
  current isolated credential acceptance and current schema still require the
  bounded real experiment. No model-level benefit is asserted by unit tests.
- Isolated DB mount/network reverified: worktree data/db only,
  drafter-v2-isolated_backend only. Compose uses --no-deps one-off containers.

Latest real-data evidence (pre-bootstrap, unchanged):
- Runs 1–4 remain final. Run 4 at 2026-09-22T18:13:43.707390Z (cd6481e)
  queried zero players and made zero requests because broad provenance was absent.
- 18,322 matches, 112,776 match players, 877 payload rows, 205 tracked players,
  four collector runs, 98 maps. Ranked 10,191 total / 10,162 countable.
- Zero conflicts/reconstructed-fingerprint duplicates. Growth DATA_UNAVAILABLE:
  no eligible API soloRanked after 2026-09-18T15:04:42Z; 76 newer API matches
  consist of 75 trophy ranked and one friendly.
- Read-only reproduction on 2026-09-23T17:11:57.566647Z: 205 old queue players
  due, zero tagged Ranked rows and zero broad-qualified candidates. Waiting
  cannot repair anonymization. See collection_queue_audit.py and D-007.

Sealed evaluation (final, unchanged):
- Manifest `v2-dataset-freeze-1`, digest `2bb8222b9025a5da7daadea8b9a252c39b16bcda8b07b9bc2df69315ea4dcf9e`.
- 10,158 eligible historical examples: train 6,094 / validation 2,031 / holdout 2,033.
- Final shared subset n=1,956: Legacy LogLoss/Brier 0.689749/0.248301; V2 0.692600/0.249725.
- Full V2 holdout n=2,033: 0.692603/0.249727; 77 duplicate-Brawler rows are ineligible for unchanged Legacy.
- No historical training, re-evaluation, new split, feature tuning or ranking adjustment during this resume.
- Provenance limitation: Legacy benchmark uses stored aggregates without enforcing train-only input. See EVALUATION.md; final numbers retained, not treated as proof of leakage-free generalization.

Data integrity and recovery:
- No real bootstrap API calls or imports at this implementation milestone.
- Raw responses persist before parsing. Records at/before the sealed cutoff are
  retained raw only; newer duplicates use the existing fingerprint/importer.
- Failure evidence and claims survive interruption. Inspect CollectorRun and
  raw payloads before resuming; never reset timestamps or refetch to hide failure.
- No credentials, raw bodies or player identities committed. UNKNOWN stays UNKNOWN.
- Earlier full suites (692 Drafter/four skipped; 253 Fitness) are historical,
  not newly run or claims about this patch.

Next:
1. Follow the RESUME FROM line and exact runbook; one bounded real experiment only.
2. Run PostgreSQL read-only frontier_audit.py, drafter_v2_audit and drafter_v2_growth.
   Record run/revision, actual seed/request/status/retry/discovery/match/duplicate
   counts and resulting frontier. Missing ranking tags is a concrete stop condition.
3. If zero new eligible Ranked observations, record DATA_UNAVAILABLE and stop
   collection. No expanded population, request budget, model freeze or tuning.
4. Independent future task: Phase 5A source/coverage inventory under D-006. Any
   model experiment needs a preregistered new immutable temporal protocol and
   training-only statistical inputs; the historical holdout stays closed.
