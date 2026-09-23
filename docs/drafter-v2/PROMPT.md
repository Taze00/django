# Drafter V2 Spezifikation

Verbindliche Quelle: `CODEX_DRAFTER_V2_MASTER_PROMPT.md` im Repository; Ausgangsfassung Commit `639b5a0` (22.09.2026), ergänzt um die Nutzerpräzisierung für strukturierte bedingte Mechaniken und Kompositions-Matchups vom 23.09.2026 (DECISIONS D-006). Dieses Dokument hält den für die Implementierung relevanten Scope fest: Legacy bleibt unverändert und benchmarkbar; V2 bewertet vollständige Teamkompositionen probabilistisch; Draft-Entscheidungen verwenden V; unbekannte Daten bleiben UNKNOWN; alle Ergebnisse müssen zeitlich gesplittet, reproduzierbar und ohne Leakage evaluiert werden.

Phasen: Repository/Baseline, Daten- und API-Audit, Evaluationsframework, Legacy-Benchmark, Bewertungsmodell V, objektive Mechanikdaten, Teamfeatures, faktorisierte Interaktionen nur bei Bedarf, Draft-Search, Erklärungen, UI/API, Logging, Collector, Regressionen und Abschlussbericht.

Nicht verhandelbar: keine erfundenen Werte, keine produktiven Datenänderungen, keine Löschung von Rawpayloads, keine Änderung anderer Apps ohne Notwendigkeit, kein Default-Wechsel ohne Holdout-Nachweis und Rollback.
