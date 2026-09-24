# Exact Train-only Legacy bundle — BLOCKED_PRIOR_LINEAGE

The collection prerequisite was attempted exactly once as run 6. The separate
Legacy prerequisite was then audited independently. No verified bundle was built
or published, and no future window was registered. This is a failed scientific
prerequisite, not a completed bundle or a runtime aggregate digest relabeled as
Train-only evidence.

## Verified Train inputs

The unchanged selected V2 artifact has byte hash
`92e0b427bf9abce62e047419ea1008f740c9ee7b39b1458ae15692402b7cf52d`.
Its retained 6,094 Train fingerprints allow direct membership queries; no original
freeze reconstruction, Validation examples or holdout examples are loaded.

The independent database read verifies uniqueness, order, count and complete
composition/outcome content against the previously pinned Train digest:
`5e8ff094ad9f93ed565bcaed9f725ffd7d78dd67c22e31c7b6aaed6cd2cec447`.
All 6,094 rows have source api. Observed range: 2026-08-29T00:48:08Z through
2026-09-17T21:43:04Z. Raw provenance is inspected only as metadata/content hashes;
shared raw response bodies are not loaded. No player tags or outcomes are printed.
No model is fitted, evaluated or changed.

## Exact prior contradiction

Actual provider: `OverlayStatProvider`, configured `auto`. Its measured side is
separate from its demo/manual prior side. `Datenraum.laden()` explicitly loads
both sides; the scoring components decide how those priors contribute.

| Input | Stored demo rows | Resolved Hideout / masters prior rows |
|---|---:|---:|
| Brawler | 20 | 20 |
| Counter | 90 | 90 |
| Synergy | 27 | 27 |
| Build | 0 | 0 |

All 137 resolved prior records have source demo. The seed implementation supplies
META rates and COUNTER/SYNERGY values from hand-set seed data, rather than Train
matches. Provider documentation identifies demo/manual rows as curated estimates.
These are required inputs of the exact current provider path. Being selected into
a prior table does not mean every row materially affects every candidate score;
no numerical effect size is asserted here.

The runtime measured tables contain 11,823 Brawler, 57,558 Counter and 48,528
Synergy API rows, with no Build rows. Those counts/hashes prove neither Train-only
membership nor historical input timing. No runtime measured aggregate was copied
into a proposed verified bundle. A rebuild in an empty scratch database could
establish measured Train lineage, but cannot establish Train lineage for these
hand-set priors. Therefore it was not run under a false claim of exact equivalence.

## What was preserved and what is not complete

`LEGACY_TRAIN_BUNDLE_PREFLIGHT.json` records the actual provider, source counts,
resolved-prior hashes, independently verified Train digest/membership, catalog,
configuration and source-metadata digests. Catalog covers modes/maps/patches,
Brawlers, balance changes, equipment and build rules. Service-code hashes identify
the implementation read. These are diagnostic integrity receipts, NOT a restorable
scoring bundle, NOT complete per-aggregate lineage, and NOT proof that fixed catalog
profiles/configuration originated from Train. No current/default inputs changed.

The preflight returns `verified: false` even if a future database has no demo
rows: absence alone would not prove measured aggregates or catalog lineage.
Positive verification still requires an actual isolated rebuild, source-membership
and prior audit, restorable input export, and independent scoring replay.

## Resolution needed before proceeding

The present requirements jointly demand exact frozen Legacy inputs and Train-only
lineage for its priors. Existing demo priors cannot satisfy both. Do not invent
observation membership, silently drop/zero the prior tables, reclassify demo as api,
or modify the default engine to make a check pass.

A subsequent explicit comparison-protocol decision must resolve this distinction:
either allow and disclose fixed non-learned Legacy priors as baseline constants
while requiring Train-only empirical statistics, or define a separate baseline
input variant with differently sourced priors. Neither is the currently requested
all-inputs-Train-only exact bundle. No option was silently selected. Even after
that decision, catalog/profile and empirical source lineage need their own audit;
a prior-policy revision is not automatic verification or permission to reopen
historical held-out data.

## Reproduce

Use the isolated project with read-only DB enforcement and no API credential:

```sh
DJANGO_SECRET_KEY=drafter-v2-isolated-test-only DJANGO_REGISTRATION_KEY=disabled \
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
-e PYTHONDONTWRITEBYTECODE=1 -e 'PGOPTIONS=-c default_transaction_read_only=on' \
--entrypoint python django-dev manage.py drafter_v2_legacy_bundle_audit
```

Validation: 14 focused bundle/Legacy-parity/future-window tests passed (5.024 s).
Tests prove demo/manual cannot pass the gate, measured-only is not assumed
Train-only, direct Train selection excludes other examples, and modified labels
or membership fail. Earlier run-6 collector/growth validation: 31 passed (12.849 s).
All fixtures are synthetic tests, not newly collected Ranked observations.
