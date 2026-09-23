# Drafter V2 Data Audit

Status: Phase 1 prerequisite audit complete; the isolated database contains an
anonymized read-only snapshot from the live Drafter data, and contains no
unrelated Fitness, Films, user/account or other application data. The repository baseline ran successfully: 680 Drafter tests,
4 skipped, 0 failures, 237.054 seconds.

## Source boundaries
- Repository source code and anonymized fixtures are available locally.
- The feature worktree had no `data/` directory at initialization; the isolated
	test database now uses only `./data/db` in this worktree.
- The live checkout and its database/raw payloads are explicitly out of scope.

## Planned reproducible audit
Use a management command or read-only Django shell in the isolated Compose project to report counts and distributions for RawPayload, Match, MatchPlayer, Brawler, GameMode, BrawlMap, Patch, CounterStat and SynergyStat. Reports must include filters, patch window, source, `battle_type`, distinct fingerprints and sampling provenance.

## API capability matrix
The anonymized official battlelog fixture contains 25 entries, 17 two-team
matches and 8 Showdown entries. Four of the 17 team matches have
`battle.type == "soloRanked"`; this is the only type currently admitted by
`config.DRAFT_STATISTIK_BATTLE_TYPEN`.

| Capability | Fixture evidence | Classification | Use/limitation |
|---|---|---|---|
| Battle time | `battleTime` | observed | parsed to UTC timestamp |
| Map/mode | `event.id`, `event.map`, `event.mode`, `event.modeId`, `battle.mode` | observed | map/mode IDs and names available |
| Brawlers | team brawler `id`, `name` | observed | six players in team matches |
| Result | `battle.result` plus queried-player perspective | observed | side conversion required; no result without perspective |
| Duration | `battle.duration` | observed | optional |
| Player tags | team `tag` and envelope `referenz` | observed | raw tags anonymized in fixture; provenance-sensitive |
| Rank/trophy-like fields | `trophyChange`, brawler `trophies`, `battle.rank` in Showdown | observed | semantics differ by battle type; not a validated skill variable |
| Power | brawler `power` | observed | per-player value; no causal use established |
| Star player | `starPlayer` | observed | not used as team skill without validation |
| Pick order | no field observed | not_observed_in_fixture | remains UNKNOWN |
| Bans | no field observed | not_observed_in_fixture | remains UNKNOWN |
| Builds | no gadget/star power/gear/hypercharge fields observed | not_observed_in_fixture | remains UNKNOWN |
| Damage/healing/kills/deaths/objective stats | no fields observed | not_observed_in_fixture | remains UNKNOWN |
| Match/replay ID | no field observed | not_observed_in_fixture | dedup uses reconstructed fingerprint |
| Ranked Elo/skill | no validated field observed | unknown | must not be invented or proxied without validation |

Observed top-level item fields: `battle`, `battleTime`, `event`.
Observed battle fields: `duration`, `mode`, `players`, `rank`, `result`,
`starPlayer`, `teams`, `trophyChange`, `type`.
Observed event fields: `id`, `map`, `mode`, `modeId`.
Observed brawler fields: `id`, `name`, `power`, `trophies`.

The command `python manage.py drafter_v2_audit --format json` is the
reproducible database audit. In the isolated Phase-1 database it reported
zero raw payloads, zero matches, zero players, zero stats, zero maps, zero
modes and zero patches. This is an environment fact, not a claim about the
live checkout.

## Measured historical snapshot

Source was queried read-only through `alex-django-db-1`; destination was the
separate `drafter-v2-isolated-db-1` bind mount. Exported tables were only the
Drafter catalog, patches, matches, match players, match-payload links and
aggregated Brawler/Counter/Synergy statistics. Raw JSON was replaced with `{}`;
player tags and builds were blanked; collector, preference, Praxisfall and all
other application tables were excluded.

Snapshot counts: 108 Brawler, 15 modes, 97 maps, 2 patches, 18,222 matches,
111,868 match players, 10,191 `soloRanked` matches, 10,162 countable
`soloRanked` matches, 11,843 Brawler stats, 57,648 Counter stats and 48,555
Synergy stats. Reconstructed-fingerprint duplicates: 0; conflicts: 0.
The countable Ranked window is 2026-08-29 through 2026-09-18 UTC.

The isolated import had zero orphaned match-player, Brawler, map or payload-link
references. Snapshot staging was `/tmp/drafter-v2-snapshot-20260922`; it was not
copied into the worktree or the live checkout.

## Post-freeze bounded collector audit

Three isolated `CollectorRun` records were created under D-004. Run 1 queried
the ranking endpoint only. Run 2 queried five fresh ranking seeds and added 100
`ranked` trophy matches, all deduplicated with 25 duplicate observations. Run 3
queried five previously observed players with `soloRanked` provenance and added
zero matches; all 125 observations were already-known `ranked` entries. All API
responses were HTTP 200, with no retries or rate-limit headers.

The current isolated audit has 18,322 matches, 112,776 match players, 877
raw-payload metadata rows, 205 tracked players and 98 maps. The eligible
`soloRanked` population remains exactly 10,191 total / 10,162 countable, with
latest timestamp `2026-09-18T15:04:42Z`. The 100 new `ranked` rows are excluded
by `DRAFT_STATISTIK_BATTLE_TYPEN` and do not justify a new V2 freeze.

## Bounded official API audit

Five bounded GET targets returned HTTP 200: `/brawlers` (108 items),
`/events/rotation` (JSON array), `/rankings/global/players` (200 items), one
observed player's profile and that player's `/battlelog` (24 items, 8
`soloRanked`, 16 `ranked`). Only status and schema metadata were retained.
The live key was read only into process memory and was never printed, stored or
copied. Battlelog fields observed in this current audit were:

- Item: `battle`, `battleTime`, `event`
- Battle: `duration`, `mode`, `result`, `starPlayer`, `teams`, `trophyChange`, `type`
- Event: `id`, `map`, `mode`, `modeId`
- Team brawler: `id`, `name`, `power`, `trophies`
- Player profile: includes ranked rank/Elo fields, but no validated causal skill variable was assumed

Pick order, bans, builds, damage/healing/kills/deaths/objective statistics and a
match/replay ID were not observed in this audit and remain UNKNOWN.

Sampling and deduplication are implemented in the report: sampling is read from
RawPayload provenance, reconstructed-fingerprint duplicates are counted without
deleting or merging anything, and conflict matches are reported separately.

## Historical Phase-0 safety record
No collector, official API request, RawPayload import, aggregation, reset, delete,
or production DB access was run in Phase 0. The test database was created by Django
inside the isolated Compose project and destroyed after the test run.

At Phase 0, the host had no `BRAWL_STARS_API_KEY` and the feature worktree had no `.env`, so
no official API request was attempted. The live `.env`, database and rawpayload
directories were not opened or mounted. A future historical-data audit requires
a separately authorized read-only export/snapshot into a new isolated location;
direct access to `/media/docker/alex-django/data/db` is intentionally not used.


## Resume verification (2026-09-22)

The inherited, previously uncommitted collector account above was preserved.
A fresh `drafter_v2_audit --format json` against the isolated database confirms
its inventory: 18,322 matches, 112,776 player rows, 877 payload rows, 205
tracked players, three collector runs, 98 maps, 10,191 soloRanked matches and
10,162 countable soloRanked matches. Conflicts and duplicate reconstructed
fingerprints remain zero. Report: `/tmp/drafter-v2-resume-audit.json`.

The database container `drafter-v2-isolated-db-1` mounts only
`/home/alex/alex-django-drafter-v2/data/db` and belongs only to network
`drafter-v2-isolated_backend`. The worktree data directory is not a symlink
or separate live-data mount. No live database query, credential read, API call,
collector run, reaggregation or holdout evaluation was performed during this
resume. Inventory uses PostgreSQL `default_transaction_read_only=on`.

The host API credential is absent and the isolated worktree has no `.env`.
The earlier agent's credential access is historical, not authorization to
read the live checkout now. Follow `COLLECTION_RUNBOOK.md` for isolated
credential injection and bounded collection once available.


`drafter_v2_growth --after 2026-09-18T15:04:42Z --format json` additionally
confirms zero newer API soloRanked rows, hence zero new eligible examples.
There are 76 API matches played after that boundary: 75 trophy `ranked` and
one `friendly`. These are temporal counts, distinct from the 100 rows imported
by collector run 2 (which also included older matches). The latest API Ranked
timestamp remains `2026-09-18T15:04:42Z`.

Collector record verification: runs 1/2/3 made 1/5/5 requests, all HTTP 200,
with zero retries; queried 0/5/5 players; imported 0/100/0 matches and reported
0/25/125 duplicates. All 100 imported rows and all 150 duplicate observations
in runs 2/3 are trophy `ranked`. Source: allow-listed collector summary in
`/tmp/drafter-v2-resume-growth.json`. No payload bodies or player identifiers
are printed. This is inventory verification, not another holdout evaluation.


## Credential-resume preflight (2026-09-22T18:08:52.563568+00:00)

The user reported that an isolated host API credential was now available.
Presence-only checks in login, non-login and escalated host command
processes all returned false; the final recheck also returned false.
No token value was printed or fetched from another source. The runbook
credential guard therefore prevented collection: no new CollectorRun,
API call, import or authentication failure occurred.

The isolated database mount and network were reverified. Both read-only
audits completed, reporting the same 18,322 matches, 10,191 Ranked /
10,162 countable Ranked, 877 payload rows and three collector runs.
Conflicts and duplicate reconstructed fingerprints remain zero.
Growth remains DATA_UNAVAILABLE: zero eligible API soloRanked matches
after 2026-09-18T15:04:42Z; the 76 newer API matches are 75 trophy
ranked and one friendly. This is not the result of a new collector run.

Reports: `/tmp/drafter-v2-credential-resume-audit.json` and
`/tmp/drafter-v2-credential-resume-growth.json`. Reproduce with the
unchanged read-only commands in COLLECTION_RUNBOOK.md. No model command,
sealed evaluation, live data access or production change was performed.


## Completed bounded run 4 and selection diagnosis

Source revision: `cd6481e`; run ID 4 started at
`2026-09-22T18:13:43.707390Z`. This completed run preceded the architecture
clarification on 2026-09-23; it is not being repeated.
The user-supplied isolated credential file was verified as mode 600 and loaded
only into the collection process. Presence check passed. No credential value
was displayed, copied or committed. Because no HTTP request occurred, remote
credential validity was not tested by this run.

Parameters: `broad_high_rank`, max five battlelogs, max depth 1, six-hour
refresh spacing, ranking/catalog startup fetches disabled, no optional raw
files. Result: finished, zero players queried, zero battlelogs, zero requests,
zero retries, zero new/duplicate/conflicting matches. No response means no
new HTTP status or rate-limit information, not an HTTP success assertion.
Only the new CollectorRun record was added; no payload or match was imported.

Post-run read-only inventory: four runs; otherwise unchanged at 18,322
matches, 112,776 player rows, 877 payloads, 205 tracked players and 98 maps.
Ranked remains 10,191 total / 10,162 countable. Conflicts and reconstructed
fingerprint duplicates remain zero.
Growth remains DATA_UNAVAILABLE: zero API soloRanked observations strictly
after `2026-09-18T15:04:42Z`. The 76 newer API matches are still 75 trophy
`ranked` plus one `friendly`; no new model evidence was obtained.

Read-only queue diagnosis at `2026-09-22T18:15:25.024440Z`: 61,146
soloRanked player rows, zero with nonblank tags, zero broad-qualified players.
205 tracked players were active at depth <=1 and 200 were due under the
six-hour/next-fetch gates, but zero due players met broad provenance criteria.
These are snapshot-time queue counts; due counts may change with time.
The anonymized snapshot deliberately blanked player tags. `HighRankStichprobe`
skips blank tags; `Collector._naechster` returns None when its broad list is
empty, without falling back to the trophy queue. Hence this is a missing
provenance blocker, not a cooldown, credential or deduplication failure.

Reproducer: `docs/drafter-v2/collection_queue_audit.py`, invoked through
`manage.py shell` with PostgreSQL `default_transaction_read_only=on` as shown
in COLLECTION_RUNBOOK.md. Reports from the completed run:
`/tmp/drafter-v2-bounded-audit.json`, `/tmp/drafter-v2-bounded-growth.json`,
`/tmp/drafter-v2-bounded-queue.json`. Aggregate counts only; no player identities.

Next valid input: independently sourced actual soloRanked payloads carrying
player tags and rank-field provenance, imported normally into isolation.
No invented ranks/tags, deanonymization, live-data lookup, forced cooldown
reset, strategy substitution, repeat empty broad run, aggregation or sealed
holdout evaluation was performed. Legacy remains unchanged.

The committed queue reproducer was executed under PostgreSQL read-only
protection on `2026-09-23T17:11:57.566647Z`: all 205 tracked players were
now due, yet tagged Ranked rows and broad-qualified candidates both remained
zero. This confirms that expiry of the refresh interval does not resolve
the missing-provenance prerequisite. Report: `/tmp/drafter-v2-queue-reproduced.json`.


## Tagged-frontier implementation milestone (2026-09-23, D-008)

Starting tree was clean at b818313. The isolated DB mount/network were reverified.
A new provenance-only frontier and bounded command are implemented and tested;
no real bootstrap request or import has occurred at this pre-experiment milestone.
Migration 0019 adds two tables without altering existing rows. Initial 74 and
expanded 138 focused regressions passed using synthetic disposable test data.
The real experiment will record its independent official ranking response, exact
raw/run/JSON-pointer seed evidence and observed graph edges separately below.
Historical missing tags remain missing; no new data or model result is claimed yet.
Additional importer/robustness regressions: 38 passed (5.123 s). Final frontier
suite: 24 passed (2.835 s), including the case of a newer timestamp colliding
with a frozen row under fingerprint rules: raw retained, frozen labels/links/tags
unchanged. Migration drift check passed; plan shows only the two new tables.
