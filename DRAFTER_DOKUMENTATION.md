# 🎯 Draft Coach — Brawl-Stars-Ranked-Assistent

> Die vollständige Erklärung zum Drafter unter `/draft/`. Die kompakte
> Arbeitsreferenz steht in `CLAUDE.md`; diese Datei erklärt das *Warum*.
>
> **Stand:** September 2026 · MVP mit gekennzeichneten Demo-Daten · Datenpipeline für echte Daten vorbereitet

---

## 1. Was das Werkzeug ist — und was nicht

Der Drafter beantwortet **eine** Frage:

> Welche Auswahl erhöht in *genau diesem* Draft die erwartete Siegchance am meisten?

Er beantwortet ausdrücklich **nicht**: „Welcher Brawler hat die höchste
Winrate?" Das ist der Unterschied zwischen einem Draft-Werkzeug und einer
Tierlist, und er zieht sich durch jede Entscheidung im Code.

Konkret heißt das: drei einzeln starke Tanks werden nicht dreimal
empfohlen. Das System sieht die fehlende Reichweite, den fehlenden
Anti-Tank und die dreifach besetzte Frontline — und stuft den dritten
Tank herunter, obwohl er für sich genommen gut wäre.

**Zweiter Zweck:** Das Werkzeug soll Draften *beibringen*. Deshalb ist
jede Empfehlung begründet, jede Rolle benannt und jeder Score
aufschlüsselbar. Eine Zahl ohne Begründung wäre hier ein Fehler, kein
Feature.

---

## 2. Datenlage — bitte zuerst lesen

**Alle Werte im Auslieferungszustand sind gepflegte Einschätzungen, keine
gemessenen Statistiken.** Sie tragen `source="demo"`, die Oberfläche
weist oben auf jeder Seite darauf hin, und die Confidence ist bei
Demo-Daten auf 0,35 gedeckelt (`services/confidence.py`). Das System
zeigt deshalb nie „Confidence: Hoch", solange keine echten Daten
vorliegen.

Die **Empfehlungslogik ist vollständig und echt**. Was fehlt, ist die
Zahlenbasis. Die Pipeline, die sie liefern wird — Import, Deduplizierung,
Aggregation, Provider — steht und ist getestet (§16–§19); sie läuft
vollständig ohne API-Key auf gespeicherten Dateien. Sobald gemessene
Statistiken existieren, schaltet die Engine automatisch darauf um.

---

## 3. Aufbau

```
drafter/
├── attributes.py     ← das Vokabular (32 Eigenschaften, 6 Draftwerte, 9 Rollen)
├── config.py         ← ALLE Stellschrauben (Gewichte, Schwellen, Pipeline)
├── seed_data.py      ← der Demo-Datensatz
├── testdaten/        ← synthetische Match-Dateien (versioniert, klar markiert)
├── models/
│   ├── brawler.py, maps.py, patches.py, builds.py, prefs.py   Katalog und Nutzer
│   ├── stats.py      ← VORAGGREGIERTE Statistiken (das Einzige, was die Engine sieht)
│   └── matches.py    ← ROHDATEN: Lieferungen, Partien, Spieler, Bans
├── services/
│   ├── context.py, scoring.py, draft_engine.py     Engine
│   ├── team_coverage.py, team_need.py, counters.py, synergies.py,
│   │   map_fit.py, meta.py, draft_position.py, personal.py         Komponenten
│   ├── confidence.py, win_probability.py, bans.py, builds.py, coach.py
│   ├── patch_weighting.py   Zeit-/Patchgewicht, Bayes
│   ├── daten.py             Datenraum: fragt den StatProvider, wählt je Kontext die beste Zeile
│   ├── providers/           StatProvider + MatchProvider (§16)
│   ├── ingest/              Fingerabdruck, Parser, Importer (§17)
│   ├── aggregation/         Rohmatches → Statistiken (§18)
│   └── brawl_api_client.py  HTTP-Hülle für die offizielle API
├── management/commands/  seed_brawl_data, import_brawl_fixture,
│                         aggregate_brawl_stats, rebuild_draft_stats
├── views/                pages.py (3 Seiten) + api.py (5 Endpunkte)
└── tests/                ein Thema je Datei
```

Dazu außerhalb der App, der Projektkonvention folgend:
`templates/drafter/`, `static/drafter/` und `data/brawl_fixtures/`
(gitignored — mitgeschnittene API-Antworten enthalten Spieler-Tags).

---

## 4. Die zentrale Entwurfsentscheidung: ein Vokabular für alles

`drafter/attributes.py` definiert 32 Eigenschaften (`anti_tank`,
`long_range`, `peel`, `wallbreak`, …). Dieselbe Liste wird **dreifach**
benutzt:

| Wer | Bedeutung |
|-----|-----------|
| **Brawler** | „Wie stark bin ich darin?" (0–100) |
| **Map/Modus** | „Wie wichtig ist das hier?" (0–100) |
| **Team** | „Was haben wir, was fehlt uns?" |

Dadurch ist Map-Fit ein Skalarprodukt, Team-Coverage ein Vergleich zweier
Vektoren und Redundanz ein Überschuss im selben Raum. Mit drei getrennten
Vokabularen müsste jede Kombination von Hand verdrahtet werden.

**Neue Eigenschaft? Nur dort eintragen.** Die Modelle validieren gegen
diese Liste — ein Tippfehler in einem JSONField fällt beim Speichern auf
und nicht erst in einer stillen Fehlempfehlung.

---

## 5. Wie ein Score entsteht

### Der Vertrag
Jede Komponente liefert einen Wert in **[-1, +1]**, 0 heißt
„durchschnittlich". Erst nach dieser Normalisierung bedeutet „Gewicht
0.30" tatsächlich „30 % der Entscheidung". Roh-Winrates (0–1),
Attribute (0–100) und Vorteile (−1…+1) werden **nie** direkt addiert.

Die Anzeige rechnet genau einmal um, ganz am Ende:
`anzeige_score = 50 + 50 × score`. **50 ist ein durchschnittlicher Pick**
— keine Min-Max-Streckung über das Kandidatenfeld, die dem besten
Vorschlag auch dann 95 gäbe, wenn alle schlecht sind.

### Die Komponenten
| Komponente | Quelle |
|---|---|
| Map & Modus | Skalarprodukt Brawlerprofil × Mapanforderung, feldrelativ normalisiert |
| Meta | `BrawlerStat`, abgewertet nach Alter und Patch |
| Counter | `CounterStat`, sonst Heuristik aus sechs Attributsignalen |
| Synergie | `SynergyStat`, sonst Heuristik (Ergänzung, nicht Summe) |
| Teambedarf | Dringlichkeit × **Zuwachs am Teamprofil** |
| Draft-Position | `draft_values` je nach Phase + Konterbarkeit |
| Deine Sicherheit | persönliche Confidence, gedeckelt |
| Flexibilität | `flexibility_value` |
| − Redundanz | Attributüberschuss + Rollenüberhang + „bringt nichts Neues" |
| − Angreifbarkeit | Restlücken × Fähigkeit des Gegners, sie auszunutzen |
| − Datenlage | `−(1 − Confidence)` |

### Die Aufschlüsselung
**Jede** Empfehlung trägt ihre vollständige Aufschlüsselung — nicht nur
die Spitze. Sie kostet nichts extra: die Komponenten sind ohnehin
gerechnet, sonst gäbe es keinen Score.

Die elf Zeilen stehen in **fester Reihenfolge**
(`config.KOMPONENTEN_REIHENFOLGE`), auch die mit Beitrag 0. Zwei Gründe:
zwei Empfehlungen lassen sich nur vergleichen, wenn dieselben Zeilen an
denselben Stellen stehen — und eine fehlende Zeile wäre nicht von einer
Null zu unterscheiden. Dass „Counter" beim First Pick nichts beiträgt,
ist eine Aussage; sie soll sichtbar sein.

Jede Zeile nennt **Wert × Gewicht = Beitrag** und trägt ihre eigenen
Begründungen mit. Ohne den Rohwert könnte man „schwache Komponente"
nicht von „kleines Gewicht" unterscheiden. Die Summe der Beiträge ergibt
exakt `Score − 50`; ein Test hält das fest, sonst wäre die
Aufschlüsselung Dekoration.

> ⚠️ **Alle Gewichte sind Beträge, auch die der Strafkomponenten.** Das
> Vorzeichen steckt im *Wert*. Wären Gewicht und Wert negativ, würde aus
> jeder Strafe ein Bonus — ein Fehler, der beim Lesen nicht auffällt,
> weil die Zahlen einzeln richtig aussehen. Ein Test hält das fest
> (`test_phasen.py::test_strafgewichte_sind_betraege`).

### Die Phasen
Die Gewichte hängen an der Draft-Phase (`config.PHASEN_GEWICHTE`). Der
Verlauf ist die eigentliche Aussage:

| | First Pick | Early | Mid | Last |
|---|---|---|---|---|
| Counter | 0.02 | 0.12 | 0.20 | **0.29** |
| Teambedarf | 0.10 | 0.15 | 0.18 | **0.24** |
| Map & Modus | **0.34** | 0.28 | 0.24 | 0.20 |
| Flexibilität | **0.14** | 0.06 | 0.04 | 0.02 |

Am Anfang kennt man niemanden — Counter sind fast bedeutungslos, Map und
Flexibilität entscheiden. Am Ende weiß man alles — Counter und Teambedarf
entscheiden, sich offenzuhalten bringt nichts mehr.

Die Phase wird nach **Informationsstand** bestimmt, nicht nach
Slotnummer (`DraftContext.phase`).

---

## 6. Das Herzstück: Teamprofil und Lücken

Das Teamprofil ist **nicht die Summe** und **nicht der Mittelwert** der
Einzelwerte:

```
profil = bester + 0.45 × zweitbester + 0.20 × drittbester   (gedeckelt auf 1.0)
```

- **Kein Maximum**: ein zweiter guter Anti-Tank ist mehr wert als keiner.
- **Keine Summe**: zwei halbe Anti-Tanks sind kein ganzer — wenn keiner
  den Tank wirklich aufhält, hilft es nicht, dass beide es ein bisschen
  können.
- **Kein Mittelwert**: der würde die Deckung *senken*, wenn ein
  Spezialist dazukommt, der anderswo stark ist.

### Bedarf = Wichtigkeit × Fehlbetrag
```
bedarf[k] = anforderung[k] × max(0, ZIEL − profil[k]) / ZIEL
```
Was die Map nicht verlangt, erzeugt keinen Bedarf. Wallbreak ist auf
einer offenen Map kein Mangel und auf Center Stage ein dringender — ohne
dass irgendwo eine Sonderregel je Map steht.

### Der Gegner erzeugt eigene Anforderungen
Keine Map verlangt „Anti-Thrower" — ein gegnerischer Tick schon.
`anforderungen_mit_gegner()` erweitert das Mapprofil um sieben
Zwangspaarungen (gegnerische Robustheit → Anti-Tank, gegnerischer
Thrower → Anti-Thrower, …), verknüpft mit `max`: der Gegner kann
Anforderungen nur **hinzufügen**, nie eine Map-Anforderung verwässern.

**Ohne diesen Schritt wäre der Drafter wieder eine Map-Tierlist.**

### Der Kandidat wird am Zuwachs gemessen
Nicht sein Eigenwert zählt, sondern die Verbesserung des Teamprofils
(`Teamanalyse.zuwachs`). Ein Anti-Tank 95 neben einem vorhandenen
Anti-Tank 90 bringt fast nichts; derselbe Brawler in einem Team ohne
Anti-Tank bringt alles. **Das ist der Unterschied, den eine Tierlist
nicht sehen kann.**

---

## 7. Counter und Synergie — zwei vermiedene Denkfehler

**Counter sind keine Winrates.** „Gale gewinnt 62 % gegen Bull" heißt
nicht „Gale ist ein 62-%-Counter" — da stecken Map, Rang, Mitspieler und
Patch mit drin. `CounterStat.advantage` ist die bereinigte Größe,
`raw_rate` und `games` behalten die Rohmessung daneben. Gibt es keinen gepflegten
Eintrag, greift eine Heuristik aus sechs Attributsignalen — und
kennzeichnet ihre Gründe als „geschätzt".

**Synergie ist nicht gemeinsame Winrate.** Sonst gälten zwei ohnehin
starke Brawler automatisch als gute Synergie. `SynergyStat.synergy` ist
der *Mehrwert über die Einzelleistung hinaus*; die Heuristik misst
Ergänzung (wer deckt, was der andere nicht kann) und zieht für
Gleichförmigkeit ab.

---

## 8. Persönliche Sicherheit — die wichtigste Leitplanke

Nutzer können je Brawler 0–100 hinterlegen (`/draft/meine-brawler/`,
angemeldet in der Datenbank, als Gast in der Session).

**Der Einfluss ist hart gedeckelt** (`PERSOENLICH_MAX_AUSSCHLAG = 0.08`,
entspricht ±4 Punkten auf der Anzeige). Der Deckel sitzt in
`personal.deckel_anwenden()` und nicht beim Aufrufer, damit er nicht
versehentlich umgangen werden kann.

Grund: Eigene Übung soll zwischen *gleichwertigen* Vorschlägen
entscheiden — sie darf einen Pick, der nicht in den Draft passt, nicht
nach oben heben. Sonst bestätigt das Werkzeug nur noch die eigene
Gewohnheit, statt Draften beizubringen. Zwei Tests halten das fest.

---

## 9. Statistik: Alter, Patch, Stichprobe

```
gewicht = zeit_gewicht × patch_gewicht
```

- **Zeit**: exponentieller Zerfall, Halbwertszeit 14 Tage.
- **Patch**: `severity` entscheidet — Rework 0.05, groß 0.20, mittel
  0.50, klein 0.75. Mehrere Änderungen multiplizieren sich.
- **Stichprobe**: Bayes-Glättung gegen einen Prior von 120 Spielen bei
  50 %. Damit schlägt „62 % aus 150 Spielen" nicht mehr „59 % aus
  30 000" — ein eigener Test hält genau diesen Fall fest.

Nicht abgebildet ist der *indirekte* Patcheffekt (Tanks werden gebufft,
also wird Anti-Tank besser). Das braucht Matchdaten; hier wäre es
geraten.

---

## 10. Der Coach: aus Struktur werden Sätze

Kein Textbaustein-Lager, kein Sprachmodell. Jeder Satz entsteht aus
Werten, die anderswo berechnet wurden. Das hat zwei erwünschte Folgen:

1. Der Coach kann nichts behaupten, was die Bewertung nicht hergibt —
   Erklärung und Score können nicht auseinanderlaufen.
2. Neue Brawler brauchen keine neuen Texte. Wer Attribute pflegt,
   bekommt die Sätze umsonst.

### Was der fertige Draft liefert

**Je Spieler:** Rolle im Team · Hauptaufgabe · weitere Aufgaben ·
„nicht deine Aufgabe" · bevorzugtes Matchup · zu vermeidendes Matchup ·
Opening-Lane mit Begründung · Watch-outs · empfohlener Build.

**Fürs Team:** Win Condition · Matchup-Zuordnung · Lane-Swap-Plan ·
Team-Schwächen · Gefahren · Startpositionen · geschätzte Draft-Stärke ·
Data Confidence.

Zwei Dinge daran sind bewusst so gebaut:

**Eine Zuordnung für alle.** Die Matchups entstehen einmal für das Team
(beste **Gesamtsumme** über alle sechs Permutationen, nicht das beste
Einzelduell) und werden dann an die Spielerkarten verteilt. Rechnete
jeder Spieler sein bestes Matchup selbst aus, bekämen zwei denselben
Gegner und der dritte gar keinen — der Teamplan würde etwas anderes
sagen als die Karte daneben. Dasselbe gilt für die Lanes.

**Team-Schwächen werden nach Ausnutzbarkeit sortiert.** Eine Lücke, die
im gegnerischen Team niemand bespielen kann, ist im Draft keine — sie
wird genannt, aber als das, was sie ist. Ausnutzbare Lücken stehen oben
und nennen den Gegner, der sie bestraft.

Ist ein Matchup nicht klar gewonnen, sagt der Coach das auch so
(„das Matchup ist nicht geschenkt, halte es offen") statt eine
Überlegenheit zu behaupten, die die Zahlen nicht hergeben.

---

## 11. Siegchance

`services/win_probability.py` hat ein Provider-Interface. Heute rechnet
dort `HeuristicWinProbabilityProvider` aus Deckungsdifferenz, Matchups
und Meta; die Spanne ist bewusst eng (±18 Punkte, gedeckelt bei 20–80 %),
weil ein Draftvorteil die Siegchance real selten über 65 % schiebt.

Die Oberfläche nennt das **„Geschätzte Draft-Stärke"** und weist die
Heuristik als solche aus — keine falsche Präzision.

Ein späteres ML-Modell tritt über `setze_provider()` an dieselbe Stelle,
ohne dass Engine, Views oder Templates sich ändern. Ein Test hält diese
Zusage fest.

---

## 12. Web-Schicht

| Route | Zweck |
|---|---|
| `/draft/` | Die Oberfläche. Wird **einmal** gerendert, danach nur noch JSON. |
| `/draft/meine-brawler/` | Confidence-Pflege (Anmeldung nötig) |
| `/draft/login/` · `/draft/logout/` | Djangos `LoginView` — die einzige Session-Anmeldung des Projekts |
| `POST /draft/api/recommend/` | Draftzustand rein, Empfehlungen + Teamanalyse + Bans raus |
| `POST /draft/api/final-analysis/` | Matchplan |
| `POST /draft/api/detail/` | vollständige Aufschlüsselung eines Brawlers |
| `POST /draft/api/confidence/` | persönlichen Wert speichern |
| `GET /draft/api/katalog/` | Brawler, Modi, Maps — einmal beim Laden |

**Kein DRF.** Das Projekt stellt DRF global auf JWT + `IsAuthenticated`
(richtig für CORVIS, falsch für eine öffentlich nutzbare Draft-Seite).
Statt diese Voreinstellung in jeder View zu überschreiben, benutzt der
Drafter schlichte Django-Views mit Session und CSRF.

**Frontend:** ES-Module ohne Build-Schritt (`api.js`, `state.js`,
`ui.js`, `main.js`). Bewusst kein React — CORVIS bringt seine eigene
React-App mit, die Portfolio-Seiten sind Vanilla; eine dritte
Werkzeugkette wäre unnötig.

**Geschwindigkeit:** rund 40 ms und 14 Abfragen je Empfehlungsanfrage,
Antwort ~33 KB — inklusive Aufschlüsselung, Coach-Texten und Build für
alle acht angezeigten Empfehlungen.

Drei Dinge halten das niedrig, und alle drei sind gegen dieselbe Falle
gebaut (eine Abfrage je Kandidat statt einer für alle):
- der **Datenraum** lädt Statistiken, Balanceänderungen und Patches
  vorab (`prefetch_related` + `select_related`),
- der **Ausrüstungskatalog** lädt Gadgets, Star Powers und Gears einmal
  je Anfrage — die gegnerischen Gadgets sind für jeden Kandidaten
  dieselben,
- teure Auskünfte entstehen nur für das, was angezeigt wird.

> Diese N+1-Fallen fallen im Direkttest **nicht** auf: ohne gesetzten
> Patch überspringt die Engine die Patchgewichtung ganz. Gemessen wird
> deshalb über die API, nicht über die Engine allein.

---

## 13. Bedienung

```
Modus und Map wählen  →  Ban-Phase (oder überspringen)  →  Picks klicken
```

Ein Klick auf eine Brawlerkarte setzt sie auf die nächste Position der
Standardreihenfolge **1-2-2-1**. Klick auf einen belegten Slot nimmt den
Pick zurück, Klick auf einen freien Slot zielt dorthin (für
Korrekturen). Klick auf eine Empfehlung öffnet die vollständige
Aufschlüsselung.

---

## 14. Daten pflegen

```bash
# Demo-Datensatz anlegen oder aktualisieren (idempotent)
docker compose exec django-dev python manage.py seed_brawl_data

# Demo-Daten vorher löschen - manuell gepflegte bleiben stehen
docker compose exec django-dev python manage.py seed_brawl_data --reset
```

Im Admin lässt sich alles bearbeiten. **Achtung:** `seed_brawl_data`
gleicht Demo-Daten wieder an die Datei an. Wer Änderungen behalten will,
stellt `source` auf „Manuell gepflegt" — `--reset` fasst sie dann nicht
an.

---

## 15. Tests

```bash
docker compose exec django-dev python manage.py test drafter \
    --settings=meinprojekt.settings_test
```

215 Tests, rund zwei Minuten. Sie laufen gegen den echten Demo-Datensatz statt
gegen erfundene Testobjekte: der Seed ist Teil der Auslieferung, und mit
handgebauten Miniaturbrawlern würden die Tests an ihm vorbeiprüfen.

### Verhaltenstests statt Platzierungstests
`tests/test_modellverhalten.py` prüft **keine Platzierungen**. Ein Platz
hängt von allen zwanzig Kandidaten gleichzeitig ab, verschiebt sich bei
jeder Attributänderung, und ein Fehlschlag sagt nicht, was kaputt ist.
Schlimmer: solche Tests verleiten dazu, an den Gewichten zu drehen, bis
ein Lieblingsbeispiel wieder oben steht — also genau zum Übertrainieren
auf Einzelfälle.

Geprüft wird stattdessen die **Richtung**, gemessen an den
Score-Komponenten selbst, mit zwei Läufen derselben Engine und genau
einem Unterschied:

| Ändert sich die Lage so … | … muss das passieren |
|---|---|
| Gegner pickt zwei Tanks | Teambedarfs-Beitrag eines Anti-Tanks steigt — **und stärker** als der eines Brawlers ohne Anti-Tank |
| Gegner pickt einen Thrower | Anti-Thrower gewinnt relativ gegen einen Kandidaten ohne diese Antwort |
| Eigenes Team hat zwei Nahkämpfer | Abstand Reichweite ↔ weiterer Nahkämpfer wird größer |
| Ein gleichartiger Pick mehr im Team | Redundanzstrafe wächst monoton |
| Persönliche Sicherheit gesetzt | **nur** die persönliche Komponente ändert sich |

Die relativen Vergleiche sind der Kern: gegen Tanks steigt der Bedarf
für alle; die Aussage ist, dass er für den Anti-Tank *stärker* steigt.
Ein absoluter Vergleich würde auch anschlagen, wenn sich nur das Niveau
verschoben hätte.

Abgedeckt sind unter anderem: gebannte/gepickte Brawler verschwinden aus
den Vorschlägen, Anti-Tank steigt gegen Tanks, der dritte Tank wird
abgestraft, der persönliche Modifikator wirkt **und** bleibt gedeckelt,
Last-Pick-Gewichte unterscheiden sich von First-Pick-Gewichten, kleine
Stichproben senken die Confidence, Patches entwerten alte Daten, die
Siegchance bleibt in ihren Grenzen, ungültige Draftzustände werden
abgewiesen.

---

## 16. Datenarchitektur

### Zwei Rollen, streng getrennt

```
                    ┌─────────── Import (§17) ───────────┐   ┌──── Aggregation (§18) ────┐
MatchProvider ──▶ Lieferung ──▶ RawPayload ──▶ Match/Spieler ──▶ Brawler-/Counter-/Synergie-/Build-Stats
 · Fixture                     (unverändert)   (dedupliziert)                    │
 · offizielle API                                                                 ▼
                                                  StatProvider ──▶ Datenraum ──▶ DraftEngine
                                                   · Demo                         (Coach, Builds, Bans)
                                                   · gemessen / synthetisch
                                                   · Momentaufnahme
```

| Rolle | Liefert | Wer benutzt es | Methoden |
|---|---|---|---|
| `MatchProvider` | Rohmatches | nur der **Import** | `lieferungen()` |
| `StatProvider` | voraggregierte Statistiken | nur die **Engine** | `brawler_stats` (Meta), `counter_stats`, `synergy_stats`, `build_stats` |

**Die Engine liest nie Rohmatches.** Zwei Gründe: Eine Empfehlung hat rund
50 ms, eine Aggregation über hunderttausende Partien nicht. Und Glättung,
Zeit- und Patchgewichtung sollen an genau einer Stelle passieren — läse die
Engine Rohdaten, entstünde daneben eine zweite, abweichende Statistik. Ein
Test prüft auf SQL-Ebene, dass keine Empfehlung die Rohdaten-Tabellen berührt.

### Die Provider

| Provider | Rolle | Quelle |
|---|---|---|
| `DemoDataProvider` | Stat | gepflegte Werte (`demo` + `manual`) — die bisherigen Zahlen |
| `DatenbankStatProvider(quellen)` | Stat | voraggregierte Zeilen genau dieser Quellen |
| `SnapshotStatProvider` | Stat | feste Datensätze im Speicher (Tests, später Backtesting) |
| `FixtureDataProvider` | Match | JSON-Dateien (§17) |
| `OfficialBrawlAPIProvider` | Match | offizielle API — vorbereitet, **ohne** Parser (§19) |

`providers/registry.py` entscheidet, welcher Stat-Provider gilt
(`config.STAT_PROVIDER`, überschreibbar über `settings.DRAFTER_STAT_PROVIDER`):

- **`auto`** (Standard): gemessene Statistiken, sobald es welche gibt, sonst Demo.
  Synthetische Daten wählt `auto` **nie**.
- `demo`, `gemessen`, `synthetisch`: ausdrücklich.

Umgeschaltet wird **ganz, nicht zeilenweise**. Gibt es gemessene Daten, gelten
nur diese; fehlt für einen Brawler eine Messung, fällt die Engine auf ihre
Heuristik zurück und kennzeichnet das — statt eine ausgedachte Demo-Zahl neben
eine gemessene zu stellen, die in der Aufschlüsselung gleich aussähe.

### Datensätze statt Modellzeilen

Provider liefern `StatRecord`s, keine ORM-Objekte. Sonst hinge die Engine an
Feldnamen, Fremdschlüsseln und Lazy Loading der Datenbank, und jeder andere
Provider müsste so tun, als wäre er eine Tabelle. Die Attributnamen entsprechen
bewusst den Modellfeldern — die Umstellung hat keine Score-Komponente verändert.
Nachgewiesen: dieselben Datensätze aus einem anderen Provider ergeben
**identische** Empfehlungen und Matchpläne.

### Was jede Statistik kennt

| Feld | Bedeutung |
|---|---|
| `games`, `wins` | tatsächlich gezählt |
| `sample_size` | effektive Stichprobe: Summe der Zeit- und Patchgewichte (≤ games) |
| `raw_rate` | wins / games — ungeglättet, ungewichtet |
| `adjusted_rate` | gewichtet und Bayes-geglättet — **damit wird gerechnet** |
| `source` | demo · manual · fixture · synthetic · api · aggregated |
| `window_start`, `window_end`, `window_label` | Zeitraum (7d, 30d, 90d, seit_patch) |
| `patch`, `rank_pool`, `confidence` | Kontext und Belastbarkeit |

`sample_size` neben `games` ist der Punkt: 30 Spiele von vor einem Rework haben
`games=30`, aber kaum effektive Stichprobe — und genau das soll sichtbar sein.

Nicht gemessen sind `demo`, `manual` und `synthetic`. Beruht ein Draft nur auf
solchen Quellen, bleibt die Confidence bei höchstens 0,35.

### Welche Zeile der Datenraum nimmt

Zu einem Brawler kann es viele Zeilen geben. Jede Stufe schlägt alle folgenden:

```
Map (4) > Modus (2) > Rangbereich (0,5) > Zeitfenster (≤ 0,3) > Stichprobe (≤ 0,1)
```

Zeilen für eine *andere* Map oder einen *anderen* Modus sind nicht schwach
passend, sondern falsch und werden verworfen. Fenster-Vorrang:
`config.STAT_FENSTER_VORRANG` (seit Patch vor 7d vor 30d vor 90d).

---

## 17. Rohdaten und Import

```bash
docker compose run --rm --no-deps -T django-dev python manage.py import_brawl_fixture PFAD [--trockenlauf]
```

### Das Austauschformat `drafter.match.v1`

Eigenes, vollständig definiertes Format — kein erratenes API-Format.

```json
{
  "format": "drafter.match.v1",
  "herkunft": "synthetisch",
  "matches": [{
    "played_at": "2026-09-01T18:30:00Z",
    "mode": "Gem Grab",  "map": "Hard Rock Mine",
    "rank_pool": "masters",  "ranked": true,
    "winner": "a",  "first_pick": "a",
    "teams": {
      "a": [{"brawler": "Gale", "player_tag": "#…", "pick_order": 1,
             "build": {"gadget": "twister", "star_power": "freezing-snow", "gears": ["damage-gear"]}},
            {"brawler": "Belle"}, {"brawler": "Max"}],
      "b": [{"brawler": "Buster"}, {"brawler": "Gene"}, {"brawler": "Tick"}]
    },
    "bans": [{"brawler": "Mortis", "side": "a", "order": 1}],
    "duration_seconds": 142,  "external_id": null
  }]
}
```

- **`herkunft` ist Pflicht:** `synthetisch` · `api-mitschnitt` · `manuell-erfasst`.
  Ohne Herkunft wird nichts gespeichert — sonst läge eine Datei unbekannter
  Echtheit in den Rohdaten.
- `played_at` braucht eine Zeitzone; `winner` ist `a`, `b`, `draw` oder `null`.
- **Unbekannte Felder bleiben leer, nie geraten.** Pick-Reihenfolge, First Pick,
  Bans, Builds, Dauer und `external_id` sind optional.
- Eine fehlerhafte Partie verwirft nicht die Datei — sie wird benannt und übersprungen.

### Drei Garantien

1. **Idempotent je Lieferung.** Dieselbe Datei zweimal einspielen ändert nichts —
   erkannt am Inhaltshash (unabhängig von Einrückung und Schlüsselreihenfolge).
2. **Dedupliziert je Partie.** Dieselbe Partie steht in bis zu sechs Battlelogs,
   jeweils aus Sicht eines anderen Spielers. Der Fingerabdruck kanonisiert erst
   die Seiten (Sieger, First Pick und Bans wandern mit) und nutzt dann einen
   Zeit-Eimer von `MATCH_ZEITTOLERANZ_SEKUNDEN` samt Nachbar-Eimern. **Nicht** im
   Fingerabdruck: das Ergebnis (Widersprüche sollen als Konflikt auffallen) und
   Spieler-Tags (nicht jede Quelle liefert sie). Liefert die Quelle eine eigene
   Partie-ID, gewinnt diese.
3. **Nichts wird geraten.** Unbekannte Brawler und Maps bleiben mit ihrem
   gelieferten Namen gespeichert (Fremdschlüssel leer) und stehen im Bericht.
   Widersprüchliche Ergebnisse markieren die Partie als **Konflikt** — sie wird
   nie gezählt. Unentschieden und unbekannte Ergebnisse ebenso.

Die Rohantwort wird **unverändert** gespeichert (`RawPayload`). Ein später
korrigierter Parser kann alte Lieferungen neu auswerten, ohne die Quelle erneut
abzufragen.

---

## 18. Aggregation

```bash
docker compose run --rm --no-deps -T django-dev python manage.py aggregate_brawl_stats [--quelle gemessen|fixture|api|synthetisch] [--fenster …] [--rank-pool …] [--stichtag JJJJ-MM-TT]
docker compose run --rm --no-deps -T django-dev python manage.py rebuild_draft_stats   [--quelle …]
```

Je **Quelle × Rangbereich × Zeitfenster** entstehen Statistiken für Brawler
(Winrate, Pickrate, Banrate — global, je Modus, je Map), Counter, Synergien
(global, je Modus) und Builds, sofern Partien Build-Angaben tragen.

### Gewicht je Partie

```
gewicht = zeit_gewicht(Spieldatum) × patch_gewicht(je beteiligtem Brawler)
```

Wird Gale generft, verlieren **Gales** alte Partien an Gewicht — Belles in
denselben Partien nicht. Counter und Synergien bekommen das Produkt beider.

### Glättung mit dem besten verfügbaren Prior

| Statistik | Prior | Maßstab für den Vorteil |
|---|---|---|
| Brawler global | 90-Tage-Rate (im 90-Tage-Fenster selbst: 50 %) | — |
| Brawler je Modus / Map | Rate der gröberen Ebene | — |
| **Counter** A gegen B | **log5**: pA(1−pB) / (pA(1−pB) + pB(1−pA)) | Abweichung davon |
| **Synergie** A mit B | **additive Log-Odds**: logit P = logit pA + logit pB | Abweichung davon |
| Build | Grundrate des Brawlers | Abweichung davon |

Das beantwortet die beiden Denkfehler aus §7 mit Zahlen: ein Brawler, der gegen
alle 80 % holt, ist gegen einen bestimmten Gegner **kein** Counter; zwei starke
Brawler sind **keine** Synergie. Kleine Paar-Stichproben landen durch den Prior
bei „kein besonderer Vorteil" statt bei einem Zufallswert. Beides ist als Test
festgehalten.

Kurze Fenster schrumpfen zur langfristigen Rate statt zu 50 %: zwei aktuelle
Niederlagen kippen keine lange 80-%-Historie.

### Weitere Regeln

- **Banrate** nur über Partien, deren Quelle Bans kennt. Brawler, die nur
  gebannt und nie gespielt wurden, bekommen eine Zeile mit Banrate und
  **ohne** Winrate — sonst ginge ausgerechnet die aussagekräftigste
  Ban-Information verloren.
- **Synthetische Partien werden nie mit echten zusammen aggregiert**; Demo-
  und gepflegte Daten werden weder gelesen noch geschrieben.
- **Idempotent:** jeder Lauf ersetzt die Zeilen seines Kontexts vollständig.
- `rebuild_draft_stats` ordnet zusätzlich allen Partien ihren Patch neu zu —
  nötig, wenn ein Patch nachträglich eingetragen wird.
- `--stichtag` aggregiert rückwirkend, „aktueller Patch" gilt dann relativ
  dazu (Grundlage für Backtesting).

### Build-Statistiken in der Empfehlung

Gibt es sie, fließen sie in `builds.py` ein: Zuschlag
`BUILD_STAT_EINFLUSS × Vorteil × Confidence` auf die regelbasierten Punkte, mit
Begründung („in 500 vergleichbaren Partien über Gales Durchschnitt"). Nicht
gemessene Build-Statistiken werden als solche benannt. Ohne Build-Statistik ist
die Empfehlung **exakt** die regelbasierte.

---

## 19. Die offizielle API anschließen

Heute: ohne `BRAWL_STARS_API_KEY` meldet sich `OfficialBrawlAPIProvider` als
**nicht verfügbar**, ruft nichts ab und stürzt nicht ab. Mit Key speichert er
Antworten unverändert und markiert sie als „noch nicht auswertbar" — für das
offizielle Format ist **bewusst kein Parser registriert**.

Der Weg zu echten Daten, ohne Engine, Coach oder Frontend anzufassen:

1. **Key setzen** in der `.env` (`BRAWL_STARS_API_KEY=…`). Supercell bindet Keys
   an die **IP des abrufenden Servers**.
2. **Antworten mitschneiden** — der einzige Schritt, der das Netz braucht:
   ```python
   from drafter import config
   from drafter.services.providers.official_api import OfficialBrawlAPIProvider
   OfficialBrawlAPIProvider().rohantwort_sichern("#SPIELERTAG", config.FIXTURE_VERZEICHNIS)
   ```
   Die Datei enthält die Antwort **unverändert** unter `"antwort"`, in einer
   Hülle aus ausschließlich eigenen Schlüsseln.
3. **Dateien ansehen** und die tatsächliche Struktur dokumentieren: Gibt es eine
   Partie-ID? Wie genau stimmen Zeitstempel zwischen Spielern überein? Stehen
   Ranked-Bans, Pick-Reihenfolge, Builds, Rangangaben darin? (§20)
4. **Parser schreiben** — `parse_offizieller_battlelog(daten) -> ParseErgebnis`
   in `services/ingest/parser.py`, getestet gegen genau diese Dateien — und
   registrieren:
   ```python
   PARSER[FORMAT_OFFIZIELLER_BATTLELOG] = parse_offizieller_battlelog
   ```
   Der Parser übersetzt in `MatchRecord`s mit **perspektivfreien** Seiten a/b
   und lässt alles leer, was die Antwort nicht enthält.
5. **Importieren und aggregieren** — `import_brawl_fixture`, dann
   `aggregate_brawl_stats --quelle fixture`. Ab jetzt nimmt `auto` die
   gemessenen Statistiken, und die Oberfläche hebt den Demo-Hinweis auf.
6. Später: Crawler (Ranglisten → Battlelogs → neu entdeckte Spieler), mit
   Ratenlimit, `last_fetched_at` und Priorität — als weiterer `MatchProvider`,
   ohne dass sich Import oder Aggregation ändern.

---

## 20. Offene Datenfragen

Bewusst **nicht** beantwortet, weil sie nur echte Antworten beantworten können:

| Frage | Warum sie zählt | Wo es hängt |
|---|---|---|
| Welche Felder hat eine Battlelog-Antwort, und was bedeuten sie? | Grundlage des Parsers | §19 Schritt 3 |
| Gibt es eine eindeutige Partie-ID? | sonst Rekonstruktion per Fingerabdruck | `fingerprint.py` |
| Wie genau stimmen Zeitstempel derselben Partie überein? | Toleranz `MATCH_ZEITTOLERANZ_SEKUNDEN` (60 s) ist geschätzt | `config.py` |
| Liefert die API Ranked-**Bans**? Die **Pick-Reihenfolge**? First Pick? | ohne sie keine Banrate, keine gelernten Draft-Positionen | Aggregation zählt nur Vorhandenes |
| Liefert sie **Builds** historischer Partien? | sonst bleibt `BuildStat` leer | Build-Empfehlung läuft weiter auf Regeln |
| Wie ist der **Rangbereich** einer Partie erkennbar? | Rang-Pools (Legendary+, Masters, Pro) | `Match.rank_pool` |
| Heißen Maps/Modi/Brawler in der API wie im Katalog? | sonst unbekannt im Import-Bericht; ggf. Aliasliste nötig | `katalog_schluessel()` |
| Wie viele Partien sind realistisch? | Paarzeilen wachsen quadratisch mit Brawlern × Ebenen × Fenstern × Pools — bei ~90 Brawlern Hunderttausende Zeilen; ggf. Mindeststichprobe für Paare | `aggregator.py` |
| Gewichtete Kombination der Rang-Pools (`RANG_POOL_GEWICHT`)? | derzeit je Pool getrennt aggregiert, die Gewichte werden noch nicht benutzt | `config.py` |
| Counter in beide Richtungen gemessen | `counters.vorteil` zieht die Gegenrichtung mit Faktor 0,8 ab; gemessene Counter sind symmetrisch, ein Matchup zählt dann effektiv 1,8-fach. Vor dem Umstieg prüfen — **nicht** jetzt an Demo-Daten tunen | `counters.py` |

---

## 21. Nächste Schritte

1. **Echte Antworten mitschneiden und den Parser schreiben** (§19).
2. **Crawler** als weiterer `MatchProvider`, mit Ratenlimit und Deduplizierung
   über den bestehenden Import.
3. **Aggregation planen** (Cron, später Celery Beat) — nie live aggregieren.
4. **Gelernte Gewichte** statt `config.PHASEN_GEWICHTE`, sobald genug saubere
   Partien vorliegen.
5. **Backtesting** mit `--stichtag` und `SnapshotStatProvider`: „was hätte das
   System an diesem Punkt empfohlen?" Dabei dürfen **nur** Informationen
   einfließen, die zu diesem Zeitpunkt im Draft bekannt waren — spätere Picks
   als Merkmal zu benutzen wäre Data Leakage.
6. **Brawler-Bilder** — `Brawler.image_url` ist vorbereitet; die Artworks
   gehören Supercell und liegen deshalb nicht im Repository.
7. **Mehr Brawler** — die Architektur trägt alle; gepflegt sind 20.
