# Isolated collection and post-freeze audit

Legacy remains default. The historical holdout and shared-subset comparison
are final. These commands do not train a model or reopen that comparison.

## Isolation prerequisite

Use only `/home/alex/alex-django-drafter-v2`, branch `feature/drafter-v2`.
Do not start/restart the website, use the live checkout, read its `.env`, or
connect to its database. Do not use `docker compose config` without redaction:
it can print resolved credentials.

```bash
cd /home/alex/alex-django-drafter-v2
git branch --show-current
git status --short
realpath data
stat -c '%F %n' data
docker inspect drafter-v2-isolated-db-1 --format '{{json .Mounts}} {{json .NetworkSettings.Networks}}'
```

Require the database mount source to be this worktree's `data/db` and its
network to be `drafter-v2-isolated_backend`. The database is already running;
no live service operation is needed. Use a one-off container with `--no-deps`.
The following non-production Django values avoid needing production secrets:

```bash
export DJANGO_SECRET_KEY=drafter-v2-isolated-test-only
export DJANGO_REGISTRATION_KEY=disabled
```

## Read-only audits, no API credential needed

```bash
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e 'PGOPTIONS=-c default_transaction_read_only=on' \
  --entrypoint python django-dev manage.py drafter_v2_audit --format json

docker compose -p drafter-v2-isolated run --rm --no-deps -T \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e 'PGOPTIONS=-c default_transaction_read_only=on' \
  --entrypoint python django-dev manage.py drafter_v2_growth \
  --after 2026-09-18T15:04:42Z --format json
```

The cutoff is the last match timestamp of the sealed historical freeze, not
the latest collection timestamp. Do not move it to make the count positive.
Growth is API-only; imported fixtures require separate provenance review.
Missing winners/conflicts and incomplete or unknown-player teams are excluded.
Sampling counts can overlap across strategies; absent provenance is UNKNOWN.
No skill, mechanics, draft order or match builds are inferred.
The shared settings print `/code` before command output; a saved JSON report
must be read from the first `{`, without changing those protected settings.

## Read-only queue provenance preflight

Before another broad run, check whether its required Ranked provenance exists:

```bash
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e 'PGOPTIONS=-c default_transaction_read_only=on' \
  --entrypoint python django-dev manage.py shell \
  < docs/drafter-v2/collection_queue_audit.py
```

This prints counts only. It uses `HighRankStichprobe.belegte_kandidaten()` and
mirrors the runbook's depth 1, six-hour refresh interval and `next_fetch_after`
constraints. It does not call `nachtragen()`, start a collector, reveal tags or
reinterpret the rank field as a validated skill measure.

Run 4 had zero candidates because all 61,146 historical soloRanked player rows
had blank tags. At the diagnosis time 200 tracked players were due, but none
had the tagged Ranked evidence required by `broad_high_rank`. The strategy
intentionally has no fallback to trophy-ranking seeds. Waiting for cooldowns
cannot restore missing provenance; do not keep repeating the same broad run.

A valid next input is an independently supplied observed soloRanked payload
with actual player tags and rank-field evidence. It must retain provenance,
be imported only into isolation through the normal deduplicating importer,
and pass the same rank/refresh checks. Do not reconstruct anonymized identities
or retrieve live data. A different bounded discovery/bootstrap strategy would
need an explicit revised collection plan, labeled sampling provenance and
its own budget; do not silently replace `broad_high_rank` with `standard`.

## Historical broad-only command (do not repeat without new qualifying provenance)

The user supplied `/home/alex/.drafter-v2-api.env` independently (mode 600).
Use that full absolute path. Load it only inside the collection subshell;
never display, copy, log or commit its contents, and never use the live `.env`.
API credential presence is not proof of server acceptance if no request occurs.

```bash
(
set +x
set -e
set -a
source /home/alex/.drafter-v2-api.env
set +a
test -n "${BRAWL_STARS_API_KEY:-}" || exit 1
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
  -e PYTHONDONTWRITEBYTECODE=1 \
  --entrypoint python django-dev manage.py collect_brawl_matches \
  --max-spieler 5 --max-tiefe 1 --abruf-abstand-stunden 6 \
  --strategie broad_high_rank --ohne-katalog --ohne-rangliste
)
```

If the presence check fails, stop before starting the collector. A variable
exported in another shell is not automatically inherited by an already
running command-execution process. Verify presence in the process that will
launch Compose, without printing the value. Record this as a credential
visibility blocker, not an API authentication failure or an empty collection.
The read-only audits can still run. Do not fall back to live credentials.

This uses the existing isolated catalog and player queue, preserving the
refresh interval; do not force timestamps backwards to repeat completed work.
Raw responses persist in isolated RawPayload rows; `--dateien` is unnecessary.
The collector does not aggregate. Stop if no useful new Ranked rows arrive;
record the report rather than repeatedly retrying the same population.

Budget: at most five player battlelogs. Catalog/ranking requests are disabled
here; the collector may perform one catalog refresh if an unknown ID is
encountered. The client allows up to four attempts per request, a 0.25-second
minimum spacing and bounded exponential backoff; 429 honors capped Retry-After.
These are client limits, not evidence of the provider's permitted hourly quota,
which remains UNKNOWN. Do not schedule recurring or larger runs implicitly.
401/403 terminate; exhausted 429 terminates; repeated transient failures stop
under existing collector rules. Keep already stored payloads after any failure.

After one bounded run, repeat the read-only audits. Record run IDs, request
counts, status counts, retries, new/duplicate match counts by battle type and
the exact new Ranked window. No aggregation or model training is needed.

## Regression and next experiment

Run tests sequentially, with the same isolated project and explicit test-only
environment. `python manage.py test drafter.tests.test_v2_growth
drafter.tests.test_collector drafter.tests.test_api_client --noinput` uses
the disposable `test_postgres` database; never reset the snapshot database.

If new observations become available, first preregister a new evaluation
protocol: source/patch eligibility, immutable fingerprints, temporal splits,
train-only Legacy/statistical inputs, validation selection and sealed future
test access. Do not reuse the old holdout or call the old evaluation commands
on an enlarged database as if that preserved the freeze. No automatic promotion.


## Authorized tagged frontier bootstrap (D-008)

**Completed as run 5 on 2026-09-23; the commands below document that experiment,
not unfinished work. Do not repeat automatically.** Results: three persisted
seeds, four HTTP 200 responses, 50 new trophy matches, zero eligible soloRanked
or discovered frontier tags. DATA_UNAVAILABLE; see STATUS and the committed
BOOTSTRAP_EXPERIMENT_2026-09-23.json. Future collection requires a documented
bounded plan and the existing cooldowns; the next independent task is Phase 5A.

This is the user's explicitly authorized replacement for the blocked Phase-12
bootstrap, with distinct sampling `tagged_frontier_v1`. It does not modify
`broad_high_rank` or adopt the 205 old queue entries without fresh source evidence.
Official `/rankings/global/players` is a trophy list, not a soloRanked leaderboard.
One response is preserved whole; admit at most the first three distinct valid
supplied tag strings in response order. Do not paginate or substitute another
source if tags are absent. Actual rank/trophies stay raw metadata; skill is UNKNOWN.

After tests and isolation checks above, apply only the reviewed additive migration:

```bash
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
  -e PYTHONDONTWRITEBYTECODE=1 --entrypoint python django-dev \
  manage.py migrate drafter --noinput
```

One experiment, with the independent credential loaded only in its subshell:

```bash
(
set +x
set -e
set -a
source /home/alex/.drafter-v2-api.env
set +a
test -n "${BRAWL_STARS_API_KEY:-}" || exit 1
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
  -e PYTHONDONTWRITEBYTECODE=1 --entrypoint python django-dev \
  manage.py collect_tagged_frontier \
  --after 2026-09-18T15:04:42Z --ranking-seeds 3 \
  --max-battlelogs 5 --max-depth 1 --code-revision "$(git rev-parse HEAD)"
)
```

Hard budget: one ranking HTTP attempt plus five battlelog HTTP attempts, **including
retries**, at most five distinct queried players. Existing 0.25-second minimum
spacing, exponential backoff and capped Retry-After remain active; attempts are
limited further to the remaining budget. No catalog/profile request or output raw
file, no aggregation. Provider hourly quota remains UNKNOWN. 401/403 or exhausted
429 stops; 404 pauses that tag seven days; transient errors pause at least six
hours, increasing to 48 hours; three consecutive player failures stop the run.
Successful payloads persist before parsing/import; unsupported bodies remain raw.

The persistent frontier is TaggedPlayer plus TrackedPlayer's unique tag and
last_fetched_at/next_fetch_after/is_active state. Every source observation links
its exact JSON pointer, RawPayload, run and query parent. `query` observations
refer to envelope `/referenz`, not an assertion that the response listed the tag.
First source is immutable; subsequent ranking and battlelog evidence coexist.
No historical tag backfill, even when a new payload duplicates a match.

Only records played strictly after the sealed cutoff enter MatchImporter; older
records stay in raw responses. A newer sighting that deduplicates to a row at/before
the cutoff also remains raw-only and cannot enrich that frozen row. Only known-result, conflict-free API soloRanked
complete known-Brawler 3v3 matches admit discovered tags. Trophy `ranked` remains
ineligible. Missing tag/name/id combinations are never reconstructed. No skill
threshold or arbitrary sampling correction is added. Existing catalog lookup and
match fingerprint rules remain unchanged; unknown Brawlers do not trigger HTTP.

Depth means new **request** hops in this run. Existing frontier and newly admitted
ranking seeds start at hop 0; newly discovered hop-1 players may use the remaining
budget. Further actual tags observed at the request boundary persist but are not
queried during this run. In later runs persisted players are roots, still subject
to cooldown. Cumulative discovery depth and every parent edge stay in provenance.
No recurring job or automatic second experiment is authorized by this command.

Revisiting is supported using `--ranking-seeds 0` (no ranking request), the same
five-attempt cap/cutoff and unchanged six-hour gates. Repeated seed sightings never
reset last_fetched_at or next_fetch_after. A durable claim before HTTP prevents
immediate re-fetch after process failure. Do not edit timestamps to force requests.
A database advisory lock rejects overlapping frontier runs; do not run the old
collector concurrently. On interruption inspect the last CollectorRun, raw payloads
and STATUS before resuming; retain failed/partial evidence. Recover parsing/import
from stored payloads rather than refetching solely to fix local code.

Immediately after the single experiment, run the read-only growth and inventory
commands above and this aggregate provenance audit (no credential needed):

```bash
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e 'PGOPTIONS=-c default_transaction_read_only=on' \
  --entrypoint python django-dev manage.py shell \
  < docs/drafter-v2/frontier_audit.py
```

Record code revision/run ID, UTC window, ranking response schema/counts, admitted
and due seeds, queried battlelogs, HTTP statuses/retries, unique discoveries,
new unique/eligible soloRanked matches, duplicates, resulting frontier, raw IDs
and hashes. Do not print player identities or credential values in reports.
If no eligible new Ranked rows arrive: DATA_UNAVAILABLE, no immediate rerun,
no expanded request/seed source, no new model freeze. If rankings cannot supply
usable tags: retain the response and stop before considering another source.

Regression command (disposable isolated test database, no credential loaded):
`manage.py test drafter.tests.test_tagged_frontier drafter.tests.test_collector
 drafter.tests.test_api_client drafter.tests.test_offizieller_battlelog
 drafter.tests.test_v2_growth drafter.tests.test_stichprobe --noinput`.


D-020 authorized revisit completed 2026-09-24 as run 6 (zero ranking seeds). Do not repeat it. Three HTTP 200, 50 new trophy matches, zero eligible soloRanked. Preserved raw hashes and exact run budget: FRONTIER_REVISIT_2026-09-24.json.
