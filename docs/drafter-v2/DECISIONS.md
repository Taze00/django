# Drafter V2 Entscheidungen

## D-001: Isolierte Entwicklungsdatenbank

Problem:
Das Standard-Compose bindet `./data/db` und ist für den Entwicklungsbetrieb gedacht; der Live-Checkout `/media/docker/alex-django` läuft parallel mit eigenem Compose-Projekt und eigener Bind-Mount-Datenbank.

Alternativen:
Standard-Compose unverändert starten; die Live-Datenbank verwenden; ein eigenes Compose-Projekt mit lokaler, neu angelegter Bind-Mount-Datenbank nutzen.

Evidence:
Der Feature-Worktree enthält aktuell kein `data/`; `docker compose ls` zeigt das laufende Projekt `alex-django` mit Compose-Datei im Original-Checkout.

Decision:
Nur das Compose-Projekt `drafter-v2-isolated` verwenden. Vor jedem Lauf werden Worktree, `data/`-Metadaten und aufgelöste Mounts geprüft. Keine Verbindung zum Live-Compose-Projekt, keine Verbindung zu dessen Datenbank und keine Verwendung des Original-Worktrees.

Why:
Die Tests brauchen Django/Postgres, dürfen aber weder Live-Daten noch Rawpayloads verändern. Eine frische lokale Bind-Mount-Datenbank ist reversibel und fachlich ausreichend für Tests.

Validation:
Vor Containerstart: `realpath`, `stat`, `docker compose -p drafter-v2-isolated config`; nach Start: Container-/Volume-/Mountprüfung. Kein `docker compose exec` im Live-Projekt.

Revisit if:
Historische Daten für Evaluation benötigt werden. Dann zuerst read-only Snapshot/Export mit dokumentierter Isolation entwerfen; keine direkte Live-Verbindung.

## D-003: Kein API- oder Live-Datenzugriff ohne getrennte Autorisierung

Problem:
Die Phase-1-Datenbank im Feature-Worktree ist frisch. Ein historischer
Holdout oder ein offizieller API-Audit könnte nur aus dem Live-System oder mit
einem Credential kommen, das hier nicht vorhanden ist.

Evidence:
Der Host und der Feature-Worktree enthalten keinen gesetzten
`BRAWL_STARS_API_KEY`; `/media/docker/alex-django` läuft separat und seine
`.env`/Datenbank wurden nicht geöffnet. Die anonymisierte Fixture ist lokal,
aber kein Ersatz für historische Daten.

Decision:
Keine API-Anfrage, kein Collector-Lauf und keine direkte Live-DB-Abfrage. Für
spätere Evaluation ist ausschließlich ein separat autorisierter read-only
Logical Snapshot zulässig: read-only DB-Rolle, export in einen neuen isolierten
Zielpfad, anschließende Offline-Evaluation gegen eine eigene Datenbank; keine
Live-Mounts, keine Rawpayload-Löschung und keine Rückschreibeverbindung.

Why:
So bleiben Live-DB, produktionsnahe Volumes, Rawpayloads und Original-Worktree
unberührt. Fehlende historische Daten werden als DATA_UNAVAILABLE behandelt.

Validation:
Compose-Mountprüfung zeigte nur den Feature-Worktree; API-Key-Prüfung zeigte
keinen Key; alle Evaluationscommands lieferten bei leerer DB `DATA_UNAVAILABLE`.

Revisit if:
Ein sicherer, separat autorisierter Snapshot und ein dokumentierter Importpfad
bereitgestellt werden.

## D-004: Bounded isolated collector for new data

Problem:
The frozen comparison ends on 2026-09-18. A future evaluation needs genuinely
new Ranked observations rather than retuning on the sealed holdout.

Evidence:
The repository collector enforces a 0.25 second request spacing, retries only
transient failures, caps a run at `max_spieler`, limits discovery depth and
stores provenance on `CollectorRun`/`RawPayload`. The isolated database is
separate from the live database.

Decision:
Run one authorized, bounded collector job in the isolated Compose project
with at most five battlelogs, depth 1, six-hour refresh spacing, no optional
raw files, and the existing official API key only in process environment.
Then audit/import/aggregate only in the isolated database. Do not use new
rows to modify the sealed historical comparison.

Why:
This grows the dataset additively and preserves source provenance,
deduplication and patch boundaries without touching live data or copying the
live `.env`.

Validation:
Before the run, live and isolated containers/mounts were distinct; the key is
not printed or stored; the collector command performs no aggregation.

Observed result:
Three isolated runs completed with HTTP 200 responses and no rate-limit
headers. One run added 100 non-eligible `ranked` trophy matches; the targeted
soloRanked follow-up added zero new matches because all 125 observations were
duplicates. The old soloRanked freeze was not reopened.

Revisit if:
The API returns credential/rate-limit errors, the collector cannot persist
provenance safely, or the new window has too few observations for a new freeze.

## D-002: Symmetrisches, dependency-freies V-Modell

Problem:
V2 braucht eine probabilistische Bewertungsfunktion für vollständige Teams,
aber die isolierte Datenbank enthält keine historischen Ranked-Matches und die
Runtime-Abhängigkeiten enthalten keine ML-Bibliothek.

Alternativen:
Neural-/Set-Modell; neue ML-Abhängigkeit installieren; Legacy-Score als V2
ausgeben; regularisierte Logit-Regression mit Standardbibliothek.

Evidence:
Phase-2/3 Runner melden reproduzierbar `DATA_UNAVAILABLE`; der Legacy-Engine
Vertrag ist heuristisch und nicht als kalibrierte Team-Wahrscheinlichkeit
ausgewiesen.

Decision:
Eine kleine L2-regularisierte logistische Regression mit signierten
Teamdifferenz-Features wird parallel trainierbar gemacht. Es gibt keinen
Intercept; Team-Swap ist dadurch exakt symmetrisch. Das Modell ist nicht aktiv
und wird nur bei explizitem Output-Pfad persistiert.

Why:
Die Architektur ist erklärbar, deterministisch, CPU-tauglich und kann bei
verfügbaren Daten gegen B0-B5 evaluiert werden, ohne die Legacy-Baseline zu
verändern oder Plausibilitätsgewichte zu erfinden.

Validation:
Symmetrie- und Determinismustests grün; leerer Trainingslauf liefert
`DATA_UNAVAILABLE` und erzeugt kein Artefakt.

Revisit if:
Ein eingefrorener Holdout zeigt, dass einfachere B0-B5-Modelle gleich gut oder
besser sind, oder echte Daten die Feature-Sparsität begrenzen.


## D-005: Continue with a growth audit, not another historical evaluation

Problem:
The previous agent left four documentation changes uncommitted. Its status
still called for a collector run although its audit recorded three completed
runs with no newer Ranked evidence. The evaluated holdout is closed.

Evidence:
The isolated read-only inventory reproduces the inherited counts and three
collector records. No API credential is available in the current host/worktree.
The current user forbids access to the live checkout/database.

Decision:
Preserve the prior notes and verify their aggregates. Add `drafter_v2_growth`
with an explicit timezone-aware, exclusive played-at cutoff. It reads only
new API rows for eligibility; trophy, synthetic and unverified fixture rows
are excluded. Unknown winners, conflicts, incomplete teams and missing Brawler
references remain exclusions. Multiple payload sightings do not increase the
match count. Report missing provenance as UNKNOWN and missing run counters as
null. Do not train, evaluate, create another freeze, change Legacy or infer
promotion readiness from the presence of observations.

Why:
This makes progress measurable without reusing the sealed holdout or
mistaking a recently fetched old match for new temporal evidence. A bounded
runbook allows collection to resume when an isolated credential is available.

Validation:
Regression tests exercise timestamp boundaries, source/type filters, missing
data, repeated sightings, read-only SQL and redacted collector summaries.
The real growth audit runs with PostgreSQL read-only transactions.

Revisit if:
New eligible API observations arrive. Before experimenting, define a new
temporal split, source/patch policy and train-only statistical snapshots;
do not silently repartition the growing database with the old commands.


## D-006: Structured conditional mechanics and composition matchups

Problem:
Flat booleans lose ability/loadout requirements and patch validity. Subjective
ratings confuse sourced mechanics with strategic value; role counts do not
answer whether a team can meet the opponent's concrete threats.

Alternatives:
Extend the legacy 32-attribute system; flatten kit effects to global booleans;
or separate versioned raw facts, deterministic derivations and empirically
validated strategic concepts.

Evidence:
The user's architecture clarification (2026-09-23) requires the third option.
Historical loadouts and patch-level objective mechanics remain insufficiently
sourced. The old holdout is closed, so no new feature benefit can be asserted
from it. This is a contract decision, not an empirical feature result.

Decision:
Master sections 12/13/15 and PLAN phase gates now specify a typed mechanics
model with source/retrieval dates, patch validity, raw/normalized values,
formula/input lineage and explicit ability dependencies/activation/uses.
Base attack, Super, Gadget, Star Power, Hypercharge, transformations and
summons remain distinct; ownership never proves equipped or active loadout.
Unknown requirements, values and historical builds stay UNKNOWN.
Composition hypotheses compare concrete capabilities to enemy defenses/win
conditions, are independently ablatable and require a new empirical test
window. Search evaluates complete resulting states, not isolated strength.
The coverage audit must expose per-Brawler raw/conditional/unknown fields
and global mechanic/source/patch coverage with explicit denominators.

Why:
This prevents gadget-only effects becoming permanent abilities, modern facts
being applied retroactively and hand-tuned anti-tank/thrower/safety scores
entering V2 under the name of mechanics. Critical weaknesses may lower an
individual pick only through validated composition value, not a chosen rank.

Validation:
Requirements checked against all nine points in the user's clarification.
No speculative schema, mechanic data, model feature, Legacy change or holdout
rerun is part of this documentation milestone. Existing regression contracts
are run separately; future mechanics acceptance tests remain prospective.

Revisit if:
Verified source/coverage evidence permits implementation, or new preregistered
ablations support or reject an interaction. No feature promotion by plausibility.


## D-007: Empty broad selection is missing provenance, not a cooldown bug

Problem:
The independently supplied credential loaded successfully, yet bounded run 4
selected zero players and made zero requests. The previous STATUS credential
blocker is obsolete; another identical run would not create evidence.

Evidence:
Run 4 (`cd6481e`) used max five battlelogs, depth 1 and six-hour spacing.
The read-only queue audit found 61,146 Ranked player rows with zero nonblank
tags, zero broad-qualified candidates, 205 active tracked players at depth
<=1 and 200 due players at the recorded audit time. Historical anonymization
removed the player-tag linkage required by HighRankStichprobe. The strategy
intentionally returns None without falling back to the trophy ranking queue.

Alternatives:
Fabricate/reconstruct identity linkage; bypass cooldowns; silently switch to
standard trophy-seed sampling; or preserve the sampling contract and obtain
independently sourced genuine Ranked provenance.

Decision:
Keep the broad strategy, timestamps and deduplication unchanged. Record
DATA_UNAVAILABLE for genuinely newer Ranked observations, stop repeated empty
runs and retain the run record. Supply actual tagged soloRanked payloads through
the normal isolated importer before attempting broad collection again. A
separate discovery bootstrap requires an explicit revised collection plan and
truthful sampling provenance; it is not a repair to the frozen engine/model.

Why:
Due trophy-ranking players are not evidence of qualifying Ranked history.
Waiting for cooldowns or possessing a credential cannot restore redacted tags.
The current data cannot safely resolve this prerequisite by itself.

Validation:
Isolated read-only inventory, growth report and queue audit reproduce the
counts; 94 relevant collector/sampling/UNKNOWN/V2/logging contract tests passed
with normal settings, zero failures (13.401 s test runtime).
No credential exposed, live access, model change or sealed evaluation.

Revisit if:
Independent observed Tagged Ranked evidence makes broad candidates available,
or the user specifies a bounded discovery plan with separate provenance.


## D-008: Independent persistent tagged frontier from official rankings

Problem: all 61,146 historical Ranked MatchPlayer rows are anonymized. The
existing broad_high_rank graph cannot recover their identity linkage. The
user explicitly authorized an independent bounded bootstrap on 2026-09-23.

Decision: add TaggedPlayer as an opt-in membership linked one-to-one to the
existing unique TrackedPlayer tag and its shared fetch/cooldown state. Old
queue membership alone is insufficient. TaggedPlayer preserves first source,
first/last observed timestamps, first run and minimum observed graph depth.
TaggedPlayerObservation appends the source kind (ranking, solo_ranked, query),
exact raw JSON pointer, RawPayload, CollectorRun, queried player and observed
match. Later sightings never overwrite first source or historical player tags.
Only normalization of supplied tag strings is allowed; no names/IDs become tags.
Ranking position/trophies stay raw ranking metadata, never match skill labels.

Protocol: distinct sampling=tagged_frontier_v1; an explicit exclusive played-at
cutoff; one global ranking HTTP attempt, at most three admitted seeds in this
experiment, five battlelog HTTP attempts including retries. No catalog/profile
requests, ranking pagination, auto aggregation or model work. Reuse the existing
API client/parser/fingerprint importer. Unknown catalog references stay unknown.
Records at/before the cutoff remain only in raw responses; no frozen labels or
historical MatchPlayer tags are updated. Discovery requires a current known-result,
conflict-free API soloRanked match with complete known-Brawler 3v3 teams and
actual tag fields. Trophy `ranked`, missing perspective/result, malformed teams,
unknown Brawlers and conflicts do not seed discovery. All raw fields remain saved.

Depth is bounded new request hops per run: existing frontier members and freshly
admitted ranking seeds are roots; depth 1 may query their discovered neighbors.
Tags observed at the request boundary remain stored for the next run, with exact
parent edges and their cumulative discovery depth. This grows across runs without
open recursion. Each player is attempted once per run; HTTP retries consume the
same five-attempt cap. A per-database advisory lock serializes frontier runs.
A durable six-hour claim precedes HTTP, preventing immediate refetch after a crash.
Successful fetches require six hours before revisit; 404 pauses seven days;
transient errors retain at least six hours and can back off to 48 hours. No forced
timestamp reset. The ranking endpoint also has a six-hour cooldown. 401/403 and
exhausted 429 stop; three consecutive failed player fetches stop. No usable tags
in the ranking response stops before any battlelog, retaining that response.

Tradeoffs: trophy leaders and their observed neighbors form a biased convenience
sample. Neither skill comparability nor sampling correction is established.
The small run measures collection feasibility only. Historical anonymization
remains irreversible. The existing broad strategy and Legacy engine are unchanged.
No new seed source is selected if official rankings fail. No recurring job is added.

Validation: focused synthetic tests cover source/JSON/run lineage, persistent
multi-run discovery, duplicate players/matches and opposing player perspectives,
cooldown boundary and old-queue preservation, blank/malformed tags, strict Ranked
filtering, zero-request empty frontier, depth boundaries, capped retries/Retry-After,
404/credential/parser failures and crash persistence. Real API evidence is recorded
separately after the bounded experiment in DATA_AUDIT and STATUS.

Revisit: only a documented new bounded collection plan may expand request limits,
seed populations or depth. New observations need a preregistered immutable future
split and train-only inputs before any model experiment. The historical comparison
is final and is not rerun.


D-008 observed outcome: run 5 at revision 8661c29 finished on 2026-09-23 with
one ranking and three battlelog HTTP 200 responses, no retries. Official ranking
provided 200 distinct usable tag strings; three seeds persisted and were due.
All 75 battlelog entries were trophy `ranked`; 50 newer unique matches imported,
25 older entries kept raw-only, zero duplicates/conflicts/new soloRanked or new
frontier neighbors. Three ranking + three query observations persist; raw payloads
retain 393 distinct team tags. Frontier size 3, due 0 at the post-run audit.
DATA_UNAVAILABLE remains the new Ranked evidence status. Stop this experiment;
no follow-up request or model experiment was made. Real soloRanked expansion is
not empirically demonstrated by this run. See BOOTSTRAP_EXPERIMENT_2026-09-23.json.


## D-009: Raw mechanics coverage is not patch-qualified feature coverage

Problem: Phase 5A must establish empirically available objective data before
mechanics schema/features. Broad source coverage alone can conceal stale values,
missing-cell coercion, conditional effects and identity conflicts.

Evidence: 26 bounded public unauthenticated requests; fixed isolated catalog
108/106 Ranked-available; six pinned CSV tables plus public identity metadata.
107 source identity/ability mappings corroborated, Bolt quarantined for two
wrong-target gadget IDs. CSV blanks become false/zero in public JSON. Four exact
raw cells still match official pre-September-16 values. Build history exists
without verified effective intervals. Full 47-category/per-Brawler coverage and
reproducible field locators are committed in MECHANICS_* artifacts.

Decision: Phase 5A inventory complete; Phase 5B implementation gate NOT PASSED.
Count nonempty raw fragments independently from complete current mechanics.
Preserve base/attack/Super/equipment/Hypercharge/Buffy/Nano/form/summon paths,
source conflicts and unknown dependencies. Explicit zero/false is an observation;
blank/unknown never implies absent. All 108 current-qualified field values remain
UNKNOWN under this audit contract. Individual official patch change statements
are supported without becoming universal current functions or validity intervals.

Alternatives rejected: importing latest-fetch JSON as current; decoding engine
opcodes from intuition; assigning defaults/subjective ratings; dropping Bolt's
inconvenient gadgets; modern-to-historical backfill; reopening the old holdout.

Smallest proposed future schema: source snapshot, corroborated/quarantined
identity/ability link, scoped raw observation, separately sourced conditions and
nullable temporal claims. No final mechanics schema, migrations, formulas or
consumer added. Refer to MECHANICS_SOURCES for exact fields and remaining gates.

Validation: offline audit/hash/UNKNOWN/conditional/conflict/bounded traversal
tests plus existing catalog/provenance/frontier regressions. Exact final counts
are recorded in STATUS and DATA_AUDIT. No runtime engine change or data import.

Revisit only with bounded evidence resolving source freshness, identity, units,
opaque dependencies and availability. Historical mechanics additionally require
validity intervals and observed loadout context. New model work needs independent
preregistered data; the old holdout/shared-subset comparison remains final.


## D-010: Separate current explanation eligibility from numeric and historical mechanics

User clarification: a safe current mechanics subset may qualify without complete
historical reconstruction. Phase 5A at 33c570c stays complete; this is its bounded
source follow-up, not a rerun or speculative mechanics implementation.

Evidence: 21 public top-level fetches, 20 final HTTP 200/one 404, zero retries,
3,542,689 retained response bytes; one observed redirect, wire-hop count UNKNOWN.
Ten missing dependency tables reveal named statuses/traits/buddies/decks, explicit
AND predicates and ordered continuation values. Twelve roots are traversed with
six-edge/400-node caps; no effect execution. Only 1/57 components has ValueNames.
Mirror head/only branch unchanged; folder 69.230 and fingerprint 69.229.1 disagree.
BrawlAPI conditions generatedAt is September 1, not a server validity interval.
Bolt and Brock have explicit distinct TID translations and stable sampled IDs in
68.250/69.230; the current Bolt detail endpoint still includes Brock's gadgets.
Current official support separately supplies four narrowly usable gear statements.

Decision A: CONDITIONAL, limited pass for those four source-attributed current
explanations only, with explicit equipment/activation/context/as-of qualification.
The whitelist is MECHANICS_CURRENT_CLAIMS_2026-09-23.json. Unknown loadout cannot
become an active team capability; mode overrides stay UNKNOWN. Revalidate before
later reuse and invalidate affected claims on new/conflicting evidence. No old
validity interval is required merely to report a current documented statement.
Computed current composition mechanics remain PARTIAL / NOT PASSED because of
their own current baseline, unit and execution gaps, not because history is absent.

Decision B: historical training remains UNAVAILABLE / NOT PASSED. Null validity
boundaries are not an open-ended interval; retrieval/build dates cannot substitute
for server activation. Historical loadouts remain UNKNOWN; no new join/training.

Patch model: immutable source snapshot, scoped raw observation, separate reviewed
change event, explicit conditional/dependency graph, nullable precise validity and
conflict/use status. Exact replacement and relative-only event examples are saved;
none is applied to raw data. Calendar-day facts are preserved without invented UTC
midnights. Missing relative baselines stay unknown. Proposal is in MECHANICS_FOLLOWUP.

Rejected: universal opcode interpreter; tick/power/range conversion guessed from
plausibility or one fitted ratio; repairing Bolt by dropping inconvenient gadgets;
claiming server-only flags prove impossible completeness; blanket history barrier
for current facts; treating current explanation eligibility as model promotion.

Validation: new offline audit tests plus existing 5A regression contracts; exact
replay and tests recorded in STATUS. No DB, credential, match collection, Legacy,
holdout, model, schema or runtime consumer touched. Original 5A JSONs unchanged.

Next: a separately scoped current source-claim storage/explanation implementation
can use only the reviewed allowlist and contract; no automatic start in this
research task. Numeric mechanics require new evidence; historical work requires
its independent temporal/loadout evidence and future data protocol. Preserve all
completed probes and quarantine actual conflicts rather than requesting normal
milestone approvals or manufacturing missing facts.

## D-011 — archived explanations before current runtime reuse

User requested continuation after D-010. Choose a standard-library, offline,
content-addressed annotation archive, with the committed reviewed artifact digest
as the closed allowlist. This avoids silently promoting a dated support statement
to a present-day effect. All source fields, requirements and UNKNOWNs are retained.
Atomic publication never replaces existing records; modified artifacts fail
closed for review. Rejection is not a persisted conflict-resolution workflow.

Only archived source explanations are implemented. General source snapshots,
revision admission/quarantine resolution, fresh current use and Django consumers
remain separate work. Original publisher bodies are not copied or claimed present.
No numeric features, loadout inference, temporal joins or model changes. Validation:
31 offline tests; CLI archive/read replay. Usage: MECHANICS_CLAIM_ARCHIVE.md.

## D-012 — functional experimental challenger, separate from promotion

Latest user instruction prioritizes usable Last Pick and allows Train/Validation
experiments. Earlier blanket pauses on V2 integration are superseded; no automatic
promotion or old holdout evaluation. Mechanics work stays preserved and deferred.
Missing temporary model files are recovered by verifying the original ordered
membership digest via structural metadata, then loading only 6,094 Train and 2,031
Validation examples. SQL never selects holdout labels/teams; the complete membership
digest check uses eligibility predicates, including known-result status, only.
Training is read-only, deterministic and uses the already selected 300 epochs/L2 1.

Separate `/draft/challenger/` and `/draft/api/challenger/` opt in explicitly.
No change to Legacy endpoint/scoring. Model loader validates versions, finite
weights, feature/support alignment and catalog identities. Unknown maps fail closed;
unknown candidate main effects are reported unavailable. Probabilities carry
experimental/unknown-uncertainty labels and actual joint model contributions.
Support is number of training matches containing a feature, not causal evidence.

Validation: 35 focused model/search/API/recovery tests passed (7.134 s); real isolated
page/API smoke returned 200/200, 100 legal recommendations, 43.606 ms measured
service time in one request. This is a smoke timing, not a production percentile.
No live rollout, DB mutation, collector, mechanics features or held-out evaluation.

## D-013 — opponent interactions rejected by development validation

Fixed protocol D-012 tested antisymmetric cross-team pair coefficients jointly
with existing terms, L2 1/10/100, 300 epochs, learning rate 0.05. All three are
worse than the existing model on validation LogLoss and Brier. Keep the existing
artifact/runtime model; no opponent terms activated. Implemented version remains
an experimental candidate, not a learned mechanic or promoted feature.
12 model/explanation/runtime tests passed (0.677 s). Actual training times:
baseline 10.45 s; candidate fits 14.41/14.52/15.58 s. Full metrics/calibration and
unchanged development digests: CHALLENGER_OPPONENT_EXPERIMENT.json. No holdout
examples/outcomes/predictions, new split or mechanics facts. Do not enlarge the
grid after seeing results; move to usable search rather than tune indefinitely.

## D-014 — complete-state planning with bounded minimax

Every supported legal root candidate is evaluated. Later turns follow the existing
UI contract (1-2-2-1); invalid count/side combinations fail. Every model call is a
complete 3v3, never a partial composition. Width-three subsequent shortlists use
Train appearance support, explicitly not historical pick frequency or a validated
opponent distribution. Opponent minimizes and own team maximizes within the tree.
All legal unsupported candidates are reported unavailable; no mechanics invented.

Memoized canonical team states and a 30,000-leaf upper bound bound runtime. Exceeding
the budget fails the request rather than returning a biased partial ranking.
Output includes actual worst-in-shortlist continuation, hypothetical complete-team
contributions, remaining order, leaf count and omitted-branch count. These are
search facts, not proven tactical weaknesses or guarantees of a strongest response.

15 search/runtime tests passed (0.735 s). Real isolated constructed-draft smoke:
First 105 candidates / 8,452 evaluated leaves / 770.071 ms; Mid 102 / 900 / 92.893 ms;
Last 100 / 100 / 44.313 ms. One request each, not percentile/load-test evidence.
No gameplay quality claim or new model fit; V stays the D-012 artifact.

## D-015 — opt-in comparison and signed decision snapshots

Legacy comparison is an explicit request flag; calls the unchanged engine and
labels its heuristic scores separately from V2 probabilities. No quality inference
from rank agreement. Default endpoint stays unchanged.
Authenticated users may save a signed, owner-bound, two-hour decision snapshot
and chosen recommended pick. Saving does not re-run a changed model. Idempotent
unique snapshot key prevents duplicate writes; conflicting resaves are rejected.
Only the owner can list/read snapshots or update their self-reported outcome.
Recommendations remain immutable; user results are not verified match evidence.

Reuse Praxisfall with additive nullable unique snapshot_key and JSON metadata
(migration 0020). Legacy integer score remains null for V2 probabilities. Preserve
model version, artifact hash, complete response/provenance/search, draft state and
chosen rank. No ingestion, aggregates or trainer reads these rows. CSRF stays on.
55 API/Praxisfall/comparison tests passed (15.225 s), then 12 final Challenger tests
passed (1.595 s), including expiry/ownership/tampering/idempotence/private replay.
Schema drift check clean. Applied 0020 only to isolated DB; zero pre-existing
Praxisfall rows there, before/after legacy-field digests match. Legacy preservation
with populated snapshots is covered by existing tests, not claimed as a real-data
migration experiment. No production schema or server changes.

## D-016 — final product validation and scientific stop boundary

Problem: finish a usable experimental product without claiming stronger evidence
than the available development data supports. The remaining independent-test gate
cannot be satisfied by reopening the old holdout, unverified user outcomes or
invented mechanics. The fixed opponent feature experiment was negative.

Decision: retain the working selected V and all First/Mid/Last, comparison and
snapshot capabilities; keep Legacy default. Final UX exposes known model maps and
readable Brawler contribution labels. Enforce canonical Train/Validation content
hashes as well as frozen membership. Distinguish artifact byte hashes from canonical
JSON content hashes; reports preserve both and runtime uses the byte hash.

Validation: full Drafter 774 tests/four existing skips (336.643 s), protected Fitness
253 passed (138.720 s), final focused regression documented in STATUS. Real local
HTTP/CSRF/static/modelinfo/three-phase comparison passed; JavaScript parsed in V8.
No browser DOM/visual automation or production load claim. Legacy scorer files
match 3a565bd. Actual development content hashes reverified read-only without a fit.

Operational result: local preview on 127.0.0.1:18080, Traefik disabled, isolated DB,
no live services/credentials touched. Full report and exact start/stop/model rollback
commands in CHALLENGER_REPORT.md and CHALLENGER_RUNBOOK.md. No automatic promotion.
Revisit when independently sourced new eligible Ranked evidence can support a
preregistered future evaluation, not when another routine approval is obtained.


## D-017 — exact Legacy adapter and candidate-specific attribution
Use normal DraftEngine(ctx).als_dict() unchanged in the opt-in comparison,
including default recommendation depth/details. Existing 200/no-details adapter
already matched measured top scores; the reported external ranking remains
unreproduced, not attributed to a guessed cause. Expose resolved context, complete
pool, personal/configuration/loaded-data hashes and same-session endpoint check.
Partition the complete feature vector into root-candidate and background terms;
never predict partial teams. Explain relative additive contributions separately
from absolute composition effects. Inactive enemy interactions remain inactive;
UNKNOWN evidence is not a measured zero. Search continuation is hypothetical,
not a bonus. No independent tactical/causal attribution or uncertainty claim.
Validation and exact evidence: HIDEOUT_DIAGNOSTIC.md/.json. All ranking/model and
Legacy scoring functions unchanged. Scientific promotion gate remains closed.


D-018: reuse additive Praxisfall metadata for opt-in pre-choice capture and append-only user-report history under row lock. No migration or inferred choice/result. Both engine outputs persist; unsupported legal picks have null V2 rank. Shadow cohort remains self-selected, unverified and ineligible for automatic training/independent test. See SHADOW_EVALUATION.md for contracts and 19 passing tests.


D-019: keep self-selected shadow reports separate from official future soloRanked admission. Pure preregistration contract plus read-only temporal DB adapter, exclusive manifest publication, content/raw provenance hashes and verification without metrics. Minimum 1,000 is a preregistered operational floor, not evidence of power. No real registration until input lineage and frozen bundles are audited; current Legacy receipt is insufficient. Calendar dates remain unregistered rather than invented. Tests and actual cooldown evidence: FUTURE_EVALUATION_PROTOCOL.md.
