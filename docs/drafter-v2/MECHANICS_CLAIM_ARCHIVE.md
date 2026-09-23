# Reviewed annotation archive (D-011)

This offline utility preserves the four D-010 reviewed annotations and renders
conditional statements attributed to their archived source observation. It does
not assert present-day validity. No source fetch, database, Django configuration,
credential or scoring import is involved.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m drafter.services.v2_mechanics_claims \
  --claims docs/drafter-v2/MECHANICS_CURRENT_CLAIMS_2026-09-23.json \
  --archive-dir /tmp/drafter-reviewed-claims \
  > /tmp/drafter-archived-explanations.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  drafter.tests.test_v2_mechanics_claims \
  drafter.tests.test_v2_mechanics_followup \
  drafter.tests.test_v2_mechanics_audit -v
```

Omit `--archive-dir` to read and render only. The destination filename is the
reviewed annotation SHA-256 plus `.json`. Exact bytes are verified before parsing;
modified/reformatted/unreviewed input is rejected. A future revision needs an
explicit evidence/code review, not a timestamp update. Archive import publishes
through an atomic hard link on the destination filesystem. Existing valid files
are reused; conflicting bytes are never overwritten. Interrupted imports can leave
an unpublished `.claim-*` temporary file, never a partially published record.
The filesystem must support hard links; ordinary IO errors are reported without
fallback overwrite. External filesystem edits are detected on subsequent reads.

Each output retains the original typed claim, source URL/section/response digest,
observation timestamp, conditions, limitations and null validity boundaries. The
annotation digest and source-body digest are separate. This archive does **not**
contain the publisher body or certify its availability. Null units/dates remain
null, and numeric/historical use permissions remain false. The renderer always
states unknown equipment, active effect and current applicability; requirements
are not evaluated or converted into team capabilities.

The only admitted purpose is `archived_source_explanation`. Current/numeric/
historical purposes fail closed. There is no historical lookup or general-purpose
claim ingestion interface, current UI integration, unit converter or patch engine.
Rejecting an unreviewed artifact is not a persisted quarantine workflow.

Next: define a bounded official-source revalidation protocol and evidence-backed
revision/conflict records before admitting a present-day consumer. Preserve the
completed probes and dated artifacts; do not infer currency from retrieval time
or treat missing historical validity as a blanket obstacle to new current evidence.
