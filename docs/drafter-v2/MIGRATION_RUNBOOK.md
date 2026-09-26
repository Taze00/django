# Drafter V2 private development migration

Migration freeze: no collection, fitting, promotion, historical holdout analysis,
or new final-test registration. Keep the source host intact until the owner
confirms target acceptance. Source state is branch `feature/drafter-v2`, commit
`9be54cc3b4d0f1c034d7890fa324e0418214e9ab`; migration-only tools/config/docs are
added on that branch. The private package's `CODE_REVISION` pins the exact restore
revision, including these tools. The later STATUS documentation commit may be
newer; do not substitute an unpinned branch tip during acceptance.

## Scope and source identity

Repository: `git@github.com:Taze00/django.git` (remote `alex`). Keep the whole
repository structure. Shared dependencies include `manage.py`, `meinprojekt/`
(settings/WSGI/imports), `fitness/` and `films/` code/migrations imported by Django,
`templates/`, `static/drafter/`, `docker/` and dependency files. Retaining tracked
code is not permission to migrate personal media, databases or unrelated data.
No standalone Drafter extraction is attempted.

Source PostgreSQL: container `drafter-v2-isolated-db-1`, database/user `postgres`,
PostgreSQL **16.0**, mount exactly
`/home/alex/alex-django-drafter-v2/data/db:/var/lib/postgresql/data`.
The live `alex-django-db-1` and `/media/docker/alex-django` were not queried or
mounted. There is no source collector running. Database counts are in the private
`source-audit.json`; they are exact counts, not resettable pg_stat estimates.

No auth users, sessions, token records, Films rows or personal Fitness rows were
found. Three Fitness exercise and 21 progression rows exist; all Fitness/Films
and other non-Drafter application row data are excluded regardless of origin.
Their empty schemas, Django migration history, content types and permissions are
kept so this repository can load. These excluded seed rows are NOT a parity
failure: compare `expected_restored_table_counts`, not the unfiltered source
counts. No globals/passwords/roles are dumped. No source rows are deleted.

All Drafter tables, sequences, constraints, catalog/provider statistics, raw
payloads, Match/MatchPlayer relations, collector reports, both frontier types,
Praxisfall/shadow state and preference tables are preserved. Sealed historical
rows are copied opaquely as part of the authorized backup; never inspect their
membership/outcomes or evaluate them. Do not aggregate, bootstrap, seed or
recompute data during migration.

## Package and secrets

Private staging/package: `backups/drafter-v2-migration-20260926/` (Git ignored).
The compressed `.tar.gz` alongside it is the transfer unit. Transfer its external
`.sha256` too. Contents:

- `database.dump`: portable custom-format `pg_dump`, read-only source; no PGDATA copy.
- `database.toc`: inspected `pg_restore --list` inventory.
- `artifacts/data/brawl_reports/`: allowlisted non-secret private models,
  candidate, historical experiment, frozen Legacy inputs/primary bundle/replay,
  and all seven development snapshots.
- `artifact-inventory.json`: every source artifact's path, bytes, SHA-256,
  required/optional status, purpose, included flag. Two redundant identical
  D-022 rebuild copies are inventoried but omitted; the primary archive is kept.
  The older Legacy input is optional historical material and is included.
- `source-audit.json` and post-dump `source-audit-recheck.json`: exact counts,
  critical frontier/catalog/migration hashes, checkpoint verification, draft
  smoke outputs, and read-only readiness. No model-quality metrics are computed.
- `manifest.json`, `SHA256SUMS`, `CODE_REVISION`, `storage.json`, this runbook and
  `verify_package.py`.

This is private player-tag-bearing data even though it contains no credentials.
Do not upload it to Git or a public link. It excludes unrelated media/uploads,
raw PGDATA, caches, node_modules, virtualenvs, `/tmp` logs and Docker image layers.
Durable Git reports and database CollectorRun records replace temporary logs.
Raw API payloads are database rows; no external raw-file directory exists here.

Secret names only:

- `BRAWL_STARS_API_KEY`: source file `/home/alex/.drafter-v2-api.env`, mode 0600.
  Copy this file **manually**, separately over SSH to the new Mac's
  `$HOME/.drafter-v2-api.env`; set mode 0600. Never display it, package it, or add
  it to Git. New outbound IP authorization may require a separately issued API
  key; do not probe the API during acceptance.
- `DJANGO_SECRET_KEY`: create a new local key on the new host. No user/session
  data or pending signed shadow tokens exist in this source DB (Praxisfall=0).
- `DJANGO_REGISTRATION_KEY`: disabled in the isolated preview. No production key
  is needed. `POSTGRES_PASSWORD` is the documented local-only container password,
  not a production credential. `TMDB_API_KEY` is unnecessary and remains empty.

Do not source the API credential during any verification or preview command.
It is only for later explicitly resumed bounded development collection.

## New Mac: clone and verify transfer

Install Git, Python 3 and Docker Desktop matching the Mac's Intel/Apple Silicon
architecture. Start Docker and check `docker info`. The standalone Compose file
uses PostgreSQL 16.0 and Python 3.11.14 with dependency versions captured from the
source image; Docker selects the architecture. No old image layers are copied.

Official references: [Docker Mac installation](https://docs.docker.com/desktop/setup/install/mac-install/),
[PostgreSQL 16 portable custom dumps](https://www.postgresql.org/docs/16/app-pgdump.html),
[pg_restore](https://www.postgresql.org/docs/16/app-pgrestore.html).

The following commands are **on the new Mac only**. Set `BUNDLE` to the absolute
path of the extracted private package. Do not overwrite an existing checkout or package.

```bash
# First verify the transferred archive with its separate .sha256 file:
shasum -a 256 -c drafter-v2-migration-20260926.tar.gz.sha256
mkdir -m 700 drafter-transfer
tar -xzf drafter-v2-migration-20260926.tar.gz -C drafter-transfer
BUNDLE="$PWD/drafter-transfer/drafter-v2-migration-20260926"
(cd "$BUNDLE" && shasum -a 256 -c SHA256SUMS)
python3 "$BUNDLE/verify_package.py" "$BUNDLE"
git clone --branch feature/drafter-v2 git@github.com:Taze00/django.git drafter-v2
cd drafter-v2
git checkout --detach "$(cat "$BUNDLE/CODE_REVISION")"
python3 "$BUNDLE/verify_package.py" "$BUNDLE" --install-artifacts "$PWD"
```

Artifact installation is exclusive/idempotent: existing different artifacts fail
closed instead of being overwritten. Do not copy a source `.env` or `data/db`.
Create a local key without printing it (only in the fresh clone):

```bash
python3 - <<'PY'
import os,secrets
from pathlib import Path
os.umask(0o077)
p=Path('.env')
with p.open('x') as f:f.write('DJANGO_SECRET_KEY='+secrets.token_urlsafe(48)+'\n')
PY
unset BRAWL_STARS_API_KEY
# Always use this standalone file, NEVER merge in docker-compose.yml.
dc() { docker compose -p drafter-v2-migrated -f compose.drafter-v2-migration.yml "$@"; }
dc config --quiet
dc build app
dc up -d db
dc ps
```

The new DB has its own project-scoped Docker named volume, no host PGDATA bind,
no published DB port, no external/proxy network, no Traefik labels, no restart
policy. Inspect mounts/networks (`docker inspect "$(dc ps -q db)"`) before restore;
only the new `drafter-v2-migrated` volume may be present. Neither production nor
source mounts are acceptable. On startup, `dc exec -T db pg_isready -U postgres`
must succeed. If an old volume exists, STOP; do not delete/reset it.

```bash
# This gate must print 0; otherwise stop without restoring.
dc exec -T db psql -X -U postgres -d postgres -Atc \
  "SELECT count(*) FROM pg_tables WHERE schemaname='public';"
# Only after the zero-table gate, restore into this NEW isolated DB:
dc exec -T db pg_restore --exit-on-error --single-transaction \
  --no-owner --no-privileges -U postgres -d postgres < "$BUNDLE/database.dump"
```

No `--clean`, drop/reset, ownership changes or raw-directory copy is required.
A failed restore stays visible; diagnose it, do not erase an existing database.

## Read-only acceptance BEFORE preview or collection

```bash
dc run --rm --no-deps -e 'PGOPTIONS=-c default_transaction_read_only=on' app \
  python manage.py check
dc run --rm --no-deps -e 'PGOPTIONS=-c default_transaction_read_only=on' app \
  python manage.py migrate --check
dc run --rm --no-deps -e 'PGOPTIONS=-c default_transaction_read_only=on' app \
  python manage.py migrate --plan
```

There must be **no pending migrations** at the pinned revision. These commands
check history without applying data migrations. Do not run an unreviewed bare
`migrate`, `seed`, `aggregate`, refresh or bootstrap command to fix a mismatch.
Create a new private output directory for target acceptance (not in the bundle):

```bash
mkdir -m 700 backups/target-migration-verification
dc run --rm --no-deps \
  --volume "$BUNDLE:/handoff:ro" \
  --volume "$PWD/backups/target-migration-verification:/verification" \
  -e 'PGOPTIONS=-c default_transaction_read_only=on' \
  -e DRAFTER_MIGRATION_EXPECTED=/handoff/source-audit.json \
  -e DRAFTER_MIGRATION_OUTPUT=/verification/target-audit.json app \
  python manage.py shell -c "exec(open('tools/drafter_migration/audit.py').read())"
```

PASS requires exact restored counts, critical table hashes (including cooldowns,
provenance, both frontiers, catalog and migration history), 22,321 checkpoint
members with content/origin hashes, 6,094 pinned Train examples, active V2 and
frozen candidate/D-022 byte hashes, and fixed Hideout Last/Mid/First smoke outputs.
Only elapsed timing is omitted; floats are normalized to 12 decimals to allow
architecture-level rounding, while ranking/order and other fields stay exact.
Smoke contexts are diagnostic parity fixtures, never ranking targets.
Readiness reports due-target counts/backoff using actual target time; these counts
may advance naturally, but persisted frontier state hashes must not change.
It verifies no running CollectorRun and makes **zero API requests**. Also inspect
`dc ps` and host processes for a collector; do not start one during migration.

Focused and full regressions use Django's separate disposable `test_postgres`,
never the imported development database. They create synthetic test data only:

```bash
dc run --rm --no-deps app python -m unittest tools.drafter_migration.test_package
dc run --rm --no-deps -e DJANGO_SETTINGS_MODULE=meinprojekt.settings app \
  python manage.py test drafter.tests.test_v2_challenger \
  drafter.tests.test_v2_legacy_comparison drafter.tests.test_v2_planning \
  drafter.tests.test_v2_shadow drafter.tests.test_development_collection \
  drafter.tests.test_development_experiment drafter.tests.test_development_forward --noinput
dc run --rm --no-deps -e DJANGO_SETTINGS_MODULE=meinprojekt.settings app \
  python manage.py test --noinput
```

Do not alter unrelated apps to make tests pass. Record failures precisely. Re-run
the acceptance audit to a **new** target output filename after tests to confirm
imported state is unchanged. Target verification and full regressions are not
claimed to have run on the old host; that would write new test databases there.

## Loopback preview and SSH access

```bash
dc up -d app
# On the new Mac:
open http://127.0.0.1:8000/draft/challenger/
```

The container listens internally on 8000; the host publishes **127.0.0.1 only**.
The migration preview URL config exposes only `/draft/`; the repository remains
intact and production settings are unchanged. The default draft engine remains
Legacy; Challenger is experimental. Anonymous smoke requests must not enable
shadow capture. No collector service is defined or started.

From another computer, use SSH to the Mac (Remote Login enabled for an authorized
account), not a router/public port mapping:

```bash
ssh -N -L 127.0.0.1:18000:127.0.0.1:8000 MAC_USER@MAC_LAN_OR_PRIVATE_SSH_HOST
# Open locally on that other computer:
# http://127.0.0.1:18000/draft/challenger/
```

Never publish 8000 on `0.0.0.0`, add a public reverse proxy, or open internet
firewall/router ports for this preview. Transfer the credential manually with
SSH/SCP and mode 0600; verify names/permissions without displaying values.

## Handoff and later continuation

Target acceptance remains PENDING until the owner confirms the new Mac works,
all checks pass, and the private target receipt is retained. Keep the entire
source environment untouched until then. No destructive cleanup is authorized.
After successful migration, explicitly resume documented bounded collection from
the restored discovery frontier; never reset timers or re-query to repair data.
The September-25 slice is frozen, no candidate promotion is authorized, and the
fixed forward-development confirmation may only run after September 28 UTC.
No collection or fitting is part of migration verification.
