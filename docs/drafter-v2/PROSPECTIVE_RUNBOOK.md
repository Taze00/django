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

## Actual registration and temporal gate

D-024 REGISTERED_NOT_STARTED. Fixed interval: (2026-09-25T00:00:00Z, 2026-10-09T00:00:00Z]. Registration: 2026-09-24T16:37:53.358317Z. Protocol digest 70e55f3dde205e15b232814f98b4e00c34fac8238f2fe5bc8b190608891adac8; implementation revision e9e6e7714409b566e86197abf01ddbe0957eaa9f. D-022 bundle and V2 artifact remain byte-identical. Fifty-nine combined tests passed (8.696 s). Real read-only pre-start collector check rejected before HTTP/run creation; inventory is zero. No predictions, metrics, training, promotion or recurring collector.

Protocol: `PROSPECTIVE_WINDOW.json`; digest receipt:
`PROSPECTIVE_REGISTRATION.json`; actual pre-start check:
`PROSPECTIVE_REGISTRATION_CHECK.json`. Start is 02:00 Europe/Berlin on
25 September; end is 02:00 Europe/Berlin on 9 October. No prospective API
request has been made. The fixed calendar boundary is the current external
blocker; keep Legacy default and the existing Challenger usable while waiting.

## Operational continuation: 25 September, run 8

Run 8 completed 2026-09-25T14:12:18.440952+00:00–2026-09-25T14:16:42.334100+00:00: ten battlelog HTTP 200, zero retries/ranking requests, 250 raw entries (233 trophy ranked, one friendly, 16 UNKNOWN). No raw soloRanked and no newly eligible prospective observations: DATA_UNAVAILABLE for this run, not a final window verdict. 94 pre-start entries retained raw-only; 33 unsupported entries skipped. 105 new matches (104 trophy, one friendly), 18 trophy duplicates, zero conflicts. All 105 current-window rows are excluded as non-soloRanked. Current admissible prospective count is zero; no membership sealed.

1,294 new query-eligible tags; discovery frontier 2,665. The cumulative Ranked-evidence frontier remains 56 tags/33 matches from the excluded pilot; these are not prospective observations. All ten raw content hashes, frozen implementation/artifacts and catalog identities verified. Preflight found 1,371 due existing tags and no earlier prospective run. Fourteen focused prospective/future-window regressions passed (3.759 s) on synthetic data.

The window is now open. The pre-start checkpoint above is historical. No policy
or registered JSON was changed. Next global run gate: 2026-09-25T20:12:18.440952+00:00.
No immediate retry or recurring job. Acquisition/integrity evidence only:
`PROSPECTIVE_RUN_008_2026-09-25.json`; reproducer:
`prospective_acquisition_audit.py` through read-only `manage.py shell`.
Its candidate count checks the frozen admission predicates but neither seals
membership nor computes model performance. Source tags and response bodies
remain private in the isolated database.
