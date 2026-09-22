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
