# Next independent window — prepared protocol, NOT REGISTERED

D-019 implements admission/membership infrastructure. No real window has been
registered, sealed, evaluated or added to training. Example timestamps/hashes in
tests are synthetic fixtures. Do not substitute them into a real registration.
Old holdout and recorded comparisons remain permanently closed to development.

## Two independent streams

1. Opt-in shadow Praxisfall records capture user-entered drafts, both returned
   engines and actual later reports. They are unverified, self-selected and
   potentially influenced by recommendations. They support descriptive usage,
   missingness, disagreement and chosen-rank diagnostics only.
2. Future official API `soloRanked` matches from the preserved tagged frontier
   form a possible prospective outcome cohort. Trophy `ranked` never qualifies.
   This is temporal independence from development, not independent sampling of
   players: trophy-seeded graph, repeated players/teams and queried perspectives
   retain selection/dependence bias. No sampling weights are invented.

No shadow-to-Match join, player identity reconstruction, old holdout recovery,
automatic training, model search or mechanics research is part of this milestone.

## Preregistration prerequisites

Before choosing prospective start/end timestamps, freeze and archive:

- Current selected V2 artifact bytes and hash (D-016/D-017; no retraining).
- Exact code revision and development membership hash with latest development
  timestamp. All candidate/feature/hyperparameter decisions use Train/Validation
  only. Rejected opponent models remain rejected. New candidate work needs its
  own preregistered development protocol and must finish before registration.
- An independently audited **Train-only Legacy input bundle**, including catalog,
  provider statistics, priors, configuration, patch/map/mode resolution and source
  membership. Use the unchanged Legacy scorer/probability path. Freeze its hash
  before the future window. No online post-window aggregates may enter scoring.

The current runtime Legacy loaded-input digest is NOT such a bundle: it is a
context-specific hash, not restorable statistics nor verified Train-only lineage.
Historical Legacy aggregate timing is not repaired by labeling it frozen. This
bundle remains a prerequisite; infrastructure does not manufacture or verify its
lineage from a hash. `register()` is a low-level contract called only after that
independent bundle audit. Its `frozen_train_only_verified` field records the
caller's established prerequisite, not a computed audit result. No real call has
been made, and no fair-comparison readiness claim is made here.

After prerequisites, choose a fixed prospective calendar window (planned 14 days)
strictly after registration and every development observation. Freeze dates and
policy in version control before the start; pin canonical protocol digest in the
run record. Do not move the window, replace insufficient results or extend it after
looking at predictions/outcomes. Another window requires a new prospective protocol.
At least 1,000 eligible observations are required to seal under this version:
this is a disclosed operational floor, NOT a power calculation or guarantee of
useful precision. Insufficient data is DATA_UNAVAILABLE, not permission to tune.

## Implemented admission/membership contract

`v2_future_window.register()` validates temporal ordering, version/policy and
required SHA-256 identifiers. `publish()` atomically creates complete files via
exclusive link publication and refuses replacement. Pin `digest(protocol)` in the
preregistration commit/run record, independent of the file later supplied.

`manage.py drafter_v2_future_window --protocol PATH
 --expected-protocol-sha256 DIGEST` reads only the registered future interval in a
repeatable-read, read-only transaction. Its default output is operational counts,
not win rates, predictions or metrics. No historical rows are selected. Sealing
with `--seal-output NEW_PATH` requires the fixed window to be closed and the floor
met. Admission requires official API soloRanked, known non-conflicting result,
known map/mode, complete unique known-brawler 3v3 teams and observed API battlelog
provenance from tagged_frontier_v1 with a CollectorRun, content hash and plausible
fetch timestamp. Missing player tags are never reconstructed or exported.

Membership stores original and reconstructed match fingerprints, played-at,
content hash of outcome/context/composition (no outcome value in manifest), raw
content hashes, source/sampling/run provenance, exclusions, protocol hash and
membership hash. Duplicate fingerprints fail closed; dedup problems must be
resolved without deleting raw payloads. Exact match inclusion is immutable after
seal. Records rejected for missing/conflicting evidence are not silently promoted
later. Additional matches arriving after seal remain excluded.

`--verify-membership PATH` verifies the original content and source evidence;
additional raw sightings are allowed but never alter the seal. Changed outcomes,
teams, context, eligibility, disappeared records or source evidence fail closed.
An operator must retain the original seal digest/commit independently; filesystem
publication/digests do not prevent privileged manual file or database edits.
There is no evaluation or model fitting entrypoint in this command.

## Fair paired evaluation (future, not run)

After one-time sealing, evaluate the frozen candidates without any retuning.
Use complete observed 3v3 compositions on the same common eligible matches;
Legacy `DraftEngine.siegchance()` provides its existing probability mapping.
Do not divide recommendation heuristic scores by 100. V2 uses its complete-team
probability, never a First/Mid hypothetical search leaf. Pin canonical side A/B
orientation, patch/context handling and probability clipping from the existing
metric implementation. Report each model's full coverage and every common-subset
exclusion. Unknown maps/players/builds/skills cannot be filled by guesswork.

Primary metrics: paired LogLoss and Brier differences, plus calibration in ten
fixed equal-width probability bins with counts, mean prediction and observed
frequency. Report sample size, dates, source cohort, patch mix and coverage.
Use the existing B0 50/50 comparison. Any uncertainty analysis must account for
repeated-player/time dependence and state its assumptions; no independent-match
significance claim or fabricated confidence interval. Raw player tags stay private.
No threshold or calibration fitting on test outcomes; no promotion from rank
agreement or merely crossing the operational sample floor.

Ranking diagnostics are descriptive where actual draft order, bans, legal pool
and chosen pick were observed: top-k overlap, chosen rank, unknown-pick coverage
and phase-stratified disagreement. Match battlelogs alone do not establish draft
order or legal alternatives. A chosen pick is not a ground-truth optimal pick;
nonchosen counterfactual outcomes remain unknown. Early-phase search evaluation
requires actually observed continuations. No recommendation regret/NDCG/causal
benefit is asserted without defensible labels. Shadow win rates stay separate
from this independent API cohort and cannot supply missing test outcomes.

## Collection readiness and resume

Read-only audit at 2026-09-23T21:51:32Z: three preserved frontier players, zero due,
next stored cooldown minimum 2026-09-23T23:39:17Z. Zero API soloRanked observations
after the existing cutoff; 125 trophy ranked observations are not Ranked evidence.
No collection was attempted, credentials were not loaded, and no cooldown changed.
Reproducer: `shadow_frontier_readiness.py`; measured counts:
`SHADOW_FRONTIER_READINESS.json`. Zero real shadow snapshots currently exist.

Once due, a new bounded revisit may use zero ranking seeds, at most five battlelog
HTTP attempts including retries, depth at most one, unchanged six-hour claims,
backoff/rate-limit/lock rules and raw persistence. Record code revision, request
budget, genuine eligible soloRanked counts and retained provenance. Do not repeat
bootstrap, force timestamps, expand sources or set up a recurring collector.
Use existing COLLECTION_RUNBOOK.md and command; no API call is made by readiness.
Import cutoff protection remains unchanged; future admission separately enforces
its own preregistered dates. No qualifying observations means stop that bounded
run, record DATA_UNAVAILABLE and retain evidence rather than immediately retrying.

Validation: 46 combined future-contract/shadow/frontier tests passed (4.443 s),
then eight focused future tests including SQL-boundary, content-change and
true-development-end coverage passed (1.027 s). Fixtures are explicitly synthetic, not evidence accumulation.
