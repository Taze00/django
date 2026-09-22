# Drafter V2 Status

Overall:
- Completed milestones: 3 / 10
- Current phase: Phase 3/4 evidence evaluation
- Current task: complete unchanged Legacy benchmark, then perform one sealed final comparison
- Blocker: none for data access; Legacy benchmark is still running in the isolated container

Latest validation:
- Git status: calibration fix pending commit; snapshot/freeze commit `d58c4f9` is pushed
- Branch: `feature/drafter-v2`
- Live Compose `alex-django`: läuft separat unter `/media/docker/alex-django`
- Testbaseline: 680 Drafter-Tests, 4 übersprungen, 0 Fehler, 237.054 s; Systemcheck ohne Befund
- Aktuelle Vollsuite: 690 Drafter-Tests, 4 übersprungen, 0 Fehler, 234.768 s
- Fitness-Cross-App-Suite: 253 Tests, 0 Fehler, 5.726 s
- V2-Audit-Test: 1 Test, 0 Fehler
- V2-Datenaudit: 10,162 countable soloRanked matches, 10,191 soloRanked total; 0 conflicts and 0 reconstructed-fingerprint duplicates
- V2-Evaluationsvertrag: 5 Tests, 0 Fehler; Duplicate-Fingerprint- und Split-Grenzen geprüft
- V2-Evaluationscommand: 10,158 eligible; train 6,094, validation 2,031, holdout 2,033; fingerprint digest recorded in `EVALUATION.md`
- Baselines: B0 holdout LogLoss 0.693147; B2 0.704446; B3 0.730888; B4 0.772412; B5 0.717746
- V2-Modellvertrag: 4 Tests, 0 Fehler; validation LogLoss 0.688604, preliminary holdout 0.692603; not promoted
- Mechanik/UNKNOWN/Search: 14 fokussierte Tests, 0 Fehler; Last Pick und Mid-Expectimax nicht-aktiv verfügbar
- V2-Erklärung: 1 fokussierter Test, 0 Fehler; nicht in API/UI aktiv
- API audit: bounded HTTP 200 audit completed; unsupported fields remain UNKNOWN
- Legacy-Abbildung: unchanged engine benchmark still running; duplicate-Brawler rows are counted as skipped

Data integrity:
- fabricated values: 0
- destructive operations: 0
- unresolved gaps: Pickorder, Bans, Builds, Kampfstatistiken und valide Skillkontrolle UNKNOWN; objektive Patchmechanikwerte UNKNOWN; Legacy benchmark pending

Next:
- RESUME FROM: Phase 3 / unchanged Legacy benchmark result, then sealed final comparison.
- V2-Modell, Search und Erklärung nicht aktivieren; keine Holdout-basierte Nachjustierung.
