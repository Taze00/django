# D-026 — resumable Ranked development acquisition

D-025 aborts the previous prospective test before evaluation. Its immutable
registration, raw payloads and original run reports remain historical evidence.
Pilot and aborted-window observations are now DEVELOPMENT, permanently excluded
from any later final test. No final test is registered by this work.

## Collector policy ranked_development_v1

Finite, explicit cycles: default four cycles, each at most 50 battlelog HTTP
attempts including retries. CLI permits 1–20 cycles, never more than 50 attempts
per cycle. There is no daemon/cron. Continue with another bounded invocation only
when the existing client's actual status and available due frontier permit it.
50k–100k is a long-term data target, not an assumed throughput or API quota.

Use only persistent DiscoveryPlayer identities with original official raw/pointer
provenance. No leaderboard/catalog/profile requests and no fabricated tags.
Ranked-activity priority uses directly observed soloRanked tag occurrences (not
winning, predicted quality or an invented skill label). Every fifth query prefers
a due broader discovery candidate; otherwise due Ranked-active candidates lead.
Remaining order: oldest/null last fetch, first seen, tag. This is intentionally
biased graph sampling with repeated players; no independent-sample claim or
invented sampling weights. Cycle request depth remains at most one; boundary
identities persist for later cycles.

Shared TrackedPlayer six-hour cooldowns, claims, 404 pauses, error backoff,
Retry-After, client pacing and advisory lock remain in force. The abandoned
prospective protocol's global six-hour *run* gate does not govern the newly
authorized development cycles; per-player cooldowns are never reset. Any observed
429, even followed by a successful retry, stops further queries in that cycle
and persists a global six-hour development pause. Credential errors and client
abort conditions also stop automatic continuation. Unknown quota stays UNKNOWN.

Raw response persists in its own transaction before parsing. Processing a response
uses one transaction for imports/discovery edges, reducing per-edge synchronous
commits without sacrificing raw retention. Per-response request/progress counters
are durable in CollectorRun. Interrupted cycles are retained as aborted, and new
cycles recover previously unparsed development raw without HTTP refetch, changed
fetch timestamps or player cooldown manipulation. Original raw run provenance
survives recovery; the new recovery/admission run remains separately visible.
Conflicts stop automatic continuation for inspection. No deleting/resetting data.

Trophy/friendly/other entries support discovery ONLY: new development cycles do
not import them as Match rows. Existing historic trophy rows remain preserved.
Only soloRanked records after max(old closed cutoff, current clock minus 30 days)
are import candidates. Strict dataset membership additionally requires official
provenance, known nonconflicting result, known map/mode, complete six distinct
known Brawlers and played-at no later than the observed fetch/current clock.
Actual game patch remains UNKNOWN; imported patch labels are reported separately.

Each cycle records requests/status/retries/429, queried players, raw battle types,
new tags, new eligible soloRanked, duplicates/conflicts, yield per HTTP attempt,
query/evidence frontier sizes and recovery counts. Raw IDs/hashes remain in the
isolated database. Repeated bounded cycles stop on API/error/backoff, conflicts,
no due players or explicit invocation bounds; normal bounds are checkpoints for
the autonomous agent to audit and continue, not a scientific stopping criterion.

## Versioned development datasets and validation gates

`drafter_development_dataset --output NEW_PRIVATE_PATH` creates a new immutable
manifest with verified original Train membership/content (6,094 examples) and
strict current new development membership/provenance/content hashes. It queries
original Train by already pinned fingerprints, never recovers or scans the old
holdout split. Original historical Validation is not imported into this dataset.
Pilot/aborted-window/development origins are allowed; any protected future final
origin fails closed. Trophy/unknown/incomplete/conflicting data cannot be examples.
No command automatically trains or replaces the working Challenger.

Checkpoints: 1k, 5k, 10k, 25k, 50k new eligible Ranked; each includes integrity,
duplicate/sampling audit and map/mode/time/import-patch coverage. Preserve every
snapshot, not just the latest count. As data grows use newer immutable snapshots
and forward validation rather than reusing the same newest slice indefinitely.

First development experiment gate (operational minimum, not power guarantee):
at least 1,000 new eligible matches, at least 500 on earlier UTC days for Train,
and at least 200 on the latest observed UTC day for Validation. Original pinned
Train joins only the older side. Whole UTC days/timestamp ties stay together;
no random mixing. Candidate grid and comparison criteria must be preregistered
before fitting/reading validation quality. Report development LogLoss, Brier,
calibration, coverage and latency; never call them final independent results.
Keep the prior negative opponent experiment. Mechanics remain evidence-gated.

## Isolated commands

Use the established isolated Compose project/credential pattern. Never live data.

```
python manage.py collect_development_frontier --cycles 4 --max-battlelogs 50 --code-revision COMMIT
python manage.py drafter_development_dataset --output data/brawl_reports/NEW_PRIVATE_MANIFEST.json
```

Dataset command runs read-only DB transactions; output is an additive private file.
Keep Legacy default and the existing V2 artifact/UI/shadow logging unchanged while
collecting. A later genuinely final independent window must begin only after all
development choices and model/input/code freezes; do not register one now.

Validation: 43 combined collector tests passed (6.222 s), 20 additional lifecycle/
dataset safety tests passed (3.641 s), final eight development/recovery tests
passed (2.056 s). Recovery also restores eligible Ranked-evidence edges without
changing raw fetch or player clocks. `--recover-only` performs this local replay
without HTTP and is available during an API pause.
