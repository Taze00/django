# CODEX MASTER TASK — Brawl Stars Draft Coach V2

## Rolle und Arbeitsmodus

Du arbeitest in einem bereits existierenden, produktiv genutzten Multi-App-Django-Repository. Der Bereich `drafter` ist nur ein Teil der Website. Andere Apps und Seiten dürfen nicht unbeabsichtigt verändert oder beschädigt werden.

Deine Aufgabe ist **kein einzelner Bugfix**. Du sollst das bestehende Brawl-Stars-Draft-Coach-Projekt vom aktuellen Stand aus systematisch evaluieren und eine neue, empirisch validierbare V2-Architektur entwickeln, integrieren, testen und dokumentieren.

Arbeite autonom über mehrere Phasen hinweg. Beende die Arbeit **nicht** nach einer Analyse oder einem Plan. Nach der initialen Orientierung sollst du implementieren, testen, validieren, Fehler beheben, dokumentieren und committen, bis alle erreichbaren Meilensteine und Acceptance Criteria erfüllt sind.

Der aktuelle Plan ist eine Arbeitshypothese, kein Dogma. Wenn reale Daten eine Annahme widerlegen, darfst und sollst du die spätere Umsetzung anpassen. Dokumentiere jede solche Entscheidung nachvollziehbar.

Zeit ist kein Abbruchkriterium. Ein längerer Lauf ist ausdrücklich akzeptiert.

---

# 0. Oberstes Ziel

Baue einen möglichst starken und erklärbaren Brawl-Stars-Ranked-Draft-Coach.

Der Coach soll langfristig nicht bloß einzelne Brawler nach handgesetzten Scores sortieren, sondern die Qualität einer **gesamten möglichen Teamkomposition** bewerten und daraus für den aktuellen Draftzustand den sinnvollsten Pick ableiten.

Langfristige Zielgröße:

```text
P(Sieg | Map, Modus, Patch, eigenes Team, Gegnerteam, Skill-/Kontextinformationen)
```

Für frühe Draftphasen soll zusätzlich berücksichtigt werden, welche realistischen Antworten des Gegners noch folgen können.

Das System soll dabei echte Matchdaten verwenden, Unsicherheit korrekt behandeln, keine erfundenen Statistiken benutzen, objektive Mechaniken von subjektiver Einschätzung trennen, vollständige Teamkompositionen statt nur Einzelbrawler betrachten, verständlich erklären können, warum ein Pick empfohlen wird, messbar gegen Baselines evaluiert werden und die bestehende Website sowie andere Django-Apps nicht beschädigen.

---

# 1. Nicht verhandelbare Regeln

## 1.1 Keine erfundenen Daten — FAIL CLOSED

Niemals Statistiken erfinden, fehlende Samples simulieren und als echte Daten behandeln, 0–100-Werte für Brawlerfähigkeiten raten, LLM-Wissen als Datenbankfakt ausgeben, fehlende API-Felder durch plausible Werte ersetzen oder nicht belegte Matchups als gemessen darstellen.

Wenn Daten fehlen:

1. Prüfe vorhandene Datenbank, RawPayloads, existierenden Code und tatsächlich erreichbare offizielle API-Antworten.
2. Prüfe externe Quellen nur, wenn der jeweilige Meilenstein dies ausdrücklich erlaubt.
3. Wenn der Wert nicht belastbar verfügbar ist, markiere ihn als `UNKNOWN` / `UNAVAILABLE`.
4. Dokumentiere die Lücke in `docs/drafter-v2/DATA_GAPS.md`.
5. Wenn ein Meilenstein ohne diese Information nicht seriös fortgesetzt werden kann, markiere ihn als `BLOCKED`.
6. Erfinde niemals einen Ersatzwert, um einen Test oder Meilenstein künstlich grün zu bekommen.

Alle wichtigen Zahlen in Berichten müssen reproduzierbar sein. Dokumentiere bei zentralen Messwerten Quelle, Zeitraum/Patchfenster, Filter, Anzahl Beobachtungen, reproduzierbaren Query-/Command-/Script-Pfad und Git-/Modellstand.

## 1.2 Bestehende Nutzerdaten schützen

Verboten:

```text
rekursives chmod/chown auf /code/data
Ownership-Änderungen an /code/data/data/db
Löschen/Reset bestehender DB-Daten, um Tests zum Laufen zu bringen
Löschen vorhandener RawPayloads
unbegründete destructive migrations
```

Insbesondere:

```text
NEVER recursively chmod/chown /code/data
NEVER alter ownership of /code/data/data/db
NEVER reset/delete the database to fix an application problem
```

Wenn Migrationen nötig sind, bevorzuge additive/reversible Migrationen und erhalte historische Daten.

## 1.3 Andere Website-Bereiche schützen

Das Repository enthält mehrere Django-Apps / Webseiten.

Primärer Scope:

```text
drafter/**
drafter-bezogene Templates/Static-Dateien
drafter-bezogene Tests
docs/drafter-v2/**
```

Shared-Dateien wie Settings, Projekt-URLs, Base Templates, Docker-Konfiguration oder gemeinsame Utilities dürfen nur verändert werden, wenn dies für den Drafter zwingend nötig ist. Andere Apps gelten zunächst als protected/out of scope. Ermittle die tatsächlichen Grenzen in Phase 0 selbst.

## 1.4 Legacy bleibt erhalten

Die existierende Engine wird nicht überschrieben. Sie ist die **LEGACY / FROZEN BASELINE**.

Die neue Architektur entsteht parallel oder hinter einer Model-/Feature-Version-Grenze. Der Legacy-Stand muss reproduzierbar und benchmarkbar bleiben. Keine weiteren lokalen Reparaturen am Legacy-Scorer nur wegen einzelner auffälliger Picks.

## 1.5 Nicht auf Einzelpicks optimieren

Praxisfälle sind Regression/Plausibilitätsprüfungen, kein Trainingsziel.

Nicht:

```text
Pam muss runter
El Primo muss hoch
Gale darf nicht #1 sein
Tick muss schlechter sein
```

Stattdessen allgemeine Hypothesen formulieren, auf Holdout-Daten messen und nur behalten, wenn sie allgemein helfen.

## 1.6 Tests nicht passend machen

Wenn ein Test scheitert, zuerst prüfen, ob er einen weiterhin gültigen Vertrag schützt. Tests nur ändern, wenn die neue Spezifikation den alten Vertrag bewusst ersetzt; Semantikänderung dokumentieren.

---

# 2. Aktueller fachlicher Stand — Kontext, nicht ungeprüfte Wahrheit

Repository und Datenbank sind Source of Truth. Zahlen hier sind Kontext und müssen verifiziert werden.

Bekannter Stand ungefähr:

```text
106 Ranked-verfügbare Brawler
10.000+ gespeicherte Ranked-Matches
mehrere tausend bekannte Spieler
Raw API Payloads
Patch-/Zeitfenster
Counter-/Synergy-Aggregationen
Praxisfall-System
Analysemodus für beliebige Brawler
```

Legacy-Komponenten umfassen ungefähr:

```text
Current Strength
Objective Fit
Map & Modus
Counter
Synergy
Team Need
Draft Position
Flexibility
Redundancy
Angreifbarkeit / Exploitability
Personal
Data / Statistical Confidence
```

Historisch existierten 32 strategische Attribute. Nur etwa 20 Brawler hatten alte Demo-Profile; diese waren handgepflegte Schätzwerte, keine Messdaten.

Bereits umgesetzt wurden unter anderem:

```text
Unknown != 0
alte Demo-Draftwerte deaktiviert
Mechanik/Fachquelle/Messung/Demo/Unknown getrennt
Teamprofil kennt known/total
Team Need berücksichtigt Wissensabdeckung
Portrait-Normalisierung
Counter-/Synergy-Hierarchie
Patchverwaltung
Bayesian/Shrinkage-Logik
```

Der jüngste Legacy-Counter-Ansatz normalisiert Counter feldrelativ ungefähr als:

```text
0.6 * relative Position im Feld + 0.4 * Rohwert
```

Praxistests zeigten, dass sehr schwache/unsichere Pair-Evidenz dadurch stark verstärkt werden kann. Beispiele wie GALE/TICK mit sehr niedriger Pair-Confidence erhielten große Counter-Beiträge.

**Nicht weiter lokal am Legacy-Scorer tunen. Er wird objektiv benchmarked.**

---

# 3. Neue Leitidee

Trenne zwei Probleme.

## Bewertungsfunktion V

```text
V(map, mode, patch, team_a, team_b, context)
    -> geschätzte Sieg-Wahrscheinlichkeit Team A
```

## Entscheidungsproblem

```text
Welcher legale Pick führt unter realistischen folgenden Antworten
zur besten erwarteten Endkomposition?
```

Last Pick:

```text
argmax Kandidat V(fertige Komposition)
```

Frühere Picks:

```text
kleine Search-/Planning-Schicht über verbleibende Picks
```

First-Pick-Sicherheit, Flexibilität und Counterability sollen möglichst aus möglichen gegnerischen Antworten entstehen statt aus Handgewichten. Counter, Synergy, Map/Mode und Team-Composition dürfen Features von V sein. Gewichte sollen, wo sinnvoll, aus Daten gelernt werden.

Diese Leitidee darf verändert werden, wenn Evaluation klare empirische Gründe liefert.

---

# 4. Persistentes Projektgedächtnis

Lege zu Beginn an:

```text
docs/drafter-v2/
    PROMPT.md
    PLAN.md
    STATUS.md
    DECISIONS.md
    DATA_GAPS.md
    REPO_MAP.md
    DATA_AUDIT.md
    EVALUATION.md
    MODEL_CARD.md
```

`PROMPT.md`: Spezifikation.
`PLAN.md`: konkrete Meilensteine, Acceptance Criteria, Commands, Abhängigkeiten.
`STATUS.md`: Gesamtfortschritt, aktive Phase, Tests, Commits, Blocker.
`DECISIONS.md`: Architekturentscheidungen und empirische Begründung.
`DATA_GAPS.md`: fehlende/unzuverlässige Daten und legitime Beschaffungswege.
`REPO_MAP.md`: Multi-App-Struktur und protected scopes.
`DATA_AUDIT.md`: Datenbestand und API-Befund.
`EVALUATION.md`: Splits, Baselines, Metriken, Ergebnisse.
`MODEL_CARD.md`: finales aktives V2-Modell, Features und Grenzen.

Nach jedem abgeschlossenen Meilenstein:

```text
Tests/Validierung
Fehler beheben
Dokumentation aktualisieren
Commit
STATUS.md aktualisieren
dann weiter
```

---

# 5. Git-Regeln

Vor Änderungen:

```text
git status
git branch --show-current
git log --oneline --decorate -20
```

Dirty Worktree niemals blind resetten. Nutzeränderungen erhalten.

Bevorzugt eigener Branch/Worktree wie `feature/drafter-v2`, aber nur wenn sicher möglich.

Keine fachfremden Änderungen committen. Kleine Commits je Meilenstein.

---

# 6. Fehler- und Stopregeln

## RECOVERABLE

Test-, Lint-, Parser-, Migrations- oder numerische Fehler: diagnose -> fix -> retry -> validate -> continue.

## DATA_UNAVAILABLE

UNKNOWN markieren, DATA_GAPS aktualisieren, keine Erfindung. Mit verbleibenden validen Features fortfahren, wenn fachlich vertretbar.

## EXTERNAL_BLOCKER

Credential ungültig, DB nicht erreichbar, Permission fehlt, Nutzungslimit beendet Lauf: sicheren Stand herstellen, STATUS aktualisieren, abgeschlossene sichere Arbeit committen, exakten Resume-Punkt dokumentieren.

## DESTRUCTIVE_OR_UNSAFE

DB löschen, Raw-Daten löschen, geschützte Verzeichnisse rekursiv chownen, Secrets ausgeben oder irreversible Migration ohne sicheren Rückweg: nicht ausführen; dokumentieren und menschliche Freigabe verlangen.

---

# 7. PHASE 0 — Repository Orientation & Baseline Freeze

Zuerst das Repository verstehen, bevor funktionaler Code geändert wird.

Ermittle:

```text
Git root
Django project root
alle Django apps
drafter app
settings
root/drafter urls
models
migrations
views/APIs
services/providers
management commands
templates/static
tests
Docker/Compose
Datenbankzugriff
Raw-data paths
Report paths
Collector
Patchsystem
Praxisfall-System
Analysemodus
```

Lies vorhandene `AGENTS.md`, `CLAUDE.md`, README und relevante docs.

Erstelle `REPO_MAP.md` mit tatsächlichem Datenfluss:

```text
Browser/UI -> View/API -> Engine -> Provider -> DB/Aggregation -> Response
```

Identifiziere protected Apps und Shared Files.

Führe den aktuellen Testbestand mit den repository-eigenen Commands aus und dokumentiere Testzahl, Laufzeit und bestehende Fehler.

Ermittle den Legacy-Stand. Keine funktionale Scoring-Änderung.

Acceptance:

```text
REPO_MAP vorhanden
App-Grenzen klar
Drafter-Datenfluss dokumentiert
Testbaseline bekannt
Legacy reproduzierbar
STATUS aktuell
```

---

# 8. PHASE 1 — Daten- und API-Audit

Ziel: exakt wissen, welche echten Daten vorhanden sind.

Ein Feld gilt nur als verfügbar, wenn es in echten RawPayloads vorkommt oder über den tatsächlich nutzbaren offiziellen API-Zugriff bestätigt wurde.

## Datenbank

Reproduzierbar bestimmen:

```text
eindeutige Ranked-Matches
Matches seit aktivem bestätigten Patch
RawPayloads
Spieler
Brawler
aktive Ranked-Maps
Modi
Matches je Modus/Map
Brawler appearances
Brawler x mode
Brawler x map
Counter pairs
Synergy pairs
```

Sinnvolle Verteilungen: min, median, p90, max sowie >=10/20/50/100/250/500.

## Dedup

Bestehende Fingerprints prüfen. Dasselbe Match kann in mehreren Battlelogs vorkommen. Suche nach Duplikaten/Kollisionen und Zeitstempelproblemen. Vor Korrekturen nichts destruktiv löschen.

## Sampling Bias

Vorhandene Provenance untersuchen:

```text
queried player
collector run
sampling type
broad/targeted/historical soweit vorhanden
```

Quantifiziere queried-side winrate, side balance, Brawler- und Skillverteilung soweit möglich.

## Offizielle API

Prüfe tatsächlich erreichbare relevante Endpunkte/Responses:

```text
players
battlelog
brawlers
events/rotation
rankings
gamemodes
```

Besonders:

```text
battle.type
Map/Mode/Brawler IDs
Player tags
Teams
Result
Duration
Star Player
Rank/Trophy-like fields
Power level
Player profile brawler data
Gadget/SP/Gear ownership
```

Explizit untersuchen, aber nicht voraussetzen:

```text
Pick order
Bans
First-pick side
per-match build
damage
healing
kills/deaths
objective stats
match/replay id
```

Prüfe teams[]-/Team-Reihenfolge statistisch, ohne daraus ungeprüft Pickorder abzuleiten.

## Skill Control

Suche nach valider Spieler-/Match-Skill-Kontrollvariable. Wenn keine valide existiert: nicht erfinden, als wichtige Lücke dokumentieren, Modelle mit/ohne Proxy getrennt evaluieren.

## Secrets

API-Tokens nie loggen/committen. Große Collector-Läufe erst nach Rate-Limit-/Kapazitätsprüfung.

Deliverables:

```text
DATA_AUDIT.md
DATA_GAPS.md
API capability matrix
reproduzierbare Audit-Commands
```

Matrix mindestens für Meta, Map/Mode, Counter, Synergy, Skill, Pickorder, Bans, Damage/DPS, HP, Range, Reload, Mobility, Wallbreak, Healing, CC, Thrower, Team DPS, Objective Pressure, Builds.

---

# 9. PHASE 2 — Evaluationsframework zuerst

Bevor neue intelligente Features gebaut werden, objektive Messlatte schaffen.

## Zeitbasierter Split

Eingefrorenen Train/Validation/Test-Split bauen:

```text
zeitbasiert
möglichst gleicher Patch/Meta-Zustand
keine Zukunft im Training
keine Fingerprint-Duplikate über Splits
Holdout nach Erstellung nicht zum Tuning verwenden
```

## Hauptmetriken

```text
Log Loss
Brier Score
Calibration
```

Sekundär optional AUC/Accuracy, aber nicht Hauptkriterium.

## Baseline-Leiter

Mindestens:

```text
B0 50/50
B1 Skill-only, falls valider Proxy
B2 global Meta
B3 + Mode
B4 + Map
B5 einfache regularisierte Pair-/Synergy-Features
```

## Leakage

Prüfe Duplicate leakage, future leakage, result-derived features, post-match information, player identity leakage und sampling artifacts.

## Runner

Baue reproduzierbaren Evaluation-Command/Script, das Split lädt, Modelle trainiert, Holdout evaluiert und JSON/CSV/Markdown Report erzeugt.

Acceptance:

```text
frozen holdout
reproduzierbare Baselines
Log Loss/Brier/Calibration
Leakage-Schutz
EVALUATION.md
```

---

# 10. PHASE 3 — Legacy objektiv benchmarken

Legacy unverändert auf demselben Holdout bewerten.

Definiere und dokumentiere eine faire Abbildung des existierenden Scorers auf fertige historische 3v3-Kompositionen.

Vergleiche B0–B5 gegen Legacy.

Soweit sauber möglich, evaluative Ablationen:

```text
Legacy ohne Counter
Legacy ohne Synergy
Legacy ohne Team Need
Legacy ohne Demo-basierte Inputs
```

Beantworte empirisch:

```text
Ist Legacy besser als Meta+Map?
Hilft Counter?
Hilft Synergy?
Hilft Team Need?
Welche Komponenten generalisieren?
Welche schaden?
```

Keine Legacy-Fixes.

---

# 11. PHASE 4 — Erstes echtes Bewertungsmodell V

Baue ein einfaches, stark regularisiertes, erklärbares probabilistisches Modell:

```text
P(Team A gewinnt | fertige Komposition, map, mode, patch, context)
```

Nicht direkt neuronales Netz.

Bevorzugter Start, falls Evaluation nichts dagegen spricht:

```text
regularisierte logistische Regression / hierarchisch-additives Logit-Modell
```

Mögliche Terme:

```text
globale Brawlerstärke
Mode-Abweichung
Map-Abweichung
gegnerische Pair-Interaktionen
eigene Synergy-Interaktionen
Skill-Differenz falls belastbar
```

Counter/Synergy gemeinsam mit anderen Termen schätzen, nicht nur aus marginalen Pair-Winrates.

Team-Swap-Symmetrie sicherstellen:

```text
P(A beats B) ~= 1 - P(B beats A)
```

Starke Regularisierung. Hyperparameter nur über Train/Validation, nicht Holdout.

Keine Post-Hoc-Feldnormalisierung, die geschrumpfte Mini-Effekte wieder extrem macht.

Unsicherheit dokumentiert erhalten.

V1 nur promoten, wenn es auf eingefrorenem Holdout sinnvoll gegen Baselines überzeugt. Primär Log Loss/Brier/Calibration.

Deliverables:

```text
training command
evaluation command
persisted model/coefs
feature manifest
MODEL_CARD
```

---

# 12. PHASE 5 — Strukturierte, versionierte Mechanikdaten

Keine subjektiven 0–100-Profile und kein flaches Brawler-Profil aus
`wallbreak=true`, `healing=true` oder `mobility=true`. Mechanikdaten dienen
als belegbare Seiteninformation, Teamfeatures, Erklärung und Cold-start-Hilfe.
Diese Architekturpräzisierung definiert Verträge, keine bereits verfügbaren
Spieldaten. Ohne etablierte Quellen und Coverage keine spekulative Mechanik-
Implementierung und keine Befüllung aus LLM-Wissen.

## Drei getrennte Ebenen

1. **Objektive Rohmechaniken:** tatsächlich belegte Werte und Effekte eines
   konkreten Angriffs, einer Fähigkeit, Form oder Beschwörung.
2. **Deterministisch abgeleitete Mechaniken:** versionierte Formeln über diese
   Rohwerte; mit Einheiten, Eingaben, Voraussetzungen und Gültigkeitsbereich.
3. **Statistisch validierte strategische Konzepte:** gelernte oder getestete
   Zusammenhänge zur Kompositionsqualität. Kein manuelles Stärkeurteil.

Ein Rohwert darf nicht still zu einem strategischen Rating werden. Insbesondere
keine Werte wie `anti_tank = 90`, `thrower_counter = 80`, `safe_pick = 95`
oder `flexibility = 90`. Alte Attribute und Legacy-Snapshots bleiben erhalten,
sind aber keine objektiven V2-Mechanikfakten.

## Mechanikvokabular und Datensatzvertrag

Soweit zuverlässig belegt, umfasst der Mechanikkatalog:

```text
HP
Schaden pro Treffer / Projektil / Schadensinstanz
Projektilzahl / Zahl und zeitlicher Verlauf der Schadensinstanzen
Reload, Munition, Reichweite
Bewegungsgeschwindigkeit, Projektilgeschwindigkeit falls verfügbar
Pierce, Splash/AOE, Bounce, prozentualer HP-Schaden
Heilung, Schilde, Schadensreduktion
Slow, Stun, Knockback, Pull, Silence / Root soweit zutreffend
Dash, Jump, Teleport
Wallbreak, Wanddurchdringung, Schießen über Wände (getrennte Eigenschaften)
Beschwörungen, Transformationen
Super-, Gadget-, Star-Power- und Hypercharge-Effekte
```

Ein Datensatz identifiziert Brawler, Mechanik, Fähigkeit und ggf. Form oder
Beschwörung. Er enthält einen typisierten Rohwert und normalisierten Wert mit
Einheit, Skalierung/Power-Level und relevantem Ziel-/Loadout-Kontext; dazu
Schema-/Mechanikversion, Patch-/Gültigkeitsbezug und Quellenbelege. Numerische,
kategorische und explizit belegte Ja/Nein-Werte sind zulässig; fehlende Werte
bleiben `UNKNOWN`, nicht null oder falsch. Ein belegter bedingter Effekt ist
kein globales Fähigkeits-Bool des Brawlers.

## Bedingungen bleiben Bedingungen

Die Herkunft eines Effekts im Kit ist getrennt von seiner Datenquelle:
`base_attack`, `super`, `gadget`, `star_power`, `hypercharge`,
`transformation` oder `summon`. Mehrere Voraussetzungen können gleichzeitig
nötig sein; sie dürfen nicht als gegenseitig ausschließende Kategorien
missverstanden werden. Abhängigkeiten sind explizit mit AND/OR-Semantik zu
beschreiben, sofern bekannt; unbekannte Aktivierungsbedingungen bleiben offen.

Je nach Mechanik erfasst der Vertrag:

```text
conditional
requires_super / requires_gadget / requires_star_power / requires_hypercharge
konkrete benötigte Fähigkeit / Form / Beschwörung
limited_uses / Ladungen und deren Bezugszeitraum
repeatability / Wiederholbarkeit
activation_condition / Aktivierungsbedingung
Dauer, Cooldown, Aufladung oder Ressourcenkosten soweit belegt
patch/version und Provenance
```

Nicht belegte Requirements dürfen nicht automatisch `False` werden. Ein
Gadget-only-Wallbreak ist keine dauerhaft verfügbare Wandzerstörung.
Potentielle Fähigkeit, Besitz, ausgerüstetes Loadout und aktuell verfügbare
Ladung sind unterschiedliche Aussagen.

## Historische Loadouts und Patchversionen

Wenn Battlelogs das ausgerüstete Gadget, die Star Power oder Hypercharge nicht
nennen, bleibt das historische Loadout `UNKNOWN`. Besitz im Spielerprofil ist
kein Ausrüstungsnachweis. Keine erfundenen Builds, keine Annahme, dass ein
bedingter Effekt aktiv war. Base Kit und optionale Loadout-Effekte bleiben
getrennt. Explizite Was-wäre-wenn-Loadouts sind Szenarien, keine historischen
Beobachtungen; auch Aktivierungswahrscheinlichkeiten werden nicht geraten.

Jeder Quellenbeleg bewahrt:

```text
Quelle (stabile Referenz / URL / Datensatzkennung)
source_date (Datum der Quelle)
retrieved_at (Abrufdatum)
patch/version und belegten zeitlichen Gültigkeitsbereich
Rohwert sowie normalisierten Wert / Einheit, soweit relevant
Normalisierungsversion und Provenance
```

Fehlende Quellendaten und Versionsgrenzen bleiben `UNKNOWN`; Abrufdatum ist
kein Patchdatum. Moderne Werte werden nicht rückwirkend auf alte Matches
übertragen. Ein zeitlich nicht belegbarer Join muss als unbekannt bzw.
ausgeschlossen dokumentiert werden. Quellenkonflikte bleiben sichtbar und
werden nicht durch plausibles Raten aufgelöst.

Quellenpriorität:

1. Offizielle API-/Spieldaten, wenn tatsächlich verfügbar und verifiziert.
2. Offizielle Supercell-Patch-/Release-Notes.
3. Zuverlässige strukturierte öffentliche Spieldatenquellen.
4. Dokumentierte Referenzquellen zum Gegenprüfen.
5. `UNKNOWN`.

LLM-Wissen ist niemals Source of Truth. Pro-Wissen darf Hypothesen, Testfälle
und Erklärungsvokabular liefern, keine ungeprüften Gewichte oder Ratings.

## Abgeleitete Größen

Zu untersuchen sind sustained DPS, Burst, effektive HP, Schaden gegen hohe HP,
effektives Reichweitenprofil, Heil-/Schildkapazität, CC-Kapazität,
Wallbreak-Verfügbarkeit/-Zuverlässigkeit, Mobilitäts-/Zugangsprofil,
Mehrzielschaden und Thrower-Zugang.

Jedes quantitative Feature braucht entweder eine dokumentierte deterministische
Formel oder ein auf Daten validiertes gelerntes Modell. Deterministische
Ableitungen speichern Formel-ID/-Version, Eingabereferenzen, Einheiten,
Annahmen und Gültigkeitsbedingungen. Etwaige Treffer-, Zielzahl-, Zeitfenster-,
Reload-/Angriffszyklus- oder Aktivierungsannahmen werden explizit ausgewiesen;
sie sind keine gemessenen Tatsachen. Fehlt eine notwendige Eingabe, ist die
Ableitung `UNKNOWN`. Teilweise bekannte Teamsummen sind keine vollständigen
Teamwerte. Mechanisch berechenbar bedeutet noch nicht strategisch wirksam.

## Reproduzierbarer Coverage-Audit

Vor der Mechanikimplementierung Quelleninventar und erreichbare Abdeckung
feststellen. Danach einen versionierten, reproduzierbaren Audit-Command planen
und implementieren, dessen Eingaben Brawleruniversum, Mechanikmanifest,
Patch/Version und Loadout-Kontext festhalten.

Pro Brawler: bekannte Rohmechaniken, bedingte Effekte mit Requirements,
UNKNOWN-Felder, Quellen und Patch-/Versionsbezug. Global: Abdeckung je
Mechanik, UNKNOWN-Anteil, Quellenverteilung und Patchverteilung. Zähler und
Nenner dokumentieren; Base Kit und Bedingungen getrennt berichten. Ein
bedingter Effekt zählt nicht als bestätigte Verfügbarkeit im Match. Fehlend,
nachweislich nicht vorhanden und nicht anwendbar bleiben unterscheidbar.

Acceptance:

```text
Quelleninventar und Coverage vor spekulativer Befüllung
Versionierter Vertrag trennt raw / derived / validated strategic concepts
Bedingungen und historisches UNKNOWN-Loadout bleiben erhalten
Patch-/Provenance- und Formellineage nachvollziehbar
Reproduzierbarer Coverage-Audit mit expliziten Nennern
Keine erfundenen Mechaniken; belegte Lücken in DATA_GAPS.md
```

---

# 13. PHASE 6 — Kompositions-Matchups statt bloßer Rollenzählung

Die Frage lautet: Können die konkreten Fähigkeiten von Team A auf die
Gewinnbedingungen und defensiven Eigenschaften von Team B antworten?
Reine Rollenanzahlen beantworten sie nicht.

Mit belegten Phase-5-Daten untersuchen:

- Reicht eigener Dauerschaden gegen gegnerische effektive HP und Sustain?
- Kann das eigene Team einen gegnerischen Reichweitenvorteil überwinden?
- Erreicht es Thrower hinter Terrain und stoppt es eine Frontline mit hohen HP?
- Sind Dauerschaden, Reichweite und Sustain für diesen Kontext ausreichend?
- Sind Wallbreak/Terrainkontrolle und Mobilitäts-/Zugangswerkzeuge verfügbar,
  wiederholbar und unter den tatsächlichen Bedingungen einsetzbar?
- Welche schweren funktionalen Lücken oder Redundanzen bleiben?

Terrainabhängigkeit, Gegnerdruck und andere Kontextgrößen benötigen eigene
belegte Daten oder validierte Ableitungen. Fehlende Map-Geometrie darf nicht
als bekanntes Thrower-Matchup erscheinen. UNKNOWN wird weder als Schwäche
noch als bestätigte Deckung interpretiert.

Ein individuell starker Brawler darf deutlich niedriger rangieren, wenn sein
Pick eine kritische Kompositionsschwäche offen lässt und das validierte V
für die resultierende Komposition einen schlechteren Wert vorhersagt.
Daraus folgt keine feste Strafe, kein gewünschter Beispielrang und kein
manueller Override für bestimmte Brawler.

Unabhängig ablatierbare Interaktionshypothesen:

```text
own_sustained_dps * enemy_effective_hp
own_damage_vs_high_hp * enemy_high_hp_share
own_access_tools * enemy_thrower_presence
own_wallbreak_reliability * terrain_dependence
own_range_profile * enemy_range_profile
own_cc_capacity * enemy_frontline_or_mobility
own_sustain * enemy_pressure
```

Jeder Term braucht Definition, Einheiten, Eingaben, Quellen-/Patchbezug,
Bedingungen und UNKNOWN-Verhalten. Listen sind Hypothesen, keine fertigen
Features und keine Effektbehauptungen. Weder "2 Tanks => +20 Anti-Tank" noch
andere willkürliche Boni oder statische Synergiegewichte sind erlaubt.

Hypothesen separat ablatieren; Auswahl auf Train/Validation, abschließende
Prüfung auf einem neuen, zuvor unberührten Testfenster. Der bereits evaluierte
historische Holdout und sein finaler Shared-Subset-Vergleich bleiben geschlossen.
Keine Aktivierung ohne reproduzierbaren Nutzen, Leakage-Prüfung und erhaltene
Kalibrierung/Symmetrie. Quellenabdeckung und formale Berechenbarkeit sind
notwendige Voraussetzungen, aber kein Ersatz für empirische Validierung.

Acceptance:

```text
Komposition gegen Gegnerkomposition bewertet; keine bloße Rollenliste
Jede Hypothese separat ablatierbar und versioniert
Bedingte Loadouts / UNKNOWN / Patchbezug propagiert
Nur empirisch validierte Kompositionsterme aktiv
Kein Tuning auf Einzelfälle oder den geschlossenen historischen Holdout
```

---

# 14. PHASE 7 — Faktorisierte Interaktionen nur bei Bedarf

Nur wenn V1 stabil ist und Sparse-Pair-Daten nachweislich limitieren.

Mögliche Architektur:

```text
kleine latente Brawler-Vektoren
bilineare/faktorisierte Interaktion
Mechanikdaten als Seiteninformation
geschrumpfte Brawler-Residuen
```

Ziel: Information zwischen ähnlichen Brawlern teilen und n=0/n=1-Paare mit ehrlicher Unsicherheit behandeln.

Nicht implementieren, wenn einfachere Modelle gleich gut/besser generalisieren.

Neuronales Set-/Transformer-Modell erst später als Challenger bei ausreichender Datenmenge.

---

# 15. PHASE 8 — Draft Decision Layer

Voraussetzung: ausreichend gutes, kalibriertes V.

## Jeder Kandidat erzeugt einen neuen Draftzustand

Search bewertet nie nur isolierte Kandidatenstärke. Jeder legale Kandidat
wird dem aktuellen Zustand hinzugefügt. V/Search bewertet die resultierende
Komposition und, solange Picks offen sind, plausible Fortsetzungen:

- welche Kompositionsschwächen der Pick behebt,
- welche er offen lässt oder neu erzeugt,
- welche plausiblen Antworten des Gegners folgen können,
- wie gut die resultierende vollständige Komposition ist.

Diese Aussagen müssen aus belegten Mechanik-/Kompositionstermen oder
Search-Folgen kommen; bei fehlender Evidenz bleiben sie UNKNOWN. Sie sind
keine zusätzliche Schicht handgesetzter Kandidaten-Scores. Base Kit,
bedingte Loadouts, Ressourcen und Patchversionen müssen im bewerteten Zustand
konsistent bleiben. First/Mid/Last verwenden dasselbe V und den jeweiligen
Suchhorizont; keine Doppelzählung über separate Handgewichte.

## Last Pick

Für jeden legalen Kandidaten fertige Composition bilden, V berechnen, höchsten erwarteten Wert wählen.

Keine separate Handgewichtung für Counter/Team Need/Flexibility, wenn diese Effekte bereits in V stecken.

## Mid Picks

Search/Planning über verbleibende Züge. Pickorder korrekt aus Spielregeln/UI-Zustand abbilden; historische Pickorder nicht erfinden.

Untersuche Minimax und Expectimax/population-aware. Populations-Gegnermodell aus Pickhäufigkeiten ist nur Approximation und muss so gekennzeichnet werden.

## First Pick

Search tiefer über verbleibende Züge. Blind-Pick-Sicherheit, Flexibilität und Counterability möglichst als Ergebnis möglicher Antworten.

## Bans

Nutzer-Bans als Legalitätsconstraint. Ban-Empfehlung später als Search-Nebenprodukt.

Acceptance:

```text
Last Pick deterministisch aus V
First/Mid dokumentierte Search
Legalität getestet
keine gebannten/gepickten/unverfügbaren Empfehlungen
```

---

# 16. PHASE 9 — Erklärungsschicht

Keine nachträglich erfundene Begründung.

Jede Aussage muss auf Modellterm, Messwert, Search-Folge oder objektiver Mechanik beruhen.

Pro Kandidat mindestens:

```text
P(win)
Uncertainty
größte positive Beiträge
größte Risiken
direkte vs indirekte Evidenz
beste plausible gegnerische Antwort, wenn relevant
```

Wenn Effekt überwiegend indirekt/faktorisiert ist, entsprechend formulieren statt "gemessen" zu behaupten.

Falls LLM Text formuliert, darf es nur strukturierte Modellfakten verwenden und nichts ergänzen.

---

# 17. PHASE 10 — UI/API Integration

V2 sauber integrieren, ohne andere Apps zu beschädigen.

Legacy vorerst verfügbar/benchmarkbar.

V2 bekommt explizite Modellversion und klaren Engine-/Feature-Flag-Wechsel.

Detailanalyse mindestens:

```text
model version
P(win)
uncertainty
top contributions
sample/provenance
search response
```

Praxisfälle speichern Modellversion. Historische Praxisfälle nicht überschreiben.

---

# 18. PHASE 11 — Real-Draft-Logging

Langfristig speichern:

```text
timestamp
map/mode
draft phase/state
bans
own/enemy picks
recommendation snapshot
chosen brawler
model version
result when later known
```

Vorhandenes Praxisfall-System nutzen, wenn geeignet.

Nicht ungeprüft als Training verwenden; Selektionsbias dokumentieren.

---

# 19. PHASE 12 — Collector & Datenwachstum

Vor großen Läufen Rate Limits, Requests/hour, 429 handling, Retry/backoff, Raw persistence, Dedup und Provenance prüfen.

Strategien:

```text
broad high-rank graph
rankings by brawler
rare-brawler discovery
current active maps
```

Keine Sampling-Korrektur erfinden.

Autorisierter Bootstrap (2026-09-23, D-008): Wenn die anonymisierte Historie
keine Spieler-Tags traegt, diese niemals rekonstruieren. Eine getrennte,
persistente Tagged-Frontier darf echte Tags aus offiziellen Trophaeenranglisten
als Saat aufnehmen; daraus folgt kein Ranked-/Skill-Label. Pro Beobachtung
RawPayload, CollectorRun, exakten JSON-Pointer und ggf. abgefragten Elternspieler
speichern. Nur belegte, neue, auswertbare soloRanked-Partien erweitern den Graph.
Die bestehenden gemeinsamen Spieler-Cooldowns bleiben erhalten. Initial maximal
ein Ranglisten-HTTP-Versuch, drei zugelassene Saat-Tags, fuenf Battlelog-HTTP-Versuche
inklusive Retries und ein neuer Abruf-Hop pro Lauf. Rand-Tags bleiben persistent
fuer spaetere Laeufe; keine offene Rekursion oder automatische Dauersammlung.
Rohantworten vollstaendig erhalten, historische Zeilen nicht mit Tags auffuellen.
Kein nutzbarer Ranglisten-Tag: Beleg speichern und stoppen, keine Ersatzquelle
raten. Nach dem Experiment nur neuere Beobachtungen auditieren; alter Holdout,
Legacy und finaler Shared-Subset-Vergleich bleiben geschlossen/unveraendert.

Langfristiges Planungsziel darf 50k–100k deduplizierte aktuelle Ranked-Matches pro relevantem Patchfenster sein, aber Datenmenge niemals fälschen.

Wenn kontrollierter Collector-Lauf innerhalb vorhandener Berechtigungen sicher möglich ist, darf er nach Phase 1 gestartet werden. Sonst Runbook/Automation bauen und mit verfügbaren Daten fortfahren.

---

# 20. PHASE 13 — Automatisierte Modell-Regressionen

Mindestens:

```text
calibration regression
log-loss regression
team-swap symmetry
no leakage
no illegal picks
no NaN/inf
probability in [0,1]
fixed-seed determinism
legacy reproducibility
```

Kuratierte Praxisszenarien sind Plausibilitätswarnungen, keine Ground Truth. Keine konkrete Rangfolge hardcoden, wenn objektive Ground Truth fehlt.

---

# 21. PHASE 14 — Legacy vs V2 Gesamtbericht

Reproduzierbarer Bericht mit:

```text
Dataset
Train/Validation/Holdout
Patch
Match counts
Feature sets
Model versions

50/50
Skill baseline
Meta
Meta+Mode
Meta+Map
Pair/Synergy
Legacy
V1
V2 + validierte Teamfeatures
```

Metriken:

```text
Log Loss
Brier
Calibration
optional AUC
training/inference time
coverage
known limitations
```

V2 nur als Default promoten, wenn technisch stabil, empirisch sinnvoll, kalibriert, UI korrekt, andere Apps nicht regressiert und Rollback möglich ist.

Wenn V2 Baselines nicht schlägt: nicht künstlich promoten; bestes empirisch belegtes Modell verwenden.

---

# 22. Modell-/Feature-Governance

Keine aktive Scoring-Komponente nur aufgrund von Plausibilität.

Ein Feature darf dauerhaft aktiv werden, wenn es:

```text
auf Train/Validation sinnvoll ist
Holdout nicht offensichtlich schadet
keine Leakage erzeugt
reproduzierbar ist
belegbare Datenquelle hat
```

Pro-Wissen darf Hypothesen, Struktur, Testfälle und Sprache liefern; nicht ungeprüft Gewichte oder Ratings.

---

# 23. Dependencies und Performance

Neue Dependencies nur nach Prüfung vorhandener Pakete und mit Begründung in DECISIONS.

Keine große ML-Infrastruktur, wenn regularisierte Regression reicht. Keine GPU-Pflicht für V1.

Tracke V-Inference, Last-Pick-Ranking, Search-Latenz und DB-Queries. Nutze Beam Search/Caching nur mit dokumentierter Wirkung.

---

# 24. Reproduzierbarkeit

Training/Evaluation speichern:

```text
fixed seeds
split definition
model version
feature version
patch window
commit hash
```

Reports dürfen gitignored sein, aber Erzeugungsbefehle müssen dokumentiert sein.

---

# 25. STATUS-Format

`STATUS.md` regelmäßig aktualisieren:

```text
# Drafter V2 Status

Overall:
- Completed milestones: X / Y
- Current phase: ...
- Current task: ...
- Blocker: none | ...

Latest validation:
- Drafter tests: ...
- Relevant full suite: ...
- Evaluation: ...

Data integrity:
- fabricated values: 0
- unresolved gaps: ...

Next:
...
```

Nicht nur am Ende.

---

# 26. DECISIONS-Format

```text
## D-00X: Titel

Problem:
Alternativen:
Evidence:
Decision:
Why:
Validation:
Revisit if:
```

---

# 27. Resume bei Token-/Session-Abbruch

Wenn Nutzungslimit, Sessionende oder externer Blocker stoppt:

1. keinen destruktiven halbfertigen Schritt hinterlassen,
2. konsistenten Stand herstellen,
3. Tests soweit möglich,
4. nur abgeschlossene sichere Arbeit committen,
5. STATUS aktualisieren,
6. ganz oben `RESUME FROM: Phase X / criterion Y`,
7. exakten nächsten Schritt dokumentieren.

Ein Folgeagent muss allein anhand von PROMPT, PLAN, STATUS, DECISIONS, DATA_GAPS und git log weitermachen können.

---

# 28. Abschlussbedingungen

Die Aufgabe ist fertig, wenn alle erreichbaren Punkte erfüllt sind:

```text
[ ] Repo kartiert
[ ] Legacy eingefroren/benchmarkbar
[ ] Daten/API auditiert
[ ] Dedup/Sampling geprüft
[ ] zeitbasierter Holdout
[ ] Baseline-Leiter
[ ] Legacy objektiv gemessen
[ ] probabilistisches V trainiert/evaluiert
[ ] Modellpromotion evidenzbasiert
[ ] Last Pick über V
[ ] First/Mid Search, sofern V belastbar
[ ] objektive Mechanikpipeline oder dokumentierte Lücke
[ ] nur validierte Teamfeatures aktiv
[ ] Erklärungen aus Modell/Search
[ ] UI/API integriert
[ ] Praxis-/Draft-Logging modellversioniert
[ ] Tests grün
[ ] andere Websitebereiche nicht regressiert
[ ] MODEL_CARD vollständig
[ ] EVALUATION vollständig
[ ] STATUS abgeschlossen
[ ] Rollback/Legacy-Option
```

Ein Punkt darf nur wegen echtem externen/data blocker als unerreichbar markiert werden.

Nicht akzeptierte "Blocker":

```text
zu kompliziert
dauert lange
nur Vorschlag erstellt
müsste später getestet werden
```

Evaluation tatsächlich ausführen.

---

# 29. Finaler Abschlussbericht

Am Ende berichten:

```text
Ausgangszustand
echte verfügbare Daten
fehlende Daten
objektive Legacy-Performance
Baselines
gewähltes V und Begründung
Features mit nachweislichem Nutzen
verworfene plausible Features
Last-Pick-Logik
First/Mid-Search
Unsicherheitsbehandlung
Erklärungslogik
V2-Metriken
bekannte Grenzen
wertvollste nächste Daten
Commits
Startbefehle für Training/Evaluation/App
Rollback auf Legacy
```

Klar zwischen `gemessen`, `abgeleitet`, `angenommen` und `unbekannt` unterscheiden.

---

# 30. STARTANWEISUNG

Beginne jetzt.

1. Lies alle Repository-Anweisungen (`AGENTS.md`, `CLAUDE.md`, README, relevante docs).
2. Prüfe Git-Status und Repository-Struktur.
3. Führe Phase 0 vollständig aus.
4. Erstelle/aktualisiere die persistenten `docs/drafter-v2/`-Dateien.
5. Erstelle deinen konkreten repository-spezifischen `PLAN.md`.
6. Arbeite anschließend autonom Meilenstein für Meilenstein weiter.
7. Warte nicht zwischen normalen Phasen auf menschliche Bestätigung.
8. Stoppe nur nach den definierten External-/Unsafe-Blocker-Regeln.
9. Wenn eine Annahme empirisch falsch ist, ändere den späteren Plan transparent in `DECISIONS.md`.
10. Erfinde niemals Daten, um den Plan erfüllen zu können.

**Do not stop after planning. Execute the plan.**
