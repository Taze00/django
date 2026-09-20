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
`templates/drafter/`, `static/drafter/` und `data/brawl_api_raw/`
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
| Current Strength | Beta-Binomial-Posterior über `BrawlerStat`, **am Feld gemessen** |
| Counter | `CounterStat`, sonst Heuristik aus sechs Attributsignalen |
| Synergie | `SynergyStat`, sonst Heuristik (Ergänzung, nicht Summe) |
| Teambedarf | Dringlichkeit × **Zuwachs am Teamprofil** |
| Draft-Position | `draft_values` je nach Phase + Konterbarkeit |
| Deine Sicherheit | persönliche Confidence, gedeckelt |
| Flexibilität | `flexibility_value` |
| − Redundanz | Attributüberschuss + Rollenüberhang + „bringt nichts Neues" |
| − Angreifbarkeit | Restlücken × Fähigkeit des Gegners, sie auszunutzen |
| − Datenlage | Rückstand auf die Confidence-**Mitte des Feldes** |

### Drei Aussagen, nie eine Zahl
**CURRENT STRENGTH** (läuft er gerade), **DRAFT FIT** (passt er hier) und
**PERSÖNLICH** (beherrscht der Spieler ihn) stehen getrennt in jeder
Antwort (`erklaerung`), zusammen mit Datenabdeckung und statistischer
Sicherheit. Gepflegtes Wissen — Attribute, Rolle, Fähigkeiten — speist
ausschließlich den Draft Fit; es kann **nie** als aktuelle Stärke zählen.
Dass ein Brawler Wände bricht, sagt nichts darüber, ob er gewinnt.

### Unbekanntes bleibt neutral
Eine Komponente, die für einen Brawler nicht berechenbar ist, trägt 0 bei
und wird **nicht** durch Hochrechnen der übrigen ersetzt. Bis zum
18.09.2026 rechnete `Empfehlung.skalierung` die verbliebenen Gewichte auf
100 % hoch — wer nur über eine einzige Komponente bekannt war, bekam
deren Wert vervierfacht, und je weniger man über einen Brawler wusste,
desto weiter oben stand er. Wie viel bekannt ist, steht jetzt getrennt in
`datenabdeckung` und in der Confidence, nicht im Score.

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

### Gepflegte, gemessene und geschätzte Counter

Ein Counter-Wert bedeutet je nach Quelle etwas anderes — deshalb gibt es drei
Rechenwege in `counters.vorteil`:

| Quelle | Lesezugriff | Bedeutung | Gegenrichtung |
|---|---|---|---|
| gepflegt (`demo`, `manual`) | `manual_counter_score` | gerichtete Einschätzung („Gale stößt Bull weg") | eigene Zeile, **darf asymmetrisch sein**; Netto = hin − 0,8 · her |
| gemessen (`fixture`, `api`, `aggregated`, `synthetic`) | `measured_counter_advantage` | Abweichung der geglätteten Paar-Siegquote von der log5-Erwartung | **exakt das Negativ** — abgeleitet, nicht abgezogen |
| keine Zeile | Heuristik | aus Attributen geschätzt | wie gepflegt, hin − 0,8 · her |

Warum die Trennung nötig war: Früher liefen alle Zeilen durch „hin − 0,8 · her".
Für gepflegte Werte ist das richtig. Gemessene Werte sind aber gegengleich
(her = −hin), und die Formel ergab hin + 0,8 · hin — **dasselbe Matchup zählte
1,8-fach**. Jetzt gilt für gemessene Counter: `vorteil(A, B) == −vorteil(B, A)`.

Gemessene Counter werden je Paar **nur in einer Richtung** gespeichert (kleinere
Brawler-ID zuerst). Ein Datenbank-Constraint lässt die Gegenrichtung für
berechnete Quellen gar nicht zu; Doppelzählung ist damit strukturell unmöglich,
nicht nur per Konvention. Liegen für ein Paar Pflege und Messung zugleich vor,
gilt die Messung.

Die beiden 0,8 standen vorher als Zahl im Engine-Code und liegen jetzt
unverändert in `config.py` (`GEPFLEGTER_COUNTER_GEGENRICHTUNG`,
`HEURISTISCHER_COUNTER_GEGENRICHTUNG`). Für die Demo-Daten ist das Ergebnis
identisch — nachgeprüft an 18 Draft-Lagen vor und nach dem Umbau.

Getrennt wird über zwei benannte Zugriffe auf denselben Wert, **nicht** über zwei
Spalten: zwei Spalten, von denen je nach Quelle genau eine gefüllt sein dürfte,
erlaubten einen ungültigen Zustand (beide gefüllt), den `source` ohnehin ausschließt.

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
- **Stichprobe**: Beta-Binomial-Posterior gegen einen Prior von 120
  Spielen. Damit schlägt „62 % aus 150 Spielen" nicht mehr „59 % aus
  30 000" — ein eigener Test hält genau diesen Fall fest. 1 Sieg aus
  1 Spiel landet bei 50,4 %, 1100 aus 2000 bei 54,7 %.
- **Ebenen**: global, Modus und Map zählen **zusammen**, die gröberen mit
  Abschlag, jede Partie genau einmal (die Ebenen sind verschachtelt).
  Früher gewann die spezifischste Zeile — eine Map-Zeile mit 4 Partien
  verdrängte eine globale mit 44.
- **Feldskalierung**: Der Score-Wert ist die Lage im Feld,
  `(rate − Median) / (2·√(Feldstreuung² + eigene sd²))`, nicht der
  Abstand zu festen 50 %. Echte Siegquoten liegen zwischen 45 und 58 %;
  `(rate − 0.5) × 2` machte aus 22 % nominellem Gewicht real etwa 1 %.
  Die eigene Streuung steht im Nenner, weil die Feldstreuung (robust
  0,012) kleiner ist als die typische Einzelunsicherheit (0,041) — ohne
  sie würde aus Rauschen Signal.
- **Pickrate**: senkt die *Sicherheit* einer Siegquote, nie ihren Wert.
  Selten gespielt heißt „von Spezialisten gespielt", nicht „schlecht".
- **Keine Mindestzahl von Partien.** Eine einzige Partie ist eine
  Beobachtung; wie wenig sie wiegt, entscheiden Posterior und Confidence.
  `n = 0` dagegen heißt **Unknown**, nicht 50 % — ein Prior ist eine
  Annahme, keine Messung.

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

**Geschwindigkeit:** rund 45 ms und 17 Abfragen je Empfehlungsanfrage (gemessen nach der Provider-Umstellung; die drei zusätzlichen gegenüber vorher sind die `auto`-Prüfung auf gemessene Daten und das Laden der Build-Statistiken),
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
docker compose run --rm --no-deps -T django-dev python manage.py seed_brawl_data

# Demo-Daten vorher löschen - manuell gepflegte bleiben stehen
docker compose run --rm --no-deps -T django-dev python manage.py seed_brawl_data --reset
```

Im Admin lässt sich alles bearbeiten. **Achtung:** `seed_brawl_data`
gleicht Demo-Daten wieder an die Datei an. Wer Änderungen behalten will,
stellt `source` auf „Manuell gepflegt" — `--reset` fasst sie dann nicht
an.

---

## 15. Tests

```bash
docker compose run --rm --no-deps -T django-dev python manage.py test drafter \
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
- **IDs vor Namen.** `brawler_id`, `mode_id`, `map_id` (auch in Bans) sind
  optional und haben Vorrang: der Import ordnet zuerst über
  `Brawler.external_id` / `BrawlMap.external_id` / `GameMode.external_id` zu und
  nimmt den Namen nur als Rückfall. Mit ID ist der Name optional. Die
  `external_id`-Felder im Katalog bleiben **leer, bis echte Antworten die IDs
  zeigen** — sie werden nicht erfunden. Der Import-Bericht zählt, wie viele
  Brawler per ID und wie viele per Name zugeordnet wurden.
- **Unbekannte Felder bleiben leer, nie geraten.** Pick-Reihenfolge, First Pick,
  Bans, Builds, Dauer und `external_id` sind optional.
- Eine fehlerhafte Partie verwirft nicht die Datei — sie wird benannt und übersprungen.

### Drei Garantien

1. **Idempotent je Lieferung.** Dieselbe Datei zweimal einspielen ändert nichts —
   erkannt am Inhaltshash (unabhängig von Einrückung und Schlüsselreihenfolge).
2. **Dedupliziert je Partie** — in fester Rangfolge:
   - **Partie-ID der Quelle, exakt.** Stimmt `external_id` überein, ist es
     dieselbe Partie — ohne Zeittoleranz. Zwei Sichtungen mit *verschiedenen*
     IDs sind zwei Partien, auch wenn Zeit, Map und Teams zusammenpassen.
   - **Nur als Fallback: rekonstruierter Fingerabdruck.** Ohne ID wird die
     Partie aus Ort (Map-ID aus dem Katalog, sonst Namen), Teams (Brawler-IDs
     aus dem Katalog, sonst Namen, vorher kanonisiert — Sieger, First Pick und
     Bans wandern mit) und einem Zeit-Eimer von `MATCH_ZEITTOLERANZ_SEKUNDEN`
     samt Nachbar-Eimern wiedererkannt. **Die 60-Sekunden-Toleranz existiert nur
     hier** und ist geschätzt.

   Der Fingerabdruck geht über die **Katalog-Identität**, auf die ID und Name
   beide aufgelöst werden — eine Sichtung mit IDs und eine mit Namen führen so
   zur selben Partie. Der rekonstruierte Fingerabdruck wird auch bei bekannter
   Partie-ID gespeichert (`reconstructed_fingerprint`), damit eine spätere
   Sichtung *ohne* ID die Partie wiederfindet. **Nicht** im Fingerabdruck: das
   Ergebnis (Widersprüche sollen als Konflikt auffallen) und Spieler-Tags
   (nicht jede Quelle liefert sie).
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
- **Counter: eine Zeile je Paar** (kleinere Brawler-ID zuerst), gezählt aus
  deren Sicht. Die Gegenrichtung leitet die Engine ab (§7).
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

### Offizielle Brawl Stars API

**Umgebungsvariable:** `BRAWL_STARS_API_KEY` in der gitignorten `.env`. Sie wird
über `docker-compose.yml` durchgereicht, in `settings.py` gelesen und nur über
`drafter.config.api_key()` abgefragt. Sie ist bewusst **kein** Argument eines
Commands (Argumente landen in Shell-History und Prozesslisten).

- `docker compose run --rm …` liest die `.env` bei jedem Start neu.
- Ein **laufender** Container übernimmt eine geänderte `.env` erst nach
  `docker compose up -d --force-recreate django-dev`. Die Webseite selbst ruft
  die API nicht auf — für Tests und Mitschnitte ist das nicht nötig.

**Key anlegen:** im Developer-Portal (developer.brawlstars.com) einen Key anlegen
und dabei die **öffentliche IP des Servers** als erlaubte Adresse eintragen.

**IP-Freigabe:** Supercell bindet jeden Key an die eingetragenen IP-Adressen.
Anfragen von einer anderen IP werden abgelehnt (403). Der Server hängt an einer
DynDNS-Adresse — **ändert sich seine öffentliche IP, muss der Key angepasst
oder neu angelegt werden.** Der Client meldet 403 mit genau diesem Hinweis und
gibt Supercells eigene Begründung mit aus.

**Geheimhaltung, technisch durchgesetzt:**
- Der Key steht nur im `Authorization`-Header der ausgehenden Anfrage.
- Gespeichert werden ausschließlich **Antwort**-Header.
- Der Key liegt privat am Client, `repr()` zeigt ihn nicht, Fehlermeldungen
  werden bereinigt, und Fehler werden ohne Ausnahme-Kette geworfen.
- Tests prüfen, dass er in keiner Meldung, keinem Log und keiner Datei auftaucht.

**Testbefehle** (importieren und aggregieren nichts):

```bash
docker compose run --rm --no-deps -T django-dev python manage.py test_brawl_api --brawlers
docker compose run --rm --no-deps -T django-dev python manage.py test_brawl_api --player "#SPIELERTAG"
docker compose run --rm --no-deps -T django-dev python manage.py test_brawl_api --analysiere data/brawl_api_raw/DATEI.json
```

`--analysiere` gibt die Feldstruktur einer gespeicherten Antwort aus — Pfade,
Typen, Häufigkeit, **keine Werte**. So lässt sich die Struktur zeigen, ohne
Spielernamen oder Tags auszugeben.

**Speicherort:** `data/brawl_api_raw/` (gitignored — echte Antworten enthalten
Spieler-Tags), eine Datei je Abruf, z. B. `battlelog_<TAG>_<Zeitstempel>.json`.
Jede Datei ist eine Hülle aus eigenen Schlüsseln um die **unveränderte** Antwort:

| Schlüssel | Inhalt |
|---|---|
| `format` | `brawlstars.player.raw`, `brawlstars.battlelog.raw`, `brawlstars.brawlers.raw` |
| `herkunft` | `api-mitschnitt` |
| `referenz` | Spieler-Tag bzw. `alle` |
| `endpoint` | abgefragter Pfad, z. B. `/players/%23TAG/battlelog` |
| `http_status` | Status der Antwort |
| `antwort_header` | Antwort-Header (ohne `set-cookie`) — für Rate-Limit-Hinweise |
| `abgerufen_am` | Zeitpunkt (UTC) |
| `antwort` | die JSON-Antwort, unverändert |

**Fehlerbehandlung** im Client (`services/brawl_api_client.py`): 401 → Key
fehlt/ungültig · 403 → Zugriff verweigert, meist IP-Freigabe · 404 → nicht
gefunden, meist falscher Tag · 429 → Ratenlimit · 5xx → Fehler/Wartung bei der
API · Zeitüberschreitung (12 s) und Netzwerkfehler. Jede Meldung nennt den
Endpoint und Supercells `reason`/`message`, sofern die Fehlerantwort sie enthält.

**Lage der Dokumentation:** Die öffentliche Swagger-Oberfläche des Portals
(`/api-docs/index.html`) enthält **keine** Spezifikation. Die Adresse wird erst
nach dem Anmelden mit einem temporären Token übergeben. Ohne Login ließ sich
deshalb kein einziger Endpoint belegen. Eingebaut und abgerufen werden nur die
ausdrücklich gewünschten Pfade `/players/{playerTag}`,
`/players/{playerTag}/battlelog` und `/brawlers`. **Ranking-Endpoints sind nicht
eingebaut**, bis ihre Pfade aus der Spezifikation vorliegen.


### Was die echten Antworten enthalten (Mitschnitt 2026-09-15)

Ausgewertet wurden drei Antworten: `/brawlers`, `/players/{tag}` und
`/players/{tag}/battlelog` eines Spielers (25 Einträge). Alles hier ist
**beobachtet**, nicht aus Swagger-Modellnamen abgeleitet. Eine anonymisierte
Kopie des Battlelogs liegt als Test-Fixture unter
`drafter/testdaten/offizieller_battlelog_anonymisiert.json`.

**Antwort-Header:** `date`, `content-type`, `content-length`, `connection`,
`x-content-type-options`, `strict-transport-security`, `cache-control: max-age=3`.
**Keine** Rate-Limit-Header. Über das erlaubte Limit ist damit nichts bekannt.

**Battlelog** — Wurzel `items` (25) und `paging` (`cursors: {}`). Ein Eintrag:

| Feld | Beobachtung |
|---|---|
| `battleTime` | `20260914T184146.000Z` — UTC, sekundengenau |
| `event.id` | Ganzzahl, in diesem Log 1:1 zur Map (7 Maps). Stabilität über Zeit **unbelegt** |
| `event.map` | Name, z. B. `Undermine` |
| `event.mode` / `battle.mode` | camelCase: `brawlBall`, `gemGrab`, `hotZone`, `knockout`, `bounty`, `soloShowdown` — immer gleich |
| `event.modeId` | Ganzzahl, 1:1 zum Modus (`gemGrab` 0, `bounty` 3, `brawlBall` 5, `soloShowdown` 6, `hotZone` 17, `knockout` 20) |
| `battle.type` | `ranked` (21×) oder `soloRanked` (4×) — siehe unten |
| `battle.result` | `victory` / `defeat`, **aus Sicht des abgefragten Spielers**; fehlt bei Showdown |
| `battle.duration` | 21–150, Einheit nicht dokumentiert (plausibel: Sekunden) |
| `battle.trophyChange` | nur bei `ranked` (20 von 21) |
| `battle.starPlayer` | `{tag, name, brawler}`, immer auch in `teams` |
| `battle.teams` | 2 × 3 Spieler `{tag, name, brawler{id, name, power, trophies}}` |
| `battle.players` + `battle.rank` | statt `teams` bei `soloShowdown` |

**`ranked` ist nicht Ranked.** `ranked` ist die Trophäen-Rangliste: mit
`trophyChange`, Brawler-Trophäen bis 2188, auch Showdown. Der Ranked-Modus
heißt `soloRanked`. Dort gibt es keine `trophyChange`, und `brawler.trophies`
ist bei allen sechs Spielern gleich (11–12). Das entspricht dem `rankedRank` 12
im Profil des abgefragten Spielers. **Beleg: 4 Partien eines Spielers.** Der
Parser setzt `is_ranked` deshalb nur für `soloRanked` und speichert den Rohwert
in `Match.battle_type`, damit sich die Deutung korrigieren lässt.

**Die Seiten sind nicht fest.** Der abgefragte Spieler stand 11× in `teams[0]`
und 6× in `teams[1]`. Der Parser rechnet `result` über den Spieler-Tag aus
`referenz` auf eine Seite um.

**Nicht im Battlelog:** Partie-ID, Bans, Pick-Reihenfolge, First Pick, Gadget,
Star Power, Gear, Hypercharge, Elo, Rangbereich der Partie. Keins dieser Felder
wird gelesen oder rekonstruiert.

**Spielerprofil** — nur hier, nicht pro Partie: Trophäen/Rekord, Siege je Modus,
Club, `rankedSeasonId`, `rankedRank`/`rankedRankName`/`rankedElo`, Saison- und
Allzeit-Höchstwerte, und je besessenem Brawler `power`, `rank`, Trophäen,
Win-Streaks, Skin, `gadgets`/`starPowers`/`gears`/`hyperCharges` (**besessen**,
nicht ausgerüstet) und `buffies`.

**`/brawlers`** — 108 Brawler mit stabil aussehenden Ganzzahl-IDs
(16000000–16000110), Namen in GROSSBUCHSTABEN (`8-BIT`, `MR. P`, `LARRY & LAWRIE`).
Dazu je 2 Gadgets, 2 Star Powers, 0–1 Hypercharge und 6–8 Gears (globaler Katalog von
19 Gear-IDs). Alle 20 Demo-Brawler sind per Namen auffindbar. `external_id` ist im
Katalog **noch nicht gesetzt** (Demo-Daten unverändert). Die Zuordnung läuft
bis dahin über Namen.

### Der Parser `parse_offizieller_battlelog`

Registriert für `brawlstars.battlelog.raw`. Er erwartet die eigene Hülle
(die Perspektive kommt aus `referenz`) und liest ausschließlich die Felder oben:

| MatchRecord | aus |
|---|---|
| `played_at` | `battleTime` (UTC) |
| `mode` / `external_mode_id` | `battle.mode` / `event.modeId` |
| `map` / `external_map_id` | `event.map` / `event.id` |
| `teams["a"]` / `["b"]` | `battle.teams[0]` / `[1]`, je Spieler Tag, Brawler-ID **vor** Name, `power`, `trophies` (roh) |
| `winner` | `result` über den Tag aus `referenz` umgerechnet; unbekannter Wert → leer |
| `duration_seconds` | `battle.duration` |
| `battle_type` / `ranked` | `battle.type` / `type == "soloRanked"` |
| `external_id` | **leer** — es gibt keine Partie-ID |
| `bans`, `first_pick`, `pick_order`, `build`, `rank_pool` | leer bzw. `alle` |

Einträge ohne zwei Teams (Showdown) sind **übersprungen**, nicht ungültig: Sie
werden getrennt gezählt und in `RawPayload.parse_message` genannt. Ein kaputter
Eintrag verwirft nur sich selbst. Unbekannte Zusatzfelder werden ignoriert.

`katalog_schluessel()` trennt camelCase (`brawlBall` → `brawl-ball`), damit die
Namens-Rückfallsuche die Modi findet. `Match.mode_name` bleibt roh.

**Wiedererkennung:** Ohne Partie-ID läuft sie über den rekonstruierten
Fingerabdruck (Brawler-Aufstellung, Ort, Zeit-Eimer). Dieselbe Partie aus dem
Battlelog eines Gegners — Seiten und Ergebnis gespiegelt — ist eine Dublette
ohne Konflikt. Der Test hält es fest. Wie genau `battleTime` bei zwei Spielern
derselben Partie übereinstimmt, ist mit einem einzigen Battlelog **nicht messbar**.
Die 60 s Toleranz bleibt deshalb geschätzt.

### Geprüfte Endpoints (2026-09-15)

Alle Kandidaten wurden mit einer echten Anfrage geprüft. Eingebaut ist nur,
was mit HTTP 200 geantwortet hat.

| Pfad | Antwort | Inhalt |
|---|---|---|
| `/brawlers` | 200 | 108 Brawler mit `id`, `name`, Gadgets, Star Powers, Gears, Hypercharges |
| `/players/{tag}` | 200 | Profil samt `rankedRank`, `rankedElo`, besessene Ausrüstung |
| `/players/{tag}/battlelog` | 200 | letzte 25 Partien |
| `/rankings/global/players` | 200 | Top 200 **nach Trophäen**: `tag`, `name`, `trophies`, `rank` |
| `/rankings/global/brawlers/{id}` | 200 | Top 200 je Brawler, ebenfalls nach Trophäen |
| `/rankings/global/clubs` | 200 | Top 200 Clubs |
| `/events/rotation` | 200 | 16 laufende Events mit `id`, `mode`, `modeId`, `map` |
| `/rankings/global/powerplay/seasons` | **404** | gibt es nicht (mehr) |

**Es gibt keine Ranked-Rangliste nach Elo.** Alle Ranglisten sind
Trophäenlisten. Wer Ranked-Spieler sucht, findet sie nur über den Umweg:
Top-Trophäenspieler abrufen und aus deren `soloRanked`-Partien die Mitspieler
entdecken.

**`/events/rotation` zeigt außerdem**, dass `event.id` Map UND Modus zusammen
bezeichnet: „Doom Shroom" hat drei IDs, je eine für Solo-, Duo- und
Trio-Showdown. Ranked-Maps stehen nicht in der Rotation.

### Der Collector

`services/collector.py`, Befehl `collect_brawl_matches`. Vier Schritte je Lauf:

1. **Katalog** `/brawlers` → IDs eintragen, unbekannte Brawler inaktiv anlegen.
2. **Saat** `/rankings/global/players` → bis zu 200 Spieler, Tiefe 0.
3. **Battlelogs** `/players/{tag}/battlelog` → höchstens `--max-spieler` Abrufe.
4. **Entdecken** Mitspieler aus **soloRanked**-Partien → Tiefe + 1.

**Drei Bremsen gegen unkontrollierte Rekursion**, gleichzeitig wirksam:

- **Budget** — `--max-spieler` (Standard 25) begrenzt die Battlelogs je Lauf.
- **Tiefe** — `--max-tiefe` (Standard 1). Jenseits davon werden Spieler nicht
  einmal gespeichert, nicht nur nicht abgerufen.
- **Abrufabstand** — derselbe Spieler frühestens nach
  `COLLECTOR_ABRUF_ABSTAND_STUNDEN` (Standard 6) erneut. Dafür trägt jeder
  `TrackedPlayer` sein `last_fetched_at`.

**Fehlerverhalten:**

| Fall | Reaktion |
|---|---|
| 401 / 403 | Lauf sofort beenden — Key oder IP-Freigabe betreffen jede weitere Anfrage |
| 429 | nach den Wiederholungen des Clients: Lauf beenden, der Spieler bleibt offen |
| 404 | Spieler markieren, 7 Tage Pause, weiter zum nächsten |
| 5xx, Netz | nach den Wiederholungen: Pause je Spieler 1 h, 2 h, 4 h … bis 48 h; nach 3 solchen Fehlern in Folge endet der Lauf |
| Parserfehler | Rohantwort trotzdem speichern, Spieler markieren, weiter |

Der Client wiederholt 429, 5xx und Zeitüberschreitungen bis zu `API_VERSUCHE`-mal
(Standard 4) mit exponentieller Pause; bei 429 gilt `Retry-After`, falls die
Antwort ihn nennt. 401, 403 und 404 werden **nie** wiederholt — ein zweiter
Versuch ändert daran nichts.

Jeder Lauf wird als `CollectorRun` protokolliert (Parameter und vollständiger
Bericht als JSON). `python manage.py brawl_datenlage` zeigt jederzeit ohne Netz,
was vorliegt.

### Katalog: IDs vor Namen

`services/katalog.py` trägt IDs ein und legt Fehlendes an — **aber nie
Eigenschaften**:

- Ein gepflegter Eintrag bekommt nur seine bis dahin **leere** `external_id`.
  Trägt er schon eine andere, ist das ein gemeldeter Konflikt.
- Ein **neuer** Brawler bekommt Name und ID, sonst nichts: keine Rolle, keine
  Eigenschaften, keine Draft-Werte — und `is_active=False`. Grund: eine fehlende
  Eigenschaft zählt im Modell als 0, also „kann das nicht". Ein Profil voller
  Nullen wäre eine erfundene Aussage. Engine und Oberfläche sehen solche
  Einträge deshalb nicht; Import und Aggregation zählen sie.
- **Modi und Maps** entstehen beim Import aus `event.modeId` und `event.id` —
  schon bei der ersten Sichtung. Das ist kein Übereifer, sondern
  Deduplizierung: Der Fingerabdruck einer Partie hängt daran, ob der Katalog
  die Map kennt. Käme sie erst nach mehreren Sichtungen dazu, bekäme dieselbe
  Partie aus einem später abgerufenen Battlelog einen anderen Fingerabdruck und
  würde doppelt gezählt. Jede weitere Sichtung wird stattdessen gegen den
  Katalog geprüft; Widersprüche (bekannte ID, anderer Name) stehen im Bericht.

### Trophäen und Ranked bleiben getrennt

`battle.type` wird roh gespeichert. In Draft-Statistiken geht nur ein, was in
`config.DRAFT_STATISTIK_BATTLE_TYPEN` steht — derzeit `soloRanked`. Die
Aggregation filtert doppelt: über `is_ranked` **und** über den Partietyp. Eine
Trophäen-Partie würde also auch dann nicht gezählt, wenn `is_ranked` falsch
gesetzt wäre. Entdeckt werden Mitspieler ebenfalls nur aus `soloRanked`.

### Gemessene Statistiken werden nicht automatisch produktiv

`config.GEMESSENE_STATS_FREIGEGEBEN` (aus
`settings.DRAFTER_GEMESSENE_STATS_FREIGEGEBEN`, Standard **False**) entscheidet,
ob `auto` gemessene Werte überhaupt in Betracht zieht. Solange der Schalter aus
ist, bleibt die Seite bei den Demo-Daten, auch wenn längst aggregiert wurde.

Der Weg zur Freigabe:

```bash
python manage.py collect_brawl_matches --max-spieler 25
python manage.py aggregate_brawl_stats --quelle api
python manage.py vergleiche_brawl_stats --quelle api      # Bericht, ändert nichts
```

Der Vergleichsbericht stellt Messwerte und Demo-Werte nebeneinander: Stichprobe,
Pick- und Winrate, Confidence, Counter, Synergien — und für jede Map die Top 5
der Engine einmal mit Demo- und einmal mit gemessenen Daten. Erst wenn die
Stichproben tragen, lohnt die Freigabe.

## 18b. Paarwerte über Ebenen: global ist die Basis

Counter und Synergien werden auf zwei Ebenen aggregiert, **global** und
**Modus** — eine Map-Ebene gibt es für Paare nicht (`AGGREGATIONS_EBENEN`).
Bis zum 2026-09-20 schrumpfte jede Ebene für sich gegen die nackte
log5-Erwartung, und die Engine nahm anschließend über `_spezifitaet()`
**immer** die spezifischste Zeile. Der Stichprobenterm dieser Regel ist
`min(0.1, games/1_000_000)` und kann den Modus-Bonus von 2.0 nie
aufwiegen: sechs Knockout-Partien verdrängten dreiundzwanzig globale
vollständig. Im Praxisfall #7 kippte damit ein Vorzeichen — EDGAR+GRAY
stand global bei +0.003 und im Modus bei −0.031.

### Die Kette

Dieselbe Grundidee wie bei `BrawlerStat` (Map schrumpft zum Modus, Modus
zum globalen Wert), aber ohne deren Doppelzählung:

```
global:  Prior = log5-Erwartung aus den Einzelstärken
         Posterior = bayes(n_global, Siege, Prior, PAAR_PRIOR_STAERKE)

Modus:   Rest      = global MINUS Modus          (rechnung.rest_zaehler)
         Restrate  = bayes(n_rest, Siege_rest, log5_global, k)
         Prior     = log5_modus + (Restrate - log5_global)
         Posterior = bayes(n_modus, Siege_modus, Prior, k)
```

Das Gewicht der eigenen Beobachtung ist `n/(n + PAAR_PRIOR_STAERKE)`,
also `n/(n+60)` — stetig und ohne Schwelle: 6 Partien zählen 9 %, 60 die
Hälfte, 600 zu 91 %.

**Übertragen wird die Abweichung, nicht die Rate.** Beide Ebenen haben
eigene Erwartungen: global kann für ein Paar 51,2 % erwarten lassen, im
Knockout 49,9 %, weil dort andere Einzelstärken gelten. Wanderte die
Rate, hieße „außerhalb 51 %" im Modus fälschlich „überdurchschnittlich".
Wandert der Vorsprung, heißt „außerhalb 1,1 Punkte unter Erwartung" auch
im Modus „1,1 Punkte unter der dortigen Erwartung".

### Keine Partie zählt zweimal

Der Prior ist die **Differenzmenge**, nicht die Globalzeile. Die
Globalzeile enthält die Modus-Partien bereits; sie als Prior zu nehmen,
zöge dieselben Partien ein zweites Mal in die Schätzung — einmal als
Vorannahme, einmal als Beobachtung. Mit dem Rest gilt für jede einzelne
Schätzung:

* Partien **in** diesem Modus → gehen in die Likelihood ein, genau einmal.
* Partien **außerhalb** → gehen in den Prior ein, genau einmal.
* Summe: `rest.games + modus.games == global.games` (ein Test hält das fest).

Der Rest wird mit Stärke `k` gegen die log5-Erwartung geglättet und geht
als Punkt-Prior mit derselben Stärke `k` ein — nicht mit seiner eigenen
Stichprobe. Bewusst konservativ: auch 2000 Partien außerhalb eines Modus
können die dortige Messung nicht überstimmen, sie ersetzen nur die
Annahme „kein Vorteil".

Kam ein Paar ausschließlich in einem Modus vor, ist der Rest leer, der
Prior bleibt die reine Erwartung — genau das Verhalten von vorher.

> **Was NICHT geändert wurde:** die Auswahlregel der Engine
> (`_spezifitaet`) ist unangetastet. Sie darf weiter die Modus-Zeile
> nehmen, weil die globale Information jetzt darin steckt. Ebenso
> unverändert: Current Strength, Objective Fit, Map Fit, Flexibilität,
> Draft-Position, Personal und alle Gewichte.

### Wirkung auf den Bestand (2026-09-20, 10 190 Ranked-Partien)

| Modus-Stichprobe | Zeilen | näher an global | Vorzeichenwechsel | davon \|vorher\| > 0,05 |
|---|---|---|---|---|
| n < 10 | 45 741 | 87,0 % | 11 222 | 280 |
| n 10–49 | 9 850 | 78,8 % | 2 089 | 193 |
| n 50–199 | 1 414 | 72,3 % | 230 | 10 |
| n ≥ 200 | 15 | 60,0 % | 0 | 0 |

Median der Änderung 0,0216, p90 0,0669, Maximum 0,2146. Der mediane
Abstand einer Modus-Zeile zu ihrer Globalzeile fiel von 0,0227 auf
0,0027. Globale Zeilen änderten sich um höchstens 0,0067 (reine
Stichtagsdrift) — sie sind die Kontrollgruppe, ihr Rechenweg ist
unverändert.

---

## 18c. Sampling-Bias: gemessen, nicht korrigiert

Der Collector lädt Battlelogs hochrangiger Spieler. Der jeweils
**abgefragte** Spieler gewinnt 57,8 % seiner Partien — er wurde dafür
ausgesucht. Damit hängt jede gemessene Quote daran, auf welcher Seite er
stand. Über 100 Brawler mit mindestens 50 Partien:

* `sampled_side_winrate` gesamt: **0,578**
* Median |Spreizung| (Siegquote mit ihm minus gegen ihn): **0,134**
* `queried_side_balance`: median 0,514, min 0,304, max 0,649

EDGAR: 54,9 % mit ihm im Team (505 Partien), 44,4 % gegen ihn (610) —
10,5 Punkte, die nichts mit EDGAR zu tun haben.

Messbar ist das über `python manage.py brawl_sampling_bias`
(read-only, `--brawler`, `--paar`, `--top`). **Korrigiert wird nichts.**
Eine Korrekturformel ohne saubere Herleitung würde einen bekannten Bias
durch einen unbekannten ersetzen; die Optionen stehen in §21.

Warum als Kommando und nicht in der API: die Engine liest grundsätzlich
keine Rohmatches (§16). Wer die Zahlen im Draft sehen will, braucht sie
als Feld auf der Statistikzeile, geschrieben beim Aggregieren — das ist
erst sinnvoll, wenn entschieden ist, was damit geschehen soll.

---

## 19b. Einzelanalyse: jeden Kandidaten aufklappen

Die Vorschlagsliste zeigt acht Namen. Für die Fehlersuche und den
Praxistest ist aber oft der interessant, der **nicht** darin steht:
*Warum steht EDGAR hier auf Platz 34?*

Dafür gibt es die Einzelanalyse — in der Oberfläche über den Schalter
**Analyse** neben der Sortierung (ein Klick auf eine Kachel erklärt dann,
statt zu wählen), auf dem Terminal über:

```
python manage.py drafter_analyse --map belles-rock \
    --eigene gus,gray --gegner belle,sandy,mortis --brawler edgar
```

Beides liefert dieselbe Antwort wie `/draft/api/detail/`: Rang im ganzen
Feld, Score, alle Komponenten mit Wert, Gewicht, Beitrag und Quelle, die
fünf Größen der `erklaerung`, Datenabdeckung, Confidence — und die
Counter- und Synergiewerte **einzeln gegen jeden Gegner und jeden
Mitspieler**. Die Komponente mittelt diese Paare; ohne sie sieht man
„Counter −0,1" und weiß nicht, ob das drei laue Matchups sind oder zwei
gute und ein katastrophales.

**Es ist kein zweiter Rechenweg.** `DraftEngine.analyse()` ist derselbe
Lauf wie für die Vorschlagsliste, nur ohne Abschneiden nach den ersten
Plätzen — der Rang fällt als Listenindex ab. Die Paarwerte kommen aus
`counters.vorteil()` und `synergies.paar()`, also aus genau den
Funktionen, aus denen die Komponenten ihren Mittelwert bilden. Deshalb
*kann* die Analyse nicht von der Empfehlung abweichen; `services/analyse.py`
rechnet nichts Eigenes. `drafter/tests/test_analyse.py` hält beide Wege
Komponente für Komponente gegeneinander.

**Sie wirkt nicht zurück.** Kein Score, keine Reihenfolge, keine
Komponente ändert sich dadurch, dass jemand hinsieht.

Zwei Dinge, die dabei aufgefallen sind und mitrepariert wurden:

* Der Detail-Endpunkt verlangte `is_active=True`. Katalogeinträge ohne
  gepflegtes Profil sind aber `is_active=False`, stehen trotzdem im
  Gitter und werden seit den Datenstufen (§13) bewertet, sobald
  Messwerte vorliegen — ausgerechnet der Fall, für den die Analyse
  gemacht ist, ließ sich also nicht aufklappen. Die Suche ist jetzt
  dieselbe wie im Katalog-Endpunkt.
* In der Oberfläche steht **ein** Schalter statt eines Fragezeichens auf
  jeder der gut hundert Kacheln: das hätte die Tabreihenfolge verdoppelt
  und jede Kachel zugestellt. Der Modus wird bewusst nicht gespeichert —
  ein Analysemodus, der einen Tag später noch aktiv wäre, ließe den
  nächsten Pick ins Leere gehen.

---

## 20. Offene Datenfragen

Bewusst **nicht** beantwortet, weil sie nur echte Antworten beantworten können:

| Frage | Warum sie zählt | Wo es hängt |
|---|---|---|
| Bedeutet `brawler.trophies` bei `soloRanked` wirklich den Ranked-Rang? | belegt nur durch 4 Partien eines Spielers | `Match.battle_type`, `MatchPlayer.trophies` |
| Gibt es eine eindeutige Partie-ID? | **Nein** (beobachtet) — Rekonstruktion per Fingerabdruck | `fingerprint.py` |
| Wie genau stimmen Zeitstempel derselben Partie überein? | Toleranz `MATCH_ZEITTOLERANZ_SEKUNDEN` (60 s) ist geschätzt; messbar erst mit Battlelogs zweier Spieler derselben Partie | `config.py` |
| Ranked-**Bans**, **Pick-Reihenfolge**, First Pick? | **Nicht im Battlelog** (beobachtet) — keine Banrate, keine gelernten Draft-Positionen; Quelle offen | Aggregation zählt nur Vorhandenes |
| Wie erreicht man gezielt Ranked-Spieler? | Es gibt **keine Elo-Rangliste** (geprüft) — die Saat sind Trophäenspieler, Ranked-Spieler kommen erst über deren soloRanked-Mitspieler | `services/collector.py` |
| **Builds** historischer Partien? | **Nicht im Battlelog** (beobachtet); das Profil nennt nur Besessenes — `BuildStat` bleibt leer | Build-Empfehlung läuft weiter auf Regeln |
| Wie ist der **Rangbereich** einer Partie erkennbar? | kein Feld dafür; bei `soloRanked` evtl. über `brawler.trophies` (s. o.) | `Match.rank_pool` |
| Sind Brawler-ID, `event.id` und `modeId` über Zeit stabil? In einem Log 1:1 — über Wochen unbelegt | Zuordnung läuft bevorzugt über `external_id`; bis dahin über Namen, die sich in Schreibweise und Übersetzung ändern können | `external_id` im Katalog, `importer._brawler_fuer()` |
| Wie viele Partien sind realistisch? | Paarzeilen wachsen quadratisch mit Brawlern × Ebenen × Fenstern × Pools — bei ~90 Brawlern Hunderttausende Zeilen; ggf. Mindeststichprobe für Paare | `aggregator.py` |
| Gewichtete Kombination der Rang-Pools (`RANG_POOL_GEWICHT`)? | derzeit je Pool getrennt aggregiert, die Gewichte werden noch nicht benutzt | `config.py` |

---

## 21. Nächste Schritte

1. **Mehr Läufe des Collectors** (§19), bis die Stichproben je Map und Paar tragen — und um die offenen Fragen in §20 zu klären.
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
