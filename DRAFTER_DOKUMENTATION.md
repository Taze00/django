# 🎯 Draft Coach — Brawl-Stars-Ranked-Assistent

> Die vollständige Erklärung zum Drafter unter `/draft/`. Die kompakte
> Arbeitsreferenz steht in `CLAUDE.md`; diese Datei erklärt das *Warum*.
>
> **Stand:** September 2026 · MVP mit gekennzeichneten Demo-Daten

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
Zahlenbasis. Sobald Matchdaten existieren, treten sie neben die
Demo-Zeilen — die Kontextfelder der Stat-Tabellen sind von Anfang an
dafür gebaut, es braucht keine Migration der Wertespalten.

---

## 3. Aufbau

```
drafter/
├── attributes.py     ← das Vokabular (32 Eigenschaften, 6 Draftwerte, 9 Rollen)
├── config.py         ← ALLE Stellschrauben (Gewichte, Schwellen, Grenzen)
├── seed_data.py      ← der Demo-Datensatz
├── models/           ← Katalog, Maps, Patches, Statistiken, Builds, Nutzerwerte
├── services/         ← die gesamte Logik, ein Thema je Datei
│   ├── context.py         DraftContext — der Zustand als ein Objekt
│   ├── scoring.py         der Score-Vertrag ([-1,+1]) und die Ergebnistypen
│   ├── daten.py           lädt alle Statistiken in wenigen Abfragen
│   ├── team_coverage.py   Teamprofil, Lücken, Redundanz  ← Herzstück
│   ├── team_need.py       Bedarf, Redundanz, Angreifbarkeit als Komponenten
│   ├── counters.py        Counter (gepflegt + Heuristik)
│   ├── synergies.py       Synergie als Mehrwert, nicht als gemeinsame Winrate
│   ├── map_fit.py         Passung zu Map und Modus
│   ├── meta.py            aktuelle Stärke aus Statistiken
│   ├── patch_weighting.py Zeit- und Patchabschlag, Bayes-Glättung
│   ├── draft_position.py  Blind Pick vs. Last Pick
│   ├── personal.py        persönliche Sicherheit (hart gedeckelt)
│   ├── confidence.py      wie sicher ist sich das System
│   ├── bans.py            Ban-Coach
│   ├── builds.py          Gadget/Star Power/Gears aus Regeln
│   ├── coach.py           aus Struktur werden Sätze
│   ├── win_probability.py Provider-Interface + Heuristik
│   ├── draft_engine.py    der Orchestrator — rechnet selbst nichts
│   ├── brawl_api_client.py  Gerüst für die offizielle API
│   └── providers/         MatchData / MetaData / BuildData
├── views/            ← pages.py (3 Seiten) + api.py (5 Endpunkte)
└── tests/            ← 93 Tests, ein Thema je Datei
```

Dazu außerhalb der App, der Projektkonvention folgend:
`templates/drafter/` und `static/drafter/`.

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
`win_rate` behält die Rohmessung daneben. Gibt es keinen gepflegten
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

Geliefert werden je Spieler: Rolle im Team, bis zu drei Aufgaben,
„nicht deine Aufgabe", Warnungen, bevorzugtes Matchup und Build — und
fürs Team: Win Condition, Matchup-Zuordnung (beste **Gesamtsumme** über
alle sechs Permutationen, nicht das beste Einzelduell),
Startpositionen als *Vorschlag* und ein Lane-Tausch-Plan.

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

**Geschwindigkeit:** rund 30 ms und 17 Abfragen je Empfehlung. Der
Datenraum lädt alles einmal vor, teure Auskünfte (Siegchance,
Coach-Texte, Build) entstehen nur für die angezeigte Spitze.

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

93 Tests, rund 30 s. Sie laufen gegen den echten Demo-Datensatz statt
gegen erfundene Testobjekte: der Seed ist Teil der Auslieferung, und mit
handgebauten Miniaturbrawlern würden die Tests an ihm vorbeiprüfen.

Abgedeckt sind unter anderem: gebannte/gepickte Brawler verschwinden aus
den Vorschlägen, Anti-Tank steigt gegen Tanks, der dritte Tank wird
abgestraft, der persönliche Modifikator wirkt **und** bleibt gedeckelt,
Last-Pick-Gewichte unterscheiden sich von First-Pick-Gewichten, kleine
Stichproben senken die Confidence, Patches entwerten alte Daten, die
Siegchance bleibt in ihren Grenzen, ungültige Draftzustände werden
abgewiesen.

---

## 16. Die offizielle API — bewusst noch nicht angebunden

`services/brawl_api_client.py` steht als Gerüst: Key ausschließlich aus
der Umgebung (`BRAWL_STARS_API_KEY`), Ratenbegrenzung, Zeitlimits,
saubere Fehlertypen, Tag-Normalisierung.

**Er interpretiert bewusst keine Antwortfelder.** Es ist ungeprüft, ob
die API historische Draft-Bans, Build-Daten oder die genaue
Pick-Reihenfolge überhaupt liefert. Wer jetzt
`antwort["battles"][0]["battle"]["teams"]` schreibt, erfindet eine
Struktur und baut den Rest darauf. Die Auswertung entsteht, wenn eine
echte Antwort vorliegt.

> Nicht vergessen: Supercell bindet API-Keys an die **IP des abrufenden
> Servers**. Ein Key, der lokal funktioniert, funktioniert auf dem
> Server nicht automatisch.

---

## 17. Nächste Schritte

1. **Matchsammler** (`collect_brawl_matches`) — sobald der Key da ist:
   erst echte Antworten ansehen, dann Rohmatch-Modelle entwerfen.
   Deduplikation über einen Fingerabdruck, Ratenlimit, `last_fetched_at`,
   keine Endlosschleife.
2. **Aggregator** (`aggregate_brawl_stats`) — Rohmatches → Stat-Tabellen,
   mit Zeitfenstern, Rangpools und Bayes-Glättung. Nie live aggregieren.
3. **Gelernte Gewichte** statt `config.PHASEN_GEWICHTE`.
4. **Backtesting** — „was hätte das System an diesem Punkt empfohlen?"
   Dabei dürfen **nur** Informationen einfließen, die zu diesem Zeitpunkt
   im Draft bekannt waren; spätere Picks als Merkmal zu benutzen, wäre
   Data Leakage und würde die Bewertung wertlos machen.
5. **Brawler-Bilder** — `Brawler.image_url` ist vorbereitet. Die Artworks
   gehören Supercell und liegen deshalb nicht im Repository; ohne URL
   zeigt die Oberfläche eine eingefärbte Kachel mit Kürzel.
6. **Mehr Brawler** — die Architektur trägt alle; gepflegt sind 20.
