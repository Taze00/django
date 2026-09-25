# Drafter V2 Evaluation

Status: historical dataset frozen; B0-B5, the non-active V2 candidate and the
reporting-only Legacy/V2 shared subset have been measured. Legacy comparison is
complete; V2 was not promoted.

Planned frozen protocol:
- Unit of observation: deduplicated, conflict-free Ranked match with known winner.
- Time-based train/validation/holdout split; no future rows in training and no fingerprint across splits.
- Primary metrics: log loss, Brier score, calibration. AUC/accuracy are secondary.
- Baselines: B0 50/50, B1 validated skill-only if available, B2 global meta, B3 meta+mode, B4 meta+map, B5 smoothed pair/synergy. B1 is currently unavailable because no validated skill control variable exists.
- Legacy evaluated on exactly the same holdout without changing Legacy scoring.
- Fixed seed, commit hash, feature manifest, split definition and patch window recorded in every report.
- Leakage checks cover duplicate fingerprints, future features, result-derived fields, player identity, post-match fields and sampling artifacts.

The holdout is not used for tuning or feature selection. The current freeze is
manifest `v2-dataset-freeze-1`, fingerprint digest
`2bb8222b9025a5da7daadea8b9a252c39b16bcda8b07b9bc2df69315ea4dcf9e`, with
6,094 train, 2,031 validation and 2,033 holdout rows. The eligible window is
2026-08-29 through 2026-09-18 UTC. The initial freeze used commit
`425499425fcf9a3c07b15b389cad8bbf51129859`; the final sealed rerun used
`5c3d7bf766e86aac839a32fcbadc281dc52f9778` and produced the same digest and
split counts.

## Measured baselines

| Model | Validation Log Loss | Validation Brier | Holdout Log Loss | Holdout Brier |
|---|---:|---:|---:|---:|
| B0 50/50 | 0.693147 | 0.250000 | 0.693147 | 0.250000 |
| B2 global meta | 0.692929 | 0.249731 | 0.704446 | 0.255430 |
| B3 meta + mode | 0.722226 | 0.262396 | 0.730888 | 0.266350 |
| B4 meta + map | 0.765516 | 0.278296 | 0.772412 | 0.281109 |
| B5 meta + pair/synergy | 0.698784 | 0.252338 | 0.717746 | 0.261380 |

Unchanged Legacy probability layer: validation not applicable (the Legacy
probability provider is not trained on this split); holdout Log Loss `0.689749`,
Brier `0.248301`, `n=1,956`. It skipped 77 rows with duplicate Brawlers because
the unchanged `DraftContext` contract rejects those historical compositions.

## Shared Legacy/V2 subset

For the final apples-to-apples reporting correction, both models were evaluated
on the exact 1,956 holdout fingerprints eligible for unchanged Legacy. The
full V2 holdout remains a separate coverage metric (`n=2,033`).

| Model | Shared n | Log Loss | Brier |
|---|---:|---:|---:|
| Legacy unchanged | 1,956 | 0.689749 | 0.248301 |
| V2 candidate | 1,956 | 0.692600 | 0.249725 |

The shared subset changes reporting only. It did not change V2 features,
hyperparameters, regularization, model structure, training data or selection.
The report includes the exact shared fingerprints under `shared_subset`.

B1 skill-only is unavailable: no validated causal skill control was identified.
The B0-B5 holdout values are descriptive and sealed for model selection.

## Candidate V measurement

The dependency-free L2 logistic candidate was trained on train only with 300
epochs and regularization 1.0, selected using validation. Validation:
Log Loss 0.688604, Brier 0.247741. The sealed holdout yielded Log Loss
0.692603 and Brier 0.249727. Legacy remains better on the sealed comparison,
so V2 is not promoted and Legacy remains the default. Regularization checks
0.01/0.1/1/10 showed validation Log Loss 0.688602/0.688603/0.688604/0.688617;
the selection was made on validation only.

## Reproducer

```text
python manage.py drafter_v2_evaluate --format json
```

The command is read-only. It loads conflict-free, known-result, complete 3v3
`soloRanked` matches, sorts by `(played_at, fingerprint)`, rejects duplicate
fingerprints, and uses a 60/20/20 time split. `DATA_UNAVAILABLE` is returned
when the holdout is empty. Pass `--git-commit $(git rev-parse HEAD)` when the
container image has no Git binary. Current frozen result: input `10,158`, train
`6,094`, validation `2,031`, holdout `2,033`.

Use `--skip-legacy` for the faster B0-B5-only run; the default still includes
the unchanged Legacy benchmark and reports any ineligible rows.

The implementation is dependency-free and lives in
`drafter/services/evaluation.py`. It records skipped incomplete or unknown
rows, and reports log loss, Brier score and probability-bin calibration.

## Legacy benchmark

The command additionally evaluates the unchanged Legacy probability layer
(`DraftEngine.siegchance()`) on the identical holdout when complete catalog
references are available. It does not train, alter, or normalize Legacy
scores. On the frozen isolated snapshot it evaluated 1,956 eligible rows;
ineligible duplicate-Brawler rows are reported separately rather than silently
altered.
Historical matches with duplicate Brawlers are valid observations for V2 but
are ineligible for the unchanged DraftContext Legacy contract; the report
counts those rows under `legacy.skipped` instead of modifying Legacy.

Final regression after the sealed rerun: 691 Drafter tests, 4 skipped, 0
failures. The separate Fitness suite remained green at 253 tests.


## Closed freeze and future-experiment boundary

The current user's resume instruction closes this freeze, including its
shared-subset comparison. All recorded numbers above remain final and
unchanged. Do not rerun `drafter_v2_evaluate`, `drafter_v2_train` or
`drafter_v2_freeze` on the historical database for further selection. The
commands currently derive their input/split from mutable database contents;
they are historical reproducers, not a safe automatic next-experiment protocol.

Code-inspection limitation, without recomputing the final results:
`drafter_v2_evaluate.Command._legacy_predictions` loads `Datenraum` from the
database provider, not a train-only `SnapshotStatProvider`. The imported
statistics are not shown to exclude holdout observations. Thus the recorded
Legacy/V2 comparison is not evidence of leakage-free out-of-sample superiority.
The shared subset fixes coverage comparability, not statistical-input timing.
This caveat does not alter the final report, justify retuning V2, or change
the decision to keep Legacy active. Future evaluation must use immutable
dataset membership and training-only aggregates, including all priors.

For now, run only `drafter_v2_growth --after 2026-09-18T15:04:42Z` to audit
new temporal evidence. It computes no predictions or performance metrics.
Positive counts mean observations exist, not that a dataset is large enough,
calibrated, patch-comparable or suitable for promotion.

## D-011 validation boundary

31 offline claim/source-structure contracts passed, including seven new archive
and explanation tests. These validate provenance preservation and rejection
behavior, not gameplay accuracy, current source freshness or prediction quality.
No dataset/model/holdout evaluation performed; sealed results remain unchanged.

## D-012 development-only recovery

User now authorizes Train/Validation experimentation, superseding the earlier
blanket ban on training. Historical holdout remains closed; old commands remain
unsuitable. `drafter_v2_challenger_train` verifies frozen membership metadata and
loads only the two development partitions. See CHALLENGER_PROTOCOL.md and
CHALLENGER_BASELINE.json. Validation reproduced LogLoss 0.6886038069604661,
Brier 0.24774078927297735 (n=2,031); no new holdout metric.
Train example digest: 5e8ff094ad9f93ed565bcaed9f725ffd7d78dd67c22e31c7b6aaed6cd2cec447.
Validation digest: 4b2806db07d35e20dd8a0e6e76bef74dd928706b90e6615a3b2f64776c3df797.

## D-013 bounded development experiment

| Candidate | L2 | Validation LogLoss | Validation Brier |
|---|---:|---:|---:|
| Existing | 1 | 0.688603807 | 0.247740789 |
| Opponent interactions | 1 | 0.688671923 | 0.247772212 |
| Opponent interactions | 10 | 0.688677816 | 0.247775099 |
| Opponent interactions | 100 | 0.688765489 | 0.247818086 |

All n=2,031. Existing selected under preregistered rule; no improvement claimed.
The same train/validation canonical digests were reproduced. Full calibration,
fit/inference times and artifact digest in CHALLENGER_OPPONENT_EXPERIMENT.json.
Independent test/promotion remains unavailable; old sealed results untouched.

D-014 functional validation: 15 search/runtime regressions passed. One real
isolated smoke request per phase measured First 770.071 ms (8,452 leaves), Mid
92.893 ms (900), Last 44.313 ms (100). Shortlist approximation is disclosed; these
are software/performance checks, not an empirical comparison of draft outcomes.

D-015 validation: 55 API/Praxisfall regressions and 12 final Challenger tests passed
(overlapping suites, not 67 unique tests). Migration drift clean; additive migration
0020 applied only in isolation. Side-by-side output is not an outcome benchmark.
Saved self-selected user decisions/results are excluded from automatic training.

## D-016 final validation

774 full Drafter tests passed with four existing skips (336.643 s); 253 protected
Fitness tests passed (138.720 s). Final focused content/UX checks are recorded in
STATUS. V8 syntax compilation and real localhost HTTP/static/CSRF/three-phase
comparison passed (CHALLENGER_HTTP_SMOKE.json); no automated rendered-browser test.
Actual Train/Validation content hashes reproduced once more after adding strict
content guards, without fitting/predicting a model or touching held-out examples.

Runtime byte SHA-256 is now explicitly separate from canonical artifact content
SHA-256 in both training commands and reports. Original canonical digests remain
preserved; no fitted values or recorded metrics changed. Final product/evidence
matrix, limitations and remaining independent-test blocker: CHALLENGER_REPORT.md.


## D-017 runtime diagnostic, not evaluation
HIDEOUT_DIAGNOSTIC.json records exact real Hideout probabilities, additive
attribution, Legacy parity and resolved context/data hashes. No outcomes queried,
model fit, holdout access or improvement claim. 52 focused regressions passed;
real repeatable-read endpoint parity and local HTTP smoke passed. Differences in
rank/probability are not evidence of draft quality or statistical significance.


D-018: shadow capture is descriptive observation only; no LogLoss/Brier claims from unverified self-reported outcomes or hypothetical early-pick continuations. Keep this cohort outside future independent evaluation membership.


D-019 future protocol is prepared, not executed: separate official soloRanked cohort, frozen Train-only inputs, immutable temporal membership, paired complete-team LogLoss/Brier and fixed-bin calibration. Descriptive ranking only with observed order/legal alternatives; no counterfactual optimal-pick claims. New command never trains/predicts or reads old rows. See FUTURE_EVALUATION_PROTOCOL.md.


D-020 collected no qualifying Ranked test evidence. No window registered, no outcome evaluation or model fit. Independent growth audit and run evidence committed.


D-021 fair-comparison prerequisite failed: exact overlay priors lack Train lineage. Future protocol remains unregistered. See LEGACY_TRAIN_BUNDLE.md for required explicit baseline input-policy distinction. No new metrics or model work.


D-022 frozen baseline construction is not quality evaluation: only Train compositions used for replay invariants; no validation/holdout metrics or fitting. Primary baseline retains manual priors as authorized constants. Complete-team Legacy siegchance path and normal Last-Pick serialization are replayed; no prior-free ablation replaces it. Independent source ledger/raw counts plus archive-only replay are required.


D-022 result: VERIFIED bundle 23069ec9ec9cbbc8b7475e590c18e9548c4666395834886e12c0cd8436830527. 94,302 empirical rows from 6,094 Train; 137 identical B priors; two identical builds, independent all-row counts/membership and 28 archive-only scoring replays passed. 20 focused tests passed (4.342 s). No future window registered; independent soloRanked evidence remains unavailable in the latest collection report. Exact contracts/limits: LEGACY_BUNDLE_RUNBOOK.md and verification/artifact JSONs.


D-023 acquisition pilot is not an evaluation. Pilot sampling is excluded from prospective sealing/verification, including matches later seen by another collector. No metrics or model selection are run.


D-023 pilot completed (run 7, 2026-09-24T16:22:13Z–16:24:00Z): acquisition feasibility demonstrated. Ten battlelog HTTP 200, zero retries/ranking requests. 340 authentic observed query roots; 250 raw entries: 201 trophy ranked, 33 soloRanked, 16 type UNKNOWN. Parser retained all 33 soloRanked; 60 unsupported/non-3v3 entries skipped, zero parser errors or future-dated records. 185 newly imported matches: 152 trophy and 33 eligible soloRanked; five trophy duplicates, zero conflicts. 1,031 additional query tags; discovery frontier 1,371, eligible Ranked-evidence frontier 56. Independent raw/parser/import audit agrees. Pilot matches remain permanently excluded from future test membership and automatic training.


D-024: schema 3 freezes common coverage (28 map/mode pairs, 106 supported Ranked-available Brawlers), canonical side orientation and frozen Legacy patch convention. Reject mismatched catalog/protocol/code provenance. No prospective metrics until immutable post-window sealing; minimum 1,000 is operational, not power.


D-024 REGISTERED_NOT_STARTED. Fixed interval: (2026-09-25T00:00:00Z, 2026-10-09T00:00:00Z]. Registration: 2026-09-24T16:37:53.358317Z. Protocol digest 70e55f3dde205e15b232814f98b4e00c34fac8238f2fe5bc8b190608891adac8; implementation revision e9e6e7714409b566e86197abf01ddbe0957eaa9f. D-022 bundle and V2 artifact remain byte-identical. Fifty-nine combined tests passed (8.696 s). Real read-only pre-start collector check rejected before HTTP/run creation; inventory is zero. No predictions, metrics, training, promotion or recurring collector.


D-026: sustainable development collector/dataset implementation complete, validation pending. Ranked activity priority with one broader exploration query per five, 50-attempt cycles, unchanged per-player cooldown/client safeguards, global pause on quota signals, durable raw/checkpoints and replay without HTTP. New trophy entries remain raw/discovery-only. Versioned dataset includes verified original Train plus eligible recent development data; no old holdout or protected future final origins. Model development waits for preregistered chronological volume gates. See DEVELOPMENT_COLLECTION.md.
