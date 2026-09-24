# D-024 — frozen prospective comparison

Acquisition feasibility passed D-023: 33 new eligible soloRanked observations from
one ten-request pilot. Independent preflight confirms all 33 fit the fixed common
context. This is evidence of access, not a guarantee of sustained throughput,
representative sampling, power or superior model quality. Pilot observations
remain development/acquisition only; they are permanently excluded from the test.

## Frozen comparison inputs and scope

- Exact verified D-022 Legacy archive content hash
  `23069ec9ec9cbbc8b7475e590c18e9548c4666395834886e12c0cd8436830527`;
  compressed bytes `879c8e73449280deeeb364ebcb2ed4f8997c091237175c6c006358f2eb89dede`.
  No rebuild. All 70 archived implementation files match revision `223574b`
  byte-for-byte. Replay/evaluation must use that separate pinned source context,
  not the subsequently changed acquisition model modules in the working tree.
- Frozen V2 artifact SHA-256
  `92e0b427bf9abce62e047419ea1008f740c9ee7b39b1458ae15692402b7cf52d`.
  No weights, features, calibration or scorer choices change.
- Exact map/mode pairs and Brawler IDs come from the intersection of frozen D-022
  catalog and V2 supported contexts/global feature manifest. Ranked-unavailable
  Brawlers are excluded. Six known, distinct Brawlers in complete 3v3 teams required.
- Full identity/resolution catalog is pinned separately; any drift fails closed.
  No catalog refresh, runtime statistics or online prior changes enter scoring.
- Legacy uses the verified frozen algorithmic patch context ID 1 (Demo-Patch),
  rank pool `alle`, empty personal preferences, complete-team first-pick `true`,
  and D-022's reference clock. These are baseline conventions, not observed
  draft settings or evidence of the actual patch. Matches with another/unknown
  imported patch context are excluded. The API does not supply an actual game
  patch here: it remains UNKNOWN. No claim of same-patch or patch-specific
  generalization is justified. Do not substitute a newer patch or rebuilt inputs.
- Canonical stored side A versus B; use exact frozen complete-team probabilities
  from `DraftEngine.siegchance()` and V2, never normalized recommendation scores.
  Report coverage/exclusions for each engine and paired common-subset results.

`PROSPECTIVE_PREFLIGHT.json` records the exact catalog/common subset and development
manifest digest. It was computed using frozen catalogs and only run-7-linked
post-cutoff examples, without predictions or outcome metrics. Historical holdout
remains closed. D-022's manual priors remain fixed B constants, not Train evidence.

## Acquisition policy

Schema 3 requires verified acquisition feasibility, D-022 receipt, model/code pins,
exact common context and this bounded policy before registration. No real schema-2
window existed; its earlier preparation is superseded.

`collect_prospective_frontier` performs one manual bounded run, never schedules
itself. Zero leaderboard/catalog/profile HTTP requests. At most ten battlelog HTTP
attempts including retries; depth at most one; existing per-player six-hour leases,
backoff, rate-limit handling and shared advisory lock. In addition, no more than
one prospective run in six hours and 56 runs/560 total HTTP attempts in the window.
Aborted/crashed runs consume their run allocation. The initial 1,371 observed-tag
frontier persists; later authentic tags use the same provenance-preserving graph
expansion. Selection remains earliest/null last-fetch, first-seen, tag; no changes
based on model predictions, outcomes, yield, disagreements or desired Brawlers.

Raw responses are kept intact and private in the isolated DB. Preserve its normal
backups and all source links; never delete payloads to resolve duplicates. Missing
fields stay UNKNOWN. No statistics aggregation, automatic training, shadow joins,
mechanics research or model search. Trophy/friendly/other types are not evidence.

A new raw response imports only matches strictly after registered start. Old
entries are raw-only; protected fingerprint collisions do not modify old rows.
Admission additionally requires window end, exact common context and matching
prospective run purpose, code revision and protocol digest. Any pilot origin
excludes a match even if it has an additional prospective sighting.

## Registration and execution

`PROSPECTIVE_WINDOW.json` is atomically published once; its canonical digest is
pinned separately in `PROSPECTIVE_REGISTRATION.json` and the registration commit.
The implementation revision precedes the registration commit, avoiding circular
hashes. Freeze start/end before the start. Do not move/extend/replace the window
based on counts, predictions or outcomes. The acquisition implementation and
artifacts are checked before every invocation; resolution catalog drift fails closed.

Use the existing isolated credential pattern from COLLECTION_RUNBOOK.md; do not
read live credentials or touch live data. One invocation:

```sh
python manage.py collect_prospective_frontier \
  --protocol docs/drafter-v2/PROSPECTIVE_WINDOW.json \
  --expected-protocol-sha256 DIGEST_FROM_PROSPECTIVE_REGISTRATION
```

Before-start/after-end calls fail before creating a run or making an HTTP request.
No cron, daemon, forced timestamps or recurring collector. A future continuation
may perform a due bounded run inside the registered interval. Do not run the pilot
again. The six-hour/global budgets cannot be bypassed by new frontier identities.

Read-only operational inventory uses `drafter_v2_future_window` with the same
protocol and digest. Do not compute predictions, win rates or other performance
metrics while the window is open. After close, immutable membership requires at
least 1,000 qualifying common-subset observations. This is an operational floor,
not a power guarantee. If it is not met, report DATA_UNAVAILABLE; no retrospective
extension. LogLoss, Brier, ten fixed equal-width calibration bins, B0 comparison
and defensible descriptive ranking diagnostics remain the prespecified analyses
in FUTURE_EVALUATION_PROTOCOL.md. No causal pick-benefit claim from battlelogs or
shadow win rates. Dependence/graph selection bias must remain explicit.
