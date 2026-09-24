# D-023 — acquisition feasibility, not prospective evaluation

The user authorizes separating observed identity from Ranked evidence. D-008's
soloRanked-only expansion rule is superseded only for the new discovery strategy.
The existing `collect_tagged_frontier` strategy and its five-attempt limit remain
unchanged. `DiscoveryPlayer`/`DiscoveryObservation` are separate from its tables.
Shared `TrackedPlayer` cooldowns, claims, backoff and the advisory lock are reused.

An observed team-member tag in a retained official HTTP-200 battlelog is enough
for query eligibility, regardless of battle type or result availability. Admission
requires pinned raw content, official source/format/endpoint/reference, collector
lineage and matching fetch time. This verifies retained collector provenance,
not a cryptographic signature from Supercell. No names/IDs/missing tags are inferred.
Only directly supplied team tag fields are supported in this pilot; unsupported
structures are retained raw, not reconstructed. Ranking provenance remains in the
original tables, linked through the same TrackedPlayer where applicable.

Discovery observations retain exact raw JSON pointer, raw capture time, original
collector via RawPayload, admission run, queried parent, literal battle type and
self/teammate/opponent relationship where unambiguous. A missing queried identity
or ambiguous team leaves relationship UNKNOWN. Raw soloRanked identity discovery
is distinct from `source=solo_ranked` observations linked to an eligible imported
match. Evidence counts recheck current match eligibility, excluding conflicts.
Trophy/friendly/unknown-type matches never supply Ranked evidence. Query-envelope
identity alone never creates a discovery member.

## Preregistered single pilot

`DISCOVERY_PILOT_PROTOCOL.json` is committed before execution. Its byte SHA-256
is passed separately to the command; CollectorRun retains it and the code revision.
The protocol pins the three run-6 battlelogs (929–931), not archived historical
holdout payloads. Tag-only discovery scans those newly captured responses; it
neither selects historical Match rows nor imports their older entries. Their
original response bodies and timestamps remain unchanged.

- No ranking, catalog, profile or other HTTP requests.
- At most ten battlelog HTTP attempts, including retries; at most one new request
  hop. Persist newly observed boundary tags without querying deeper hops.
- Existing six-hour minimum player cooldown, error/404 pauses, Retry-After,
  request pacing and shared advisory lock. No forced clock or recurring process.
- Bootstrap all valid observed team tags from the three pinned responses before
  requests. They are depth-zero request roots for this pilot. Stored graph edges
  still point to the original queried parent.
- Deterministic selection: due/active players only; null/old last-fetch first,
  discovery first-seen timestamp, then tag. This is a biased graph sample; neither
  random sampling nor independence nor sampling weights are claimed.
- Persist every new raw response before parsing; import only after the unchanged
  exclusive 2026-09-18T15:04:42Z cutoff. Historical tolerance collisions stay raw-only.
- A persisted pilot ID is single-use under the shared lock, including crashes or
  failed attempts. Do not immediately retry zero-yield or partial runs.
- Report HTTP/status/retries, raw battle types, available/due query tags, distinct
  bootstrap and response tags, new eligible soloRanked, duplicates/conflicts, and
  separate discovery and eligible Ranked-evidence frontier sizes.

All observations are pre-registration development/acquisition observations,
excluded from automatic training and future test membership. The distinct
`observed_discovery_pilot_v1` provenance is rejected by both prospective sealing
and verification even when another accepted origin is present. A future start
must follow both pilot completion and prospective registration.

If there is genuine new eligible soloRanked evidence, assess acquisition feasibility
without treating one observation as proof of adequate throughput or representative
sampling. Freeze a prospective policy and exact common-context/patch exclusions
before any registration. If there is none, audit literal raw types and parser
exclusions; do not infer that these players never play Ranked or that the API
universally lacks Ranked. Record DATA_UNAVAILABLE if the cause remains unresolved.

D-022 artifact and V2 bytes have passed integrity checks and are not rebuilt.
Acquisition model/module additions change some source files in the broader D-022
source manifest; future exact Legacy replay must use its archived/pinned source
checkout as already required by LEGACY_BUNDLE_RUNBOOK.md. No scorer, provider,
aggregate, prior or default-engine behavior is changed.

Validation before execution: 50 combined collector/discovery/growth/future-window
tests passed (6.084 s); final 11 discovery tests including command hash and
historical-cutoff guards passed (1.948 s). No API call during tests.

## Observed result

D-023 pilot completed (run 7, 2026-09-24T16:22:13Z–16:24:00Z): acquisition feasibility demonstrated. Ten battlelog HTTP 200, zero retries/ranking requests. 340 authentic observed query roots; 250 raw entries: 201 trophy ranked, 33 soloRanked, 16 type UNKNOWN. Parser retained all 33 soloRanked; 60 unsupported/non-3v3 entries skipped, zero parser errors or future-dated records. 185 newly imported matches: 152 trophy and 33 eligible soloRanked; five trophy duplicates, zero conflicts. 1,031 additional query tags; discovery frontier 1,371, eligible Ranked-evidence frontier 56. Independent raw/parser/import audit agrees. Pilot matches remain permanently excluded from future test membership and automatic training.

The independent read-only reproducer is `discovery_pilot_audit.py`; complete
counts, run/protocol/code identity and raw hashes are in DISCOVERY_PILOT_RESULT.json.
All ten original raw responses remain private in the isolated database. No
player tags are published in the report. The 16 UNKNOWN types were literal missing
`type` fields in lastStand responses, not reinterpreted as Ranked.

The pilot disproves an API-wide lack of useful soloRanked for this path: authentic
trophy-discovered tags led to 33 eligible observations without changing the parser.
It does not prove the original seeds never play Ranked; their finite observed
logs were trophy-only. Population coverage and sustainable throughput remain
unknown. Proceed to prospective registration prerequisites; do not repeat pilot.
