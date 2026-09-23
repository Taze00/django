# Experimental Challenger

Open `/draft/challenger/` on an instance running this branch. “V2 Labor” is a
separate navigation entry; `/draft/` and its API keep Legacy. Select map, two
own picks, three opponent picks and optional bans. Results show model probability,
model identity, training provenance, actual logit contributions and UNKNOWN
uncertainty. This is not a production promotion or evidence of better decisions.

Default model file: `data/brawl_reports/v2_challenger.json`, intentionally ignored
by Git. Override with Django setting `DRAFTER_V2_MODEL_PATH`. No user-supplied path
is accepted. Missing/corrupt/model-catalog-mismatch returns 503, never a silent
fallback. Stop serving the experiment by removing its configured model path;
Legacy is unaffected. Live checkout/services have not been changed.

Recovery on the **isolated** database only (same Compose safety checks and test-only
environment as COLLECTION_RUNBOOK):

```
python manage.py drafter_v2_challenger_train \
  --output data/brawl_reports/v2_challenger.json --revision <source-commit>
```

Destination must not exist. The command verifies the known freeze membership,
reads only development outcomes/features, uses a read-only repeatable PostgreSQL
transaction, and writes a separate artifact. Do not run the old `train`, `freeze`
or `evaluate` commands on the historical DB. Preserve previous artifacts under
versioned names for rollback. No API credentials are needed.

The model is tied to this catalog's internal IDs plus slugs. Context maps retain
exact historical model strings from Train only. Missing contexts or conflicting
identities are errors; never silently substitute IDs from a different database.
The artifact includes Train/Validation fingerprints and no player identifiers;
only aggregate reports/digests enter Git. The initial report's revision names the
base commit; its D-012 implementation is committed alongside the report.

Validation: `manage.py test drafter.tests.test_v2_challenger
 drafter.tests.test_v2_model drafter.tests.test_v2_search drafter.tests.test_api --noinput`.
The endpoint/page smoke used real isolated catalog/model with a constructed draft;
it is functional evidence, not an outcome evaluation or gameplay ground truth.

## First and Mid Pick

The same page now supports open slots. For First Pick leave both teams empty and
check own First Pick. For Mid Pick enter the actual picks and first-pick side;
our team must be next in the 1-2-2-1 order. Last Pick stays 2 own / 3 enemy with own
First Pick unchecked. Duplicate/unavailable picks and bans fail validation.

All supported legal root choices are evaluated. Following moves use a width-three
shortlist ordered by training appearance count. The displayed worst reply is only
within that shortlist; unsearched responses may be stronger. All model evaluations
are full 3v3 teams. Contributions for early picks refer to the displayed hypothetical
continuation. They are not unconditional claims about the current incomplete team.

## Comparison and saved drafts

Check “Legacy daneben anzeigen” to compare rankings. Legacy numbers remain scores,
V2 numbers remain model estimates; their scales are not interchangeable. No ranking
agreement is described as accuracy. Logged-in users can expand a candidate and save
that decision. The actual server-signed response is stored, not a later re-run.
Tokens expire after two hours. Each snapshot accepts one chosen pick; repeats are
idempotent. “Meine gespeicherten Drafts” offers private replay and later outcome
entry. Outcomes are unverified self-reports, never automatically training data.

Deploying this branch's logging requires `manage.py migrate drafter` (0020 adds two
fields). Applied and tested only in isolation. Roll back code/model selection
without deleting snapshot columns/data. Do not reverse the migration to perform a
routine model rollback, since that would discard its new metadata.

## Isolated local preview

A preview was started on loopback only, with Traefik explicitly disabled. It uses
the isolated database and test-only Django configuration; it is not a live rollout.
After the usual isolation checks, start it if it is not already running:

```bash
DJANGO_SECRET_KEY=drafter-v2-isolated-test-only \
DJANGO_REGISTRATION_KEY=disabled \
docker compose -p drafter-v2-isolated run --rm --no-deps -d \
  --name drafter-v2-challenger-preview --label traefik.enable=false \
  -p 127.0.0.1:18080:8000 -e PYTHONDONTWRITEBYTECODE=1 \
  -e DJANGO_DEBUG=True -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
  --entrypoint python django-dev manage.py runserver 0.0.0.0:8000 --noreload
```

Open `http://127.0.0.1:18080/draft/challenger/`. For a remote host, forward that
loopback port through your existing SSH connection. This command neither creates
an account nor changes credentials. Use an existing isolated account for logging;
anonymous recommendation and comparison work without one. No live credentials.

Stop only this preview with `docker stop drafter-v2-challenger-preview`; its
`--rm` container disappears, while DB/model/snapshots remain. After code changes,
restart only this named preview. Nothing restarts the production Compose project.

Final safe development commands (inside the isolated one-off runtime):

```
python manage.py drafter_v2_challenger_train --output <new-artifact-path> --revision <commit>
python manage.py drafter_v2_challenger_experiment --output <new-experiment-path> --revision <commit>
python manage.py test drafter --noinput
python manage.py test fitness --noinput
```

The fixed experiment is already completed; commands document reproduction, not an
instruction to repeatedly select on Validation. Both membership and canonical
Train/Validation example digests are enforced. Byte `artifact_sha256` matches the
runtime identifier; `canonical_content_sha256` separately identifies JSON content.
