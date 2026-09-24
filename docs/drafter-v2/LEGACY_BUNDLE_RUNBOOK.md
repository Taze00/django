# Frozen Legacy evaluation bundle (D-022)

The user's D-022 decision permits the existing 137 manual/demo priors as frozen
algorithmic constants. It supersedes the all-inputs-Train-only gate in D-021.
Empirical inputs remain strictly Train-only. Production Legacy and V2 are unchanged.
No ablation replaces the primary baseline. No collector is run in this milestone.

## Input classification and required/optional unknowns

| Input group | Class | Handling |
|---|---|---|
| Brawler, Counter, Synergy empirical statistics and empirical shrinkage priors | A | Rebuilt by the unchanged aggregator from the exact 6,094 Train keys only. Per-window/pool membership is archived and independently checked. |
| Empirical Build/Ban observations | A | Exported only when recorded for Train. Current Train has zero bans and zero nonempty builds; no empirical Build rows are invented. |
| 20 Brawler, 90 Counter, 27 Synergy prior records | B | Full original records, including source, explanation, confidence, timestamps and all values, frozen unchanged. Never labeled Train-derived. |
| Brawler identity/availability/profiles, mode/map requirements/traits, patch definitions | B | Entire pre-existing records frozen. Profiles/traits are Legacy algorithmic assumptions, not validated mechanics or outcome-derived estimates. Missing profile facts retain Legacy UNKNOWN semantics. |
| Balance-change constants, item catalog and build rules | B | Complete tables included even when empty. Current archive has no rows in these tables. Their absence supplies no fabricated loadout/mechanics evidence. |
| Config weights, thresholds, smoothing constants, pool/window rules, provider selection, model code | B | Complete configuration and 70 implementation source files pinned; changed code/config/environment is rejected. |
| Aggregation date, scoring date, timezone, empty personal preferences and complete-team evaluation context | B | Aggregation date is Train end date, 2026-09-17. Scoring clock is export date, 2026-09-24 UTC. Future date changes cannot decay the same bundle differently. Rank pool for primary replay is alle; complete-team first-pick is the fixed Legacy default true, an evaluation convention, not an observed historical fact. |
| New required table/code/config/identity outside the archive | C | Fail closed. No runtime database fallback or missing identity inference. |
| Optional unknown profiles, equipment, ban/order/skill metadata | C, optional | Preserve missingness and unchanged Legacy handling; do not turn missing observations into facts. No future ranking/causal claim from missing draft context. |

Every column of catalog tables is retained under B. Every column of a measured
stat row inherits A; rows carrying demo/manual source inherit B. Surrogate IDs and
auto-generated creation/update timestamps on newly built empirical rows are omitted
from their canonical identity because they are not scoring inputs. Raw prior rows
are compared without that normalization. All required foreign-key resolutions are
checked in each scratch database. Scoring SQL may access only the explicit catalog
and statistics table allowlist; Match/RawPayload and other tables are rejected.

## Export and isolation

`drafter_v2_legacy_export` opens a read-only repeatable-read transaction and checks
the frozen V2 artifact byte hash, original Train content digest, ordered Train
membership and the D-021 prior content digest. It selects Match/players/bans only
by the 6,094 pinned Train fingerprints. It never reads runtime empirical tables.
Original Match-to-RawPayload metadata links, raw content hashes and collector/
sampling/source fields are retained; raw bodies and player provenance are not
invented. The archive is private local data, not committed to the public repository.

An initial export attempt prefetched shared raw response bodies unnecessarily;
those bodies were not inspected, exported or used for aggregation. This was
corrected to metadata-column-only prefetch, covered by a SQL regression, and the
final input archive was regenerated. No Validation/holdout Match examples were
selected, predicted or used. Do not claim the initial attempt never loaded an
unused raw body; the corrected archive and all empirical derivations remain
restricted to Train.

Example export (new output path only):

```sh
DJANGO_SECRET_KEY=drafter-v2-isolated-test-only DJANGO_REGISTRATION_KEY=disabled \
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
-e PYTHONDONTWRITEBYTECODE=1 -e 'PGOPTIONS=-c default_transaction_read_only=on' \
--entrypoint python django-dev manage.py drafter_v2_legacy_export \
--output data/brawl_reports/legacy-input-final.json.gz --revision 839163a
```

The actual frozen archive is already present; the command deliberately refuses
overwrite. A new export has a new capture timestamp and identity. Reproduction
uses the existing pinned input archive, not a new runtime snapshot.

Offline builder: `python -m drafter.offline.legacy_bundle INPUT.gz OUTPUT.gz
 --expected-input-sha256 HASH`. It configures only a new temporary SQLite database;
project PostgreSQL settings and API credentials are not loaded. It copies frozen
catalog/priors, restores Train-only observations, verifies their content again,
and runs the unchanged Aggregator over all configured pools/windows. Runtime
statistics, live services and the isolated source DB are untouched. Temporary
inserts are batched in a transaction. No recursive permissions or data reset.

Build twice into distinct output paths. Their decompressed canonical content must
match exactly. Deterministic gzip is used, but the normative content digest is
separate from compressed-file bytes. Implementation source text is archived, and
replay refuses mismatched working code, provider config or Python/Django/SQLite
versions. Restore the pinned source revision/files in a separate checkout if the
working implementation has since changed; do not roll back the default engine.

## Independent verification and replay

The builder exercises one unique valid Train composition per observed map/mode/
patch context, without selecting by result or scoring any quality metric. Both
direct `DraftEngine(ctx).siegchance()` and an explicitly injected Datenraum must
agree. It also records the exact serialized normal Last-Pick recommendation list.
These are replay checks, not extra training, tuning or evaluation on held-out data.

`--replay` takes a built archive and its pinned content digest, restores only
catalog/constants/empirical tables into another empty scratch DB, and checks all
probability/ranking probe hashes. Train compositions are supplied from the archive
as probe contexts; the scorer cannot query Match/RawPayload tables. This proves
persistence and intended Legacy-path fidelity, not equality to the production
runtime aggregate table contents, which were intentionally not reused.

`python -m drafter.offline.verify_legacy_bundle FIRST.gz SECOND.gz REPLAY.gz
 REPORT.json --bundle-sha256 HASH --replay-sha256 HASH` is a separate standard-
library verifier. It recomputes pool/window membership and every empirical row's
raw games/wins directly from exported Train fields without invoking Aggregator.
It checks prior identity and independent rebuild/replay receipts. It fails closed
if supplementary build/ban data appear that its independent count audit does not
yet implement; the current observed Train has neither. Smoothed/weighted values
are reproduced by independent fresh executions of the exact frozen aggregator;
they are not independently derived by this raw-count audit.

Verification output and hashes are preserved separately in the D-022 report.
Filesystem access is not WORM storage: privileged users can change files, but
pinned digests reject changed archives. Readers never consult live aggregates;
future rows cannot enter a frozen archive implicitly. Keep the verification
receipt and digest in version control independently of the local gzip files.

## Prospective registration remains a separate action

The policy is now `train_empirical_frozen_manual_constants_v1`; future protocol
schema 2 requires the actual successful verification receipt, matching bundle
hash, all verification checks, no required unknown inputs, and a freeze date no
later than registration. A naked runtime hash or an unverified build is rejected.
No future window is registered by exporting, rebuilding or verifying this bundle.

Before registration, pin the final code/receipt/V2 hashes, future eligibility and
common-subset rules (including unsupported map/Brawler and patch treatment),
prospective fixed dates, and a bounded acquisition/retention plan for genuine
soloRanked observations. Preserve the negative opponent experiment and prohibit
all tuning on the new window. Current run-6 evidence remains DATA_UNAVAILABLE;
this task authorizes no collection retry or recurring job. Shadow logs remain
separate biased observations, not substitutes for independent API test data.


## Observed verification result

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
