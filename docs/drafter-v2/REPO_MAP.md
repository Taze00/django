# Drafter V2 Repository Map

## Protected boundaries
- Drafter scope: `drafter/`, `templates/drafter/`, `static/drafter/`, Drafter tests, `docs/drafter-v2/`.
- Protected apps/pages: `fitness/`, `fitness-frontend/`, `films/`, Portfolio templates/static and unrelated management data.
- Shared files (`meinprojekt/settings.py`, `meinprojekt/urls.py`, Compose) change only when a V2 contract requires it and must be separately validated.

## Runtime data flow
```text
Browser /draft/
  -> templates/drafter + static/drafter
  -> meinprojekt/urls.py -> drafter.urls -> drafter.views.api
  -> context_aus_daten -> DraftEngine
  -> providers/registry -> Datenraum / aggregation-derived stats
  -> PostgreSQL models (Brawler, maps, stats, patches, praxis)
  -> JSON response / analysis UI
```

## Ingestion and statistics
```text
Official API or fixture
  -> brawl_api_client / collector
  -> RawPayload (unchanged, provenance)
  -> importer + fingerprint
  -> Match / MatchPlayer / MatchBan (deduplicated)
  -> aggregation
  -> BrawlerStat / CounterStat / SynergyStat / BuildStat
  -> StatProvider
  -> Legacy DraftEngine
```

Raw payloads default to `data/brawl_api_raw/`, reports to `data/brawl_reports/`; both are outside Git and must never be copied from or written to the live checkout. `Match` is the unit counted by aggregation. Conflicts are excluded; unknown values remain empty/unknown.

## Existing control points
- Settings/database: `meinprojekt/settings.py`, `settings_test.py`
- URLs: `meinprojekt/urls.py`, `drafter/urls.py`
- Engine: `drafter/services/draft_engine.py`, `scoring.py`, `win_probability.py`
- Providers: `drafter/services/providers/`
- Ingest: `drafter/services/ingest/`, `collector.py`
- Models: `drafter/models/`
- Commands: `drafter/management/commands/`
- Tests: `drafter/tests/`
- Frozen snapshots: `drafter/models/praxis.py`

## Legacy boundary
The current Legacy scorer remains the production implementation until a separately versioned V2 model passes the frozen evaluation and regression gates. No Phase-0 change alters scoring behavior.


## Post-freeze continuation
- `management/commands/drafter_v2_growth.py`: read-only, API-only inventory of
  observations strictly after an explicit timestamp; no model or evaluator imports.
- `tests/test_v2_growth.py`: boundary, unknown-data, source, dedup-sighting,
  read-only and collector-summary contracts on isolated synthetic test records.
- `docs/drafter-v2/COLLECTION_RUNBOOK.md`: isolated credential, request-budget,
  growth-audit and future-experiment procedure.


Tagged-frontier collection (D-008): `drafter/services/tagged_frontier.py`, command
`collect_tagged_frontier`, new TaggedPlayer/TaggedPlayerObservation models in
`models/collector.py`, additive migration 0019, `tests/test_tagged_frontier.py`.
Uses existing BrawlApiClient/parser/importer; shared cooldowns remain on TrackedPlayer.
`docs/drafter-v2/frontier_audit.py` is a read-only aggregate provenance reproducer.
No runtime/UI/Legacy/model integration.


Phase 5A offline inventory additions (D-009):
- `drafter/services/v2_mechanics_audit.py`: standard-library CLI, hash-pinned
  local CSV/identity inputs to coverage stdout; no Django/client/runtime import.
- `drafter/tests/test_v2_mechanics_audit.py`: synthetic provenance/UNKNOWN/scope/
  bounded-traversal and exact replay contracts, no external data or API requests.
- `docs/drafter-v2/MECHANICS_SOURCES.md`, `MECHANICS_COVERAGE.md`, `MECHANICS_*json`:
  source register, frozen catalog/minimized identities, request hashes and
  reproducible aggregate/per-Brawler evidence. No final mechanics schema.


D-010 bounded follow-up additions:
- `drafter/services/v2_mechanics_followup.py`: offline continuation-aware source
  structure/identity report, no patch application, feature or runtime consumer.
- `drafter/tests/test_v2_mechanics_followup.py`: nine synthetic source contracts.
- `docs/drafter-v2/MECHANICS_FOLLOWUP*`, `MECHANICS_CURRENT_CLAIMS*`,
  `MECHANICS_PATCH_EVENTS*`: bounded evidence and independent current/historical
  gates; the original 5A JSONs remain frozen.

## Offline reviewed claims (D-011)

- `drafter/services/v2_mechanics_claims.py`: closed reviewed-artifact allowlist,
  atomic no-replace annotation archive and dated conditional explanation CLI.
- `drafter/tests/test_v2_mechanics_claims.py`: preservation, rejection, corruption,
  idempotence and use-boundary tests; standard library only.
- `docs/drafter-v2/MECHANICS_CLAIM_ARCHIVE.md`: reproduction and scope limits.
No Django model, migration, endpoint or scoring consumer added.

## Experimental Challenger (D-012)

`v2_challenger_training.py` / `drafter_v2_challenger_train`: verified development
partitions and model/provenance/support artifact (ignored data/brawl_reports).
`v2_challenger.py`: validated model runtime and Last-Pick ranking.
`views/challenger.py`, Drafter URLs, `templates/drafter/challenger.html` and
`static/drafter/challenger.js`: separate opt-in UI/API; Legacy flow untouched.
`test_v2_challenger.py`: endpoint/model/legality/holdout access regression contracts.

D-013: `drafter_v2_challenger_experiment` runs the fixed Train/Validation-only
grid. `v2_model`/`v2_explanation` support versioned antisymmetric opponent terms;
current runtime artifact remains the original model. Report in
CHALLENGER_OPPONENT_EXPERIMENT.json; candidate artifact stays local/ignored.

D-014: `v2_planning.py` provides budgeted memoized full-composition minimax;
`test_v2_planning.py` checks completed leaves, exact toy minimax, turn order,
legal continuations, determinism and budget failure. Challenger UI accepts empty
slots and explicit first-pick side. Old partial-search prototype is not the runtime.

D-015: `v2_snapshots.py` signs owner-bound responses and saves immutable recommendation
snapshots into Praxisfall. Additive `0020_challenger_snapshot` adds snapshot key and
metadata only. Challenger views expose authenticated save/list/detail/result APIs;
UI offers opt-in Legacy comparison, save buttons and outcome controls. Scoped
`challenger.css` uses a Drafter-base head extension; protected app layouts untouched.

D-016: model-info endpoint supplies only known model contexts; UI filters available
maps accordingly and explanations use catalog display names. Development loader
pins content as well as membership digests. `CHALLENGER_REPORT.md` consolidates
product acceptance/evidence; `CHALLENGER_HTTP_SMOKE.json` retains final local HTTP
observations. Preview container `drafter-v2-challenger-preview` binds loopback
18080 with Traefik disabled; no live service replacement.


## D-017 diagnostic integration
`services/v2_legacy_comparison.py` wraps exact unchanged normal Legacy als_dict
path and hashes resolved/loaded inputs. `services/v2_diagnostics.py` partitions
actual complete-composition features and compares candidates without scoring
changes. Challenger UI shows receipts, normal-endpoint verification, relative
terms and evidence limits. `docs/drafter-v2/hideout_diagnostic.py` is a read-only
runtime reproducer; matching JSON/Markdown retain measured evidence. No other app
or default Legacy path changes.


D-018: v2_snapshots stores canonical response digest, context/bias provenance and row-locked user-report history. challenger view exposes explicit authenticated shadow_capture; existing result endpoint also accepts chosen. Challenger UI offers capture and later reporting/replay. No other app/default Legacy path changed.


D-019: services/v2_future_window.py supplies pure preregistration/seal/publication/integrity contracts; management/commands/drafter_v2_future_window.py supplies read-only temporal inventory and optional sealing/verification. docs shadow_frontier_readiness.py audits counts/cooldowns without credentials or holdout data. No evaluator, collector schedule, migration or shared-app change.


D-021 services/v2_legacy_bundle.py and drafter_v2_legacy_bundle_audit command implement read-only fail-closed Train/prior preflight, not aggregation/export/promotion. Explicit Train key predicate avoids Validation and holdout examples. Provenance metadata only; no raw bodies or credentials logged.


D-022: management/commands/drafter_v2_legacy_export.py exports only pinned Train and frozen B constants under read-only repeatable read. offline/legacy_bundle.py configures standalone temporary SQLite and uses original aggregation/scoring; offline/verify_legacy_bundle.py independently audits counts/membership and binds rebuild/replay receipts. gzip data are private ignored local artifacts. Future protocol schema 2 requires verified receipt.


D-023: models/discovery.py and migration 0021 hold separate query/provenance state; services/discovery_frontier.py reuses bounded tagged-frontier safeguards; collect_discovery_pilot accepts a pinned single-use pilot protocol. DISCOVERY_PILOT.md documents it.


D-024: services/prospective_acquisition.py and collect_prospective_frontier provide one bounded run; v2_future_window schema 3 binds feasibility, fixed common catalog and purpose/code/protocol provenance. prospective_preflight.py audits only frozen catalog and run-7 examples; no predictions.


D-026: sustainable development collector/dataset implementation complete, validation pending. Ranked activity priority with one broader exploration query per five, 50-attempt cycles, unchanged per-player cooldown/client safeguards, global pause on quota signals, durable raw/checkpoints and replay without HTTP. New trophy entries remain raw/discovery-only. Versioned dataset includes verified original Train plus eligible recent development data; no old holdout or protected future final origins. Model development waits for preregistered chronological volume gates. See DEVELOPMENT_COLLECTION.md.

D-027: development_experiment.py and drafter_development_experiment load only pinned development memberships, reverify content/lineage, and run the fixed grid. No Legacy evaluation and no artifact replacement.
