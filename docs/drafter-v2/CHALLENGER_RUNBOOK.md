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
