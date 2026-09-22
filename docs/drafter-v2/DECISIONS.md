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
