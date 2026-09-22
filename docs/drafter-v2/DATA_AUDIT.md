# Drafter V2 Data Audit

Status: Phase 1 prerequisite audit complete; the isolated database is fresh and contains no historical
production data. The repository baseline ran successfully: 680 Drafter tests,
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

Sampling and deduplication are implemented in the report: sampling is read from
RawPayload provenance, reconstructed-fingerprint duplicates are counted without
deleting or merging anything, and conflict matches are reported separately.

## Safety
No collector, official API request, RawPayload import, aggregation, reset, delete,
or production DB access was run in Phase 0. The test database was created by Django
inside the isolated Compose project and destroyed after the test run.

The host had no `BRAWL_STARS_API_KEY` and the feature worktree had no `.env`, so
no official API request was attempted. The live `.env`, database and rawpayload
directories were not opened or mounted. A future historical-data audit requires
a separately authorized read-only export/snapshot into a new isolated location;
direct access to `/media/docker/alex-django/data/db` is intentionally not used.
