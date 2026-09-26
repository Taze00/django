# Migration handoff — package ready, new Mac acceptance pending

Source state: `9be54cc3b4d0f1c034d7890fa324e0418214e9ab` on `feature/drafter-v2`.
Exact restore code/tools revision: `db6c2b7110d0f7f163f6d7f7f4ee2a2b97d45446`.
Later commits add handoff documentation only. Keep the whole repository; do not
extract the app. Follow [MIGRATION_RUNBOOK.md](MIGRATION_RUNBOOK.md), also inside
the archive. No source cleanup, collection or fitting is authorized by this handoff.

Private transfer files (Git ignored, mode 0600):

- `backups/drafter-v2-migration-20260926.tar.gz`
- `backups/drafter-v2-migration-20260926.tar.gz.sha256`

Archive SHA-256: `d4d8aac8caa85a9efa0e2c6f0eb2b2a456f95262993e9c1d78e44595b22cfd86`.
Uncompressed verified staging remains in `backups/drafter-v2-migration-20260926/`.
Do not transfer `/tmp`, raw `data/db`, Docker layers, caches or unrelated media.
The logical dump excludes all unrelated row data, including 24 Fitness seed rows;
empty shared schemas/framework migration metadata remain for repository compatibility.
Users, sessions, Films and personal Fitness rows were zero in the source audit.

## Measured storage

| Category | Bytes | MiB |
| --- | ---: | ---: |
| Tracked checkout (whole repository) | 19881427 | 18.96 |
| Shared Git object store (estimate; clone may differ) | 165883904 | 158.20 |
| Source PostgreSQL allocated; not copied as PGDATA | 403575267 | 384.88 |
| Portable logical database dump | 27046758 | 25.79 |
| Required private models/evaluation/checkpoint artifacts | 42314020 | 40.35 |
| Optional historical/redundant artifacts in source | 10683869 | 10.19 |
| Included private artifacts (required + historical input) | 43540141 | 41.52 |
| External raw files | 0 | 0.00 |
| Compressed transfer archive | 45248722 | 43.15 |

These categories overlap: do not add the archive to its uncompressed contents,
or source DB allocation to the dump. The shared Git object store includes other
refs and is not packaged; cloning the pinned branch may consume a different size.
The 1,226,121-byte historical Legacy input is included; two redundant identical
4,728,874-byte bundle copies are omitted and remain on the source. Required
artifacts total 40.35 MiB. All 16 source artifacts are individually inventoried in
[MIGRATION_ARTIFACT_INVENTORY.json](MIGRATION_ARTIFACT_INVENTORY.json), with purpose,
required/optional flag, inclusion, size and SHA-256. Fourteen are packaged.

The DB's largest component is discovery observation/provenance data and indexes
(183,001,088 bytes). RawPayload storage is 19,578,880 bytes inside PostgreSQL;
there are no external raw files here. The dump preserves all 2,897 RawPayload rows.
No temporary logs are required because durable CollectorRun records and Git audit
reports retain their evidence.

## Acceptance evidence and remaining work

Source and post-dump audit match: 42,481 Matches, 258,582 MatchPlayers, 48 collector
runs, 112,203 discovery players, 451,828 discovery observations, 112,305 tracked
players; all Drafter tables and their sequences are included. Praxisfall/shadow
and user preference rows are zero but their schemas/state are preserved. Last
persisted run 48 reports Ranked-evidence frontier 47,169 and 23,752 evidence
matches; the stricter development checkpoint contains 22,321 eligible matches.
These are different recorded definitions, not interchangeable sample counts.

Pinned Train (6,094), checkpoint membership/content/provenance, catalog/frontier/
cooldown/migration hashes, active V2/candidate/D-022 hashes and Last/Mid/First smoke
outputs are in the private audit. The dump TOC and full pg_restore stream passed;
no restore was performed on the source. Three packaging safety tests and 13
no-database planning/experiment/forward tests passed. Compose checks confirm
loopback-only publication, no database port, no public proxy/external network,
and a docker-only image build context. Base image manifests provide amd64 and
arm64 variants. See [MIGRATION_PACKAGE_RECEIPT.json](MIGRATION_PACKAGE_RECEIPT.json).

**Still required on the new Mac:** restore into a fresh isolated service, verify
all hashes/counts/smoke outputs, check migration history, run focused/full
regressions on disposable test DBs, open the loopback preview and verify readiness
without any API request. Only then can the owner confirm successful migration.
No cleanup of the old host is authorized before that confirmation.

Copy the API credential manually and separately, on the new Mac, without printing
its contents (replace SSH placeholders; do not run these in the old checkout):

```bash
umask 077
# Use a fresh destination; preserve an existing credential rather than overwrite it.
test ! -e "$HOME/.drafter-v2-api.env" && \
  scp -p OLD_USER@OLD_HOST:/home/alex/.drafter-v2-api.env "$HOME/.drafter-v2-api.env"
chmod 600 "$HOME/.drafter-v2-api.env"
```

Do not source it during acceptance. Required API secret name is
`BRAWL_STARS_API_KEY`; the runbook creates a new local `DJANGO_SECRET_KEY`, disables
registration, and requires no production or TMDB credentials. API IP authorization
on the new host remains unverified without a separately authorized API call.
