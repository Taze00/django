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
6. Phase 5-7: Mechanik-/Teamfeatures und faktorisierte Interaktionen nur bei belegtem Nutzen; sonst als verworfen dokumentieren. **Nur Bestands-Pipeline inventarisiert; aktive Featureauswahl blockiert.**
7. Phase 8-9: legaler Last-Pick aus V, dokumentierte Mid-/First-Search, faktenbasierte Erklärungen. **Prototypen vorhanden; nicht akzeptiert, solange V nicht validiert ist.**
8. Phase 10-11: explizite Modellversion in API/UI und modellversioniertes Draft-Logging; Legacy bleibt verfügbar.
9. Phase 12: Collector-Runbook bzw. begrenzter Lauf nur nach Sicherheits-/Rate-Limit-Prüfung.
10. Phase 13-14: Regressionen, Gesamtbericht, Rollback, Status und Abschlussdokumentation.

Nach jedem Milestone: fokussierte Tests, Fehlerbehebung, Dokumentation, kleiner Commit, `STATUS.md` aktualisieren. The existing holdout and shared-subset report are final. Do not rerun selection on that freeze.

## Current continuation
- Preserve and verify the interrupted Phase-12 collector audit; do not repeat its completed runs.
- Add a read-only growth report restricted to API matches played strictly after `2026-09-18T15:04:42Z`. No training, evaluation, or new split.
- Run relevant regressions and commit/push the safe milestone.
- Further collection requires an API credential supplied independently to the isolated environment. Never retrieve it from the live checkout.
- Before any future experiment, preregister a new temporal protocol and training-only statistical inputs. New observations alone do not establish adequate sample size or promotion readiness.
- Phase 10 V2 integration remains gated, not completed; the existing Legacy API/UI and Praxisfall logging have regression coverage.
- Operational commands, budgets and stop conditions: `COLLECTION_RUNBOOK.md`.
