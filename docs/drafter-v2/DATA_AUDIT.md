# Drafter V2 Data Audit

Status: Phase 0 complete; the isolated database is fresh and contains no historical
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
Not yet measured. Each field will be classified `observed`, `confirmed_available`, `not_observed`, or `unknown`; absence in one fixture will not be treated as proof of global absence.

## Safety
No collector, official API request, RawPayload import, aggregation, reset, delete,
or production DB access was run in Phase 0. The test database was created by Django
inside the isolated Compose project and destroyed after the test run.
