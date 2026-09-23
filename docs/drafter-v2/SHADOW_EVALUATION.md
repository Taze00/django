# Shadow observations (D-018)

Authenticated users may explicitly enable Shadow-Protokoll on the Challenger.
Every successful opted-in calculation persists both engines' complete returned
recommendations before any pick/result is supplied. Legacy still uses the exact
normal als_dict path (eight detailed recommendations plus all candidate scores);
V2 preserves every recommendation, feature explanation and hypothetical search.
The normal/default Legacy surface is unchanged. Shadow here means observation,
not a blinded experiment: both recommendations are returned to the user.

No pick is inferred from rank 1. Unknown choice is an empty existing Praxisfall
field, rank is null, and outcome stays unknown. The owner can subsequently report
a pick from the archived legal pool, including a pick with no V2 training support;
its V2 rank then stays null. Win/loss requires an explicit choice. Corrections
append timestamped user-report events under a row lock; exact repeated reports
are idempotent. Recommendations never rerun on save/replay/report. Manual signed
selected-pick saves remain supported. Signed snapshots retain the two-hour expiry
and ownership checks. Private list/replay/result APIs retain authentication/CSRF.

Provenance includes schema, original resolved context, both model versions, V2
artifact hash, Legacy context/provider/configuration/loaded-input receipt, full
response and canonical response digest. Canonical hashing normalizes integral
floats because PostgreSQL JSONB does so. Captured time is recommendation time;
actual match-played time is UNKNOWN (legacy gespielt_am stores captured time).
Raw player identities/tokens are not added. No schema migration is required.

Bias is explicit: self-selected users and requests, exposure to recommendations,
optional outcomes, possible hypothetical drafts and repeated requests for one
match. A snapshot ID is a request observation, not a unique match fingerprint.
No causal pick benefit, game quality, or independent-test membership follows.
Real match status is unverified. No linkage to API matches is inferred.
These records remain excluded from training and future test admission; existing
trainers/importers operate on Match data, never these Praxisfall records.

The response is immutable through these APIs. Django admin/database operators
still have ordinary maintenance privileges; this is not WORM storage or external
tamper-proof notarization. Digests permit later integrity checks. Existing
historical snapshots are preserved without invented provenance backfills.

Validation: 19 focused tests passed (3.063 s), including inherited Challenger
privacy, CSRF, expiry, replay, model and logging contracts plus shadow pre-choice,
response-hash roundtrip, audit history, opt-in and unsupported-choice tests;
exact Hideout Legacy parity tests included. JavaScript parses in V8. No genuine
user draft or outcome was fabricated to populate the isolated database.

Next: future independent API observation protocol and immutable membership gates.
Shadow logs stay a separate descriptive cohort, never the new sealed test.
