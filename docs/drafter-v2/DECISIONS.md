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
