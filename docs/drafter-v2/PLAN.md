# Drafter V2 Plan

## Sicherheitsgrenzen
- Arbeitsroot: `/home/alex/alex-django-drafter-v2`, Branch `feature/drafter-v2`.
- Live-Checkout `/media/docker/alex-django` und dessen Compose-Projekt `alex-django` bleiben unberührt.
- Entwicklungscontainer nur mit eigenem Compose-Projektnamen `drafter-v2-isolated`; vor Lauf prüfen, dass `data/` im Worktree weder Symlink noch Mount auf `/media/docker/alex-django` ist.
- Keine API-, Collector- oder Datenbankläufe, bevor DB- und Rawpayload-Pfade isoliert dokumentiert sind.

## Milestones und Acceptance Criteria
1. Phase 0: Repo-Karte, Schutzbereiche, Baseline, Legacy-Stand dokumentiert.
2. Phase 1: DB-/Rawpayload-/API-Audit mit reproduzierbaren Queries, UNKNOWN-Lücken und Sampling-Befund. **Erledigt in `54d8e18`.**
3. Phase 2: eingefrorener zeitbasierter Split, Baselines B0-B5, Log-Loss/Brier/Kalibrierung, Leakage-Prüfungen und Runner. **Historical freeze and baseline measurements complete; sealed and closed to further tuning. See EVALUATION.md.**
4. Phase 3: Legacy auf identischem Holdout benchmarken; keine Legacy-Scoringänderung. **Erledigt in `5c3d7bf`; Recorded metrics favor Legacy; statistical-input timing limitation documented in EVALUATION.md.**
5. Phase 4: regularisiertes probabilistisches V-Modell, Manifest, Persistenz, Training/Evaluation und Model Card. **Kandidat evaluiert, aber nicht promotet; Legacy bleibt Default.**
6. Phase 5: strukturierte, versionierte Rohmechaniken, deterministische Ableitungen und validierte strategische Konzepte strikt trennen. **Phase 5A und begrenzte Folgeprüfung abgeschlossen (D-010); aktuelle quellengebundene Erklärungen eingeschränkt freigegeben, numerische/historische Mechaniken weiter gesperrt.**
   Phase 6: bedingte und patchbezogene Kompositions-Matchups, jede Interaktionshypothese separat ablatierbar. **Keine aktive Featureauswahl ohne neue Evaluation.**
   Phase 7: Faktorisierung nur bei empirisch belegtem Bedarf; keine automatische Erweiterung.
7. Phase 8-9: legaler Last-Pick aus V, dokumentierte Mid-/First-Search, faktenbasierte Erklärungen. **Prototypen vorhanden; nicht akzeptiert, solange V nicht validiert ist.**
8. Phase 10-11: explizite Modellversion in API/UI und modellversioniertes Draft-Logging; Legacy bleibt verfügbar.
9. Phase 12: Collector-Runbook bzw. begrenzter Lauf nur nach Sicherheits-/Rate-Limit-Prüfung.
10. Phase 13-14: Regressionen, Gesamtbericht, Rollback, Status und Abschlussdokumentation.

Nach jedem Milestone: fokussierte Tests, Fehlerbehebung, Dokumentation, kleiner Commit, `STATUS.md` aktualisieren. The existing holdout and shared-subset report are final. Do not rerun selection on that freeze.

## Current continuation
- Preserve completed Phase-12 runs 1–5. Tagged bootstrap (D-008) is complete; do not repeat it or the empty broad run.
- Read-only growth report implemented in `896ec90`; continue using the fixed exclusive cutoff `2026-09-18T15:04:42Z`. No training, evaluation, or new split.
- Run relevant regressions and commit/push the safe milestone.
- The independent tagged-frontier bootstrap is complete (run 5, D-008). Three genuine ranking seeds persist; zero new soloRanked observations. Historical broad provenance remains unavailable. Never retrieve live data or reconstruct anonymized identities.
- Before any future experiment, preregister a new temporal protocol and training-only statistical inputs. New observations alone do not establish adequate sample size or promotion readiness.
- Phase 10 V2 integration remains gated, not completed; the existing Legacy API/UI and Praxisfall logging have regression coverage.
- Operational commands, budgets and stop conditions: `COLLECTION_RUNBOOK.md`.


## Phase 5/6 architecture gates (user clarification, 2026-09-23)

The normative contracts are master prompt sections 12, 13 and 15. This plan
adds acceptance criteria and dependencies; it does not assert mechanic values.

| Milestone | Deliverable / acceptance | Dependency and validation |
|---|---|---|
| 5A Sources and coverage inventory | Establish accessible official/API/game sources, official patch notes, then reliable structured public data and documented cross-checks. Record source/date, retrieval date, patch/version, raw/normalized values and coverage denominators. | Do not implement speculative mechanics or fill facts from LLM knowledge. Missing sources/fields remain UNKNOWN in DATA_GAPS. |
| 5B Versioned mechanics contract | Raw records identify ability/form/summon, typed value/unit/context and provenance. Separate base attack, Super, Gadget, Star Power, Hypercharge, transformation and summon effects. Preserve conditional, requires_* dependencies, limited uses, repeatability and activation conditions. | Source/coverage gate 5A first. Proposed tests: unknown vs false, multiple requirements, conditional gadget-only wallbreak, patch validity and source conflicts. No unconditional flattening. |
| 5C Deterministic derivations | Versioned formulas/input lineage for sustained DPS, burst, effective HP, high-HP damage, range, sustain/shields, CC, wallbreak reliability, mobility/access, multi-target damage and thrower access where inputs support them. | Every quantitative feature has a documented formula or a validated learned model; units, assumptions and missingness propagate. No subjective anti_tank/thrower_counter/safe_pick/flexibility ratings. |
| 5D Coverage audit | Reproducible command reports per-Brawler raw/conditional/UNKNOWN mechanics, source and patch; global coverage per mechanic, UNKNOWN share, source and patch distributions. | Freeze the queried Brawler/field universe and report denominators. Separate ability existence, historical loadout and actual availability. Command/schema implementation waits for 5A. |
| 6A Matchup hypotheses | Register concrete team capability versus opponent win-condition/defense hypotheses; include all seven interactions listed in master section 13. Document terrain/context requirements and unresolved gaps/redundancies. | No role-count shortcut, arbitrary bonuses, inferred map geometry or invented historical builds. Individually strong picks may fall only through validated resulting composition quality. |
| 6B Independent ablations | Each interaction independently togglable/versioned, with train/validation selection, leakage/symmetry/calibration checks and a new sealed test window. | Phase 5 inputs, trustworthy V and preregistered new data required. Historical holdout and final shared subset stay closed. |
| 8 State-based decisions | First/Mid/Last evaluate candidate-created states through V/search, including resolved/open/new weaknesses, plausible opponent answers and completed compositions. | Explanations tied to actual terms/search. Conditional loadouts stay conditional; no separate handcrafted candidate score. |

Full mechanics vocabulary includes HP; damage/projectile counts/damage instances;
reload/ammo/range; movement/projectile speed; pierce/splash-AOE/bounce/percentage-HP
damage; healing/shield/damage reduction; slow/stun/knockback/pull/silence/root;
dash/jump/teleport; wallbreak/wall penetration/over-wall attacks; summons,
transformations and Super/Gadget/Star-Power/Hypercharge effects. Availability is
not assumed from this requested scope. Modern values are not backfilled into
historical matches. Unknown equipped loadouts remain UNKNOWN even if ownership
or a possible kit effect is known.

Completed in this milestone: architecture clarification and source/coverage
acceptance gates. Not implemented: a new mechanics schema, values, coverage
command, strategic ratings or new model features. Existing regression commands
are in COLLECTION_RUNBOOK.md; future mechanics tests are acceptance criteria,
not claims that the existing Legacy tests validate this new architecture.


## Phase 12B: tagged-frontier bootstrap (authorized 2026-09-23)

1. Add opt-in persistent TaggedPlayer membership and append-only observations,
   linked to existing shared cooldowns and RawPayload/CollectorRun provenance.
2. Reuse verified official global trophy-ranking tags; distinguish seed evidence
   from observed soloRanked graph edges. Preserve queried identities/raw tags,
   never infer tags for the anonymized history or treat trophies as skill.
3. Enforce one ranking attempt, three seeds, at most five battlelog HTTP attempts
   including retries, one new request hop per run, six-hour revisits and no hidden
   catalog fetch. Save boundary tags for future runs; no recurring job.
4. Run focused/regression tests, review additive migration 0019, persist the exact
   pre-experiment resume point and commit implementation. Apply only to isolation.
5. Run one bounded experiment, then read-only frontier/inventory/new-growth audits.
   Record actual HTTP/retry/seed/discovery/match/duplicate/frontier counts. If no
   eligible new Ranked data appears, record DATA_UNAVAILABLE and stop collection.
6. Commit and push evidence. Next independent work remains Phase 5A source/coverage
   inventory; no old holdout, reaggregation, model tuning or engine promotion.


Phase 12B result: all six implementation/experiment/documentation steps completed.
Implementation 8661c29 pushed; migration applied only to isolation. Run 5 made four
HTTP 200 requests (ranking + three battlelogs), persisted three seeds, imported
50 unique trophy matches and obtained zero new eligible soloRanked or frontier
neighbors. DATA_UNAVAILABLE; no larger/second run. Read-only audits and exact
regression results are committed in BOOTSTRAP_EXPERIMENT_2026-09-23.json.
At that milestone the next task was Phase 5A, now completed below. Model
selection, new freezes, V2 integration and promotion remain gated; Legacy stays default.


## Phase 5A result (2026-09-23, D-009)

Completed allowed-source register, fixed 108-Brawler catalog, 47-category raw/
conditional/UNKNOWN coverage, per-Brawler source/field witnesses, small diverse
verification sample and four official-patch drift checks. Offline standard-library
audit utility reads pinned CSVs and committed minimized identities only; no DB,
network or runtime import. Sources, exact reproduction and smallest future schema
proposal: MECHANICS_SOURCES.md. Output: MECHANICS_COVERAGE.md and MECHANICS_* JSON.

**5B NOT PASSED:** raw fragments do not establish current patch, normalized units,
complete condition graphs or historical validity. Do not implement 5B/5C or model
features from this inventory. No change to master prompt needed: D-006 already
requires precisely this evidence gate and separation.

Next independent research scope, if continued: document a small bounded probe of
missing status/component/buddy/gear/deck definitions; seek current source/hotfix
evidence and authoritative units; resolve Bolt conflict without guessing. Preserve
this dated inventory and add new snapshots instead of changing its denominator or
source hashes. Gate can be revisited only after evidence supports a narrowly
specified contract. Historical loadout/time gaps and new Ranked DATA_UNAVAILABLE
remain separately blocking model work. No follow-up collection is part of 5A.


## Bounded source follow-up result (D-010, after 33c570c)

Complete: focused currency/units/dependency/Bolt investigation and patch-event
contract proposal. Original 5A inventory frozen; no new roster coverage run.
Sources, budget accounting limitation, exact replay and classifications are in
MECHANICS_FOLLOWUP.md and MECHANICS_FOLLOWUP_* evidence artifacts.

| Next gate / workstream | State and acceptance |
|---|---|
| A: Current factual explanations | CONDITIONAL limited pass for four official gear claims; source/as-of, equipment/context, unknown mode overrides and future revalidation required. Historical reconstruction is not a prerequisite. |
| A: Computed current mechanics/features | NOT PASSED; current baseline, unit and behavior evidence missing for requested broad composition reasoning. A smaller independently evidenced subset may qualify later. |
| B: Historical mechanics features | NOT PASSED; effective UTC intervals and observed loadouts absent. No timestamp join, old holdout or training. |
| Patch/source claim contract | Design complete, not implemented: snapshots, raw scopes, change events, nullable temporal validity, conditions/dependencies, conflict status and independent usage flags. |

Do not start schema/features automatically from this source-research task. A next
implementation task may narrowly build source-claim/provenance storage and
conditional attributed explanations, using only the D-010 allowlist. Numeric
mechanics require source evidence first; a universal interpreter is unjustified.
Normal implementation failures can be fixed autonomously, but missing units,
server validity or loadouts must remain UNKNOWN. Preserve prior runs/probes;
no additional collection or replay of the sealed comparison is part of this plan.

## D-011 result: offline reviewed claim archive

The continuation implements a narrow first storage milestone for the four D-010
annotations. Source research remains complete. Exact-byte, content-addressed
storage and dated conditional explanations are available through
`drafter.services.v2_mechanics_claims`; see MECHANICS_CLAIM_ARCHIVE.md.
This is not general Phase 5B or a current-state consumer. Next: a separately bounded
revalidation protocol and reviewed revision/conflict contract before current use.

## Active autonomous continuation — D-012 (supersedes earlier research pauses)

The latest user instruction authorizes experimental product integration and
Train/Validation-only development. Promotion and the sealed holdout stay gated.
1. DONE: opt-in `/draft/challenger/`, Last-Pick API, safe artifact loader and
   development-only trainer. Existing 300-epoch model reproduced on Train/Validation.
2. NEXT: D-013 bounded opponent-interaction experiment in CHALLENGER_PROTOCOL.md.
3. Then complete-composition Mid/First planning with explicit approximation bounds.
4. Then experimental side-by-side Legacy comparison and versioned draft snapshots.
5. Broad regressions, operational documentation, honest final evidence limitations.
Continue after test/document/commit/push; no routine milestone approval.

D-013 complete: fixed opponent-interaction experiment produced no validation
improvement; retain existing V. Next D-014: bounded full-composition Mid/First
planning, followed by side-by-side UI and snapshots. No more mechanics research
or unbounded hyperparameter search on this validation set.

D-014 complete: usable experimental First/Mid/Last UI/API. Last exhaustive over
supported legal pool; earlier phases bounded minimax over complete 3v3 outcomes.
Next D-015: opt-in side-by-side Legacy output, immutable versioned snapshots,
then full regression and operational handoff. Promotion remains evidence-gated.

D-015 complete: optional side-by-side Legacy output and authenticated, signed,
versioned Praxisfall snapshots with later self-reported result and private replay.
Next: whole Drafter/protected Fitness regression, actual HTTP/static smoke,
operational handoff and precise remaining scientific promotion gate.

## D-016 final autonomous product checkpoint

Experimental product priorities 1/3/4/5 are functional: Last Pick, Mid/First planning,
side-by-side comparison and snapshots. Priority 2 was tested with the fixed
Train/Validation experiment; no better model found, retain existing V. Priority 6
remains evidence-gated; completed mechanics research is not reopened.

Phases 8–11 are complete as an explicitly experimental surface, not as promoted
validated gameplay policy. Phase 13 regressions and Phase 14 honest report are
complete; see CHALLENGER_REPORT.md. Independent future outcome evidence blocks
promotion/quality claims. Do not re-tune the sealed holdout or run more research
merely to avoid acknowledging that scientific gate. Exact operations and rollback:
CHALLENGER_RUNBOOK.md. Legacy remains default and data remain preserved.


## D-017 diagnostic follow-up complete
Concrete Hideout parity and additive explanation are implemented and tested;
see HIDEOUT_DIAGNOSTIC.md. No ranking tuning/retraining or new mechanics.
The existing experimental phase completions and independent-evidence gate stand.


D-018 complete: opt-in pre-choice shadow persistence and audited reports. Next D-019: future-only protocol, immutable membership and eligibility safeguards; then bounded frontier readiness audit. No routine approval pause.


D-019 complete: future-only protocol/membership preparation, atomic publication and integrity verification. No real registration/test seal. Collection blocked by zero due frontier players at audit; future evaluation blocked by absent new eligible Ranked evidence. Before arming, verified Train-only Legacy bundle and prospective dates are required. See FUTURE_EVALUATION_PROTOCOL.md.


D-020 complete: exactly one authorized zero-seed frontier revisit, run 6, DATA_UNAVAILABLE; no immediate retry. Next frozen Legacy bundle lineage audit.


D-021 exact bundle prerequisite BLOCKED_PRIOR_LINEAGE. Verified pinned Train contents, but current overlay includes 137 hand-set demo priors. No bundle/window publication. Read LEGACY_TRAIN_BUNDLE.md; explicit input-policy resolution is required before empirical rebuild and independent replay can establish a fair frozen baseline.


D-022: explicit prior policy permits unchanged pre-existing B constants. Build the empirical A statistics from pinned Train in two independent scratch databases; independently check raw counts/membership, then replay archived tables without observations. Register no future window before successful receipt. Working Challenger remains usable, Legacy default.


D-022 result: VERIFIED bundle 23069ec9ec9cbbc8b7475e590c18e9548c4666395834886e12c0cd8436830527. 94,302 empirical rows from 6,094 Train; 137 identical B priors; two identical builds, independent all-row counts/membership and 28 archive-only scoring replays passed. 20 focused tests passed (4.342 s). No future window registered; independent soloRanked evidence remains unavailable in the latest collection report. Exact contracts/limits: LEGACY_BUNDLE_RUNBOOK.md and verification/artifact JSONs.


D-023 current continuation: test the separate observed-tag query frontier, commit the preregistered single acquisition pilot, execute once within ten total battlelog attempts, audit feasibility. Do not register a prospective window until the gate passes.


D-023 pilot completed (run 7, 2026-09-24T16:22:13Z–16:24:00Z): acquisition feasibility demonstrated. Ten battlelog HTTP 200, zero retries/ranking requests. 340 authentic observed query roots; 250 raw entries: 201 trophy ranked, 33 soloRanked, 16 type UNKNOWN. Parser retained all 33 soloRanked; 60 unsupported/non-3v3 entries skipped, zero parser errors or future-dated records. 185 newly imported matches: 152 trophy and 33 eligible soloRanked; five trophy duplicates, zero conflicts. 1,031 additional query tags; discovery frontier 1,371, eligible Ranked-evidence frontier 56. Independent raw/parser/import audit agrees. Pilot matches remain permanently excluded from future test membership and automatic training.


D-024: 59 collector/future/bundle/growth regressions passed. Common-subset preflight is 28 map/mode pairs, 106 Brawlers; all 33 pilot Ranked matches fit. Commit frozen acquisition implementation, then atomically preregister dates/code/artifacts and preserve the temporal gate.
