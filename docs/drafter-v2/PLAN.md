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
6. Phase 5: strukturierte, versionierte Rohmechaniken, deterministische Ableitungen und validierte strategische Konzepte strikt trennen. **Architektur präzisiert; Quellen-/Coverage-Gate vor Implementierung offen.**
   Phase 6: bedingte und patchbezogene Kompositions-Matchups, jede Interaktionshypothese separat ablatierbar. **Keine aktive Featureauswahl ohne neue Evaluation.**
   Phase 7: Faktorisierung nur bei empirisch belegtem Bedarf; keine automatische Erweiterung.
7. Phase 8-9: legaler Last-Pick aus V, dokumentierte Mid-/First-Search, faktenbasierte Erklärungen. **Prototypen vorhanden; nicht akzeptiert, solange V nicht validiert ist.**
8. Phase 10-11: explizite Modellversion in API/UI und modellversioniertes Draft-Logging; Legacy bleibt verfügbar.
9. Phase 12: Collector-Runbook bzw. begrenzter Lauf nur nach Sicherheits-/Rate-Limit-Prüfung.
10. Phase 13-14: Regressionen, Gesamtbericht, Rollback, Status und Abschlussdokumentation.

Nach jedem Milestone: fokussierte Tests, Fehlerbehebung, Dokumentation, kleiner Commit, `STATUS.md` aktualisieren. The existing holdout and shared-subset report are final. Do not rerun selection on that freeze.

## Current continuation
- Preserve and verify the interrupted Phase-12 collector audit; do not repeat its completed runs.
- Read-only growth report implemented in `896ec90`; continue using the fixed exclusive cutoff `2026-09-18T15:04:42Z`. No training, evaluation, or new split.
- Run relevant regressions and commit/push the safe milestone.
- Isolated credential loading succeeded for collector run 4. Collection is now blocked by absent player-tag/rank provenance for `broad_high_rank`, not credential inheritance. Never retrieve live data or reconstruct anonymized identities.
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
