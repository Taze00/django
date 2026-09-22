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
