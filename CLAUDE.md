# CLAUDE.md — CORVIS

> Diese Datei wird von Claude Code automatisch gelesen. Sie ist die **kompakte Arbeits-Referenz** für CORVIS. Die vollständige Erklärung steht in `CORVIS_DOCUMENTATION.md` (nur bei Bedarf lesen — diese Datei hier reicht für die meiste Arbeit).

## Was ist CORVIS?
Minimalistische Calisthenics-App: 3 Übungen (Push-ups, Pull-ups, Planks), adaptives 7-Stufen-Progressionssystem. Domain: `alex.volkmann.com`.

## ⚠️ WICHTIG: Was zu CORVIS gehört — und was NICHT
Dieses Django-Projekt bedient **fünf unabhängige Seiten** (Portfolio `/`, Filme `/filme/`, Impressum `/impressum/`, CORVIS, Draft Coach `/draft/`). **Nur diese Pfade gehören zu CORVIS:**
- `fitness/` — Backend (Django-App: models, views, calibration, streak, serializers, urls)
- `fitness-frontend/` — Frontend (React-Quelle; der eigentliche Code in `fitness-frontend/src/`)
- `static/fitness/` — gebautes Frontend (generiert, gitignored)
- `templates/fitness.html` — Wrapper der React-App (`/corvis-app/`)
- `templates/fitness-landing.html` — Landing Page (`/corvis/`)
- API-Routen: `/api/fitness/`, `/api/token/`, `/api/register/`

**NICHT zu CORVIS gehört** (nicht lesen/ändern bei CORVIS-Arbeit): die Portfolio-Welt — `static/css/styles.css`, `static/js/main.js`, `templates/index.html`, `filme.html`, `impressum.html`, `404.html`, alles unter `templates/includes/`, sowie die `films/`-App und die `drafter/`-App. Siehe `PROJEKT_LANDKARTE.md` für die volle Übersicht.

> Die Seiten `/schubi/`, `/skills/`, `/festival/`, `/aurelia/` und die geo-App **gibt es nicht mehr** (August 2026). Wenn dir noch ein Verweis darauf begegnet, ist der Verweis der Fehler — nicht die fehlende Datei.

CORVIS ist sauber isoliert — eine CORVIS-Änderung kann keine andere Seite brechen.

## 🔴 Build- & Deploy-Workflow (KRITISCH — seit WhiteNoise + gunicorn)
> ⚠️ **Befehle im Container immer mit `docker compose run --rm --no-deps -T django-dev …`, nicht mit `exec`.**
> Seit dem Host-Neustart am 2026-09-15 scheitert `docker compose exec` mit
> `chdir to cwd ("/code") … no such file or directory` — **die Seite läuft dabei normal**: gunicorn sieht `/code`,
> nur nachträglich per `exec` gestartete Prozesse nicht. `restart` und `up -d --force-recreate` beheben das nicht.
> `run` legt einen frischen Wegwerf-Container mit funktionierendem Mount an und geht auch dann, wenn `exec` wieder
> funktioniert — deshalb ist es hier durchgehend die Standardform.
> Zwei Folgen: Dateien, die im `run`-Container entstehen (Migrationen), gehören **root** → danach
> `chown -R 1002:1002` im selben Aufruf. Und nie zwei Testläufe gleichzeitig — beide legen `test_postgres` an.

**Nach Frontend-Änderungen (React):**
```
./build-fitness.sh          # baut React → static/fitness/, aktualisiert fitness.html
# danach IMMER:
docker compose run --rm --no-deps -T django-dev python manage.py collectstatic --noinput
docker compose restart django-dev
```
**Nach Backend-/Template-Änderungen (Python/HTML):**
```
docker compose restart django-dev
```
> ⚠️ Das frühere `touch wsgi.py` reicht NICHT mehr — gunicorn hat kein Auto-Reload. Immer `restart`.
> ⚠️ `build-fitness.sh` muss vom **Host** laufen, nicht im Container (sonst `docker: command not found`).

## Stolperfallen (aus Erfahrung)
- **Dateiberechtigungen:** Viele Frontend-Dateien gehören `root`. Vor dem Schreiben vom Host:
  `docker compose run --rm --no-deps -T django-dev sh -c "chmod 666 /code/PFAD"`
- **Git-Objects:** vor `git add` ggf. `docker compose run --rm --no-deps -T django-dev sh -c "chmod -R 777 /code/.git/objects"`
- **Dateien NICHT vom Host löschen** (Permission denied) — im Container: `docker compose run --rm --no-deps -T django-dev sh -c "rm ..."`
- **`Workout.date` ist `default=heute`** (seit Migration 0010, vorher `auto_now_add`). Das Datum lässt sich beim Anlegen setzen — `Workout.objects.create(user=u, date=...)` genügt, rohes SQL braucht es dafür nicht mehr. `heute()` kommt aus `fitness/zeit.py` und liefert den Kalendertag in **deutscher** Zeit (`CORVIS_TIME_ZONE`), nicht in UTC: `TIME_ZONE` ist projektweit weiter `UTC`, weil das globale Umstellen auch Admin, Templates und die `films`-App treffen würde. Wer in `fitness/` nach „heute" fragt, nimmt `heute()` — nicht `timezone.now().date()` und nicht `datetime.date.today()`.
- **`static/fitness/` ist gitignored** — nicht committen.
- **Secrets** stehen in der gitignorten `.env` (nicht im Code). `SECRET_KEY` ist rotiert.
- **Logs ansehen:** `docker compose logs django-dev`

## Werkzeuge und Fallen
> Dieser Abschnitt gilt **repo-weit**, nicht nur für CORVIS — er betrifft vor allem die Portfolio-Seiten (`templates/index.html`, `static/css/styles.css`, `static/js/main.js`).

- **Screenshots: `tools/shots.py`** — Playwright für Python, kein Node auf dieser Maschine. Macht einen Hero-Viewport-Shot, Full-Page und Einzelsektionen in 1440px und 390px nach `screenshots/` (gitignored).
  ```
  python3 tools/shots.py                                   # Startseite, beide Breiten
  python3 tools/shots.py --url http://localhost:8000/filme/ --out screenshots/filme
  ```
  **Immer laufen lassen und die Bilder tatsächlich ansehen, bevor etwas als fertig gemeldet wird.**

- **Den Hero immer auf `<breite>-hero.png` beurteilen, nie auf dem Full-Page-Bild.** Er ist die einzige Sektion, deren Höhe aus dem Fenster kommt (`height: 100vh`), und die einzige mit Parallaxe — er hängt damit am Aufnahmezustand, nicht nur am Layout. Im Full-Page-Bild steht er außerdem zwischen 9000px Seite und ist dort nie so zu sehen, wie ein Besucher ihn sieht. `shots.py` nimmt ihn deshalb seit August 2026 zuerst als reine Viewport-Aufnahme auf.

  Nachgemessen mit der Playwright-Version von August 2026 sind die beiden Aufnahmen **identisch**: Abweichung 0.00, Namenszug in beiden auf derselben Zeile, `offsetHeight` bleibt 900. Chromium nimmt Full-Page über `captureBeyondViewport` auf und fasst den Layout-Viewport dabei nicht an, `100vh` bleibt also die Fensterhöhe — eine Stauchung des Hero war *nicht* reproduzierbar. Die alte Umschalt-Strategie, die den Viewport wirklich vergrößert und `100vh` damit auf Seitenhöhe aufbläht, greift erst ab etwa 16384px; die Startseite liegt bei 8958px (1440) und 9837px (390). Wächst sie darüber, ist der Hero-Shot die Aufnahme, die weiterhin stimmt.

- **Fehlt der Namenszug im Hero-Screenshot, war es der Intro-Vorhang, nicht die Seite.** `html.intro-laeuft .hero-buchstabe` hält die Buchstaben verborgen, bis das Intro sie einfahren lässt; das Sicherheitsnetz im `<head>` räumt erst nach 3,5s auf. Eine Aufnahme bei ~3,5s erwischt genau die Kante und zeigt Hero samt Foto, Nav und Metazeile — nur ohne Namen. `shots.py` umgeht das, indem es `sessionStorage['intro-gesehen']` setzt. **Wer eigene Playwright-Skripte schreibt, muss das mitsetzen**, sonst sucht man den Fehler im CSS:
  ```python
  kontext.add_init_script(
      "try { sessionStorage.setItem('intro-gesehen', '1'); } catch (e) {}")
  ```
  Genau daran bin ich beim Hero-Umbau hängengeblieben.

- **Leere Kacheln im Screenshot sind meist ein Aufnahmefehler, kein Seitenfehler.** Chromium rasterisiert bei langen Seiten die *erste* Full-Page-Aufnahme unvollständig — Bilder weit unterhalb des Viewports fehlen, obwohl sie geladen und sichtbar sind, und welche fehlen wechselt von Lauf zu Lauf. `shots.py` nimmt deshalb zweimal auf und behält die zweite. Vor der Fehlersuche an der Seite: mit einem **Viewport**-Screenshot gegenprüfen.

- **Textersetzungen mit `index()`: erst prüfen, dass das Ende hinter dem Anfang liegt.**
  ```python
  start = s.index(ANFANGSMARKE)
  ende  = s.index(ENDMARKE)
  assert start < ende, "Endmarke liegt vor der Anfangsmarke - Abbruch"
  s = s[:start] + neu + s[ende:]
  ```
  `index()` liefert immer das *erste* Vorkommen. Liegt die Endmarke davor, wird der Bereich **dupliziert statt entfernt** — die Datei bleibt syntaktisch gültig, und in CSS/JS gewinnt die spätere Kopie, die Änderung wirkt also folgenlos. Ist zweimal passiert (`.verteilung`/`.filmsuche` in `styles.css`, `initReveals` in `main.js`).

- **Modifikator-Regeln (`--klein`, `--neon`, `--kern`, `--empfehlungen`) müssen IMMER hinter ihrer Basisregel stehen.** `.regal--kern` und `.regal` sind gleich spezifisch — beides eine Klasse. Bei Gleichstand gewinnt die **spätere** Regel. Steht der Modifikator weiter oben in der Datei, weil er inhaltlich zu seiner Sektion gehört, überschreibt die Basis ihn stillschweigend wieder.

  Vier Mal passiert, immer unbemerkt: `.regal--kern`, `.regal--neon` und `.regal--empfehlungen` standen im Block FILMSEKTION oberhalb von `.regal` — die Staffelung 240–165–130 lief nie, alle drei Regale hatten 225px, und dem Leuchtschein der fünf fehlte die Luft, für die der Zuschlag gedacht war. `.verteilung--klein` stand vor `.verteilung`, sein `margin: 0` griff nicht, unter den kleinen Balken standen 64px unsichtbarer Abstand.

  **Es fällt nicht auf, weil nichts kaputtgeht** — die Seite sieht nur anders aus, als der Code behauptet, und der Kommentar daneben beschreibt einen Zustand, den es nie gab.

  Nach jedem neuen Modifikator prüfen, ob er wirklich **greift**, nicht nur ob er im CSS steht:
  ```
  # Zeilennummern vergleichen - Modifikator muss die groessere haben
  grep -n "^\.regal {\|^\.regal--" static/css/styles.css
  ```
  Im Zweifel im Browser messen, nicht in der Datei nachlesen:
  ```python
  getComputedStyle(document.querySelector('.regal--kern'))
      .getPropertyValue('--regal-kachel-breite')   # muss 225px sein, nicht 225px der Basis
  ```
  Die Maße aller Regal-Varianten stehen deshalb gesammelt direkt hinter `.regal` (Block „Regal-Varianten"), nicht bei den Kacheln, zu denen sie inhaltlich gehören. Neue Variante: dorthin, nicht woanders hin.

- **Nach jedem größeren CSS-/JS-Eingriff nachzählen**, ob Regeln oder Funktionen doppelt stehen:
  ```
  grep -c "^\.verteilung {" static/css/styles.css     # muss 1 sein
  grep -c "function initReveals" static/js/main.js    # muss 1 sein
  ```

- **Das Sicherheitsnetz des Ladebildschirms steht als Inline-Skript im `<head>` von `index.html`**, nicht in `main.js` — damit es auch greift, wenn `main.js` gar nicht lädt oder einen Syntaxfehler hat. Es räumt den Vorhang nach 3,5s notfalls selbst weg; die DOM-Schritte liegen außerhalb des `try`, damit ein Fehler in `introBeenden()` sie nicht verschluckt. **Nicht nach `main.js` verschieben** — der Vorhang sperrt das Scrollen, ein hängender Vorhang macht die Seite unerreichbar.

## 🎯 Draft Coach (`/draft/`) — die fünfte Seite

Brawl-Stars-Ranked-Draft-Assistent. **Genauso isoliert wie CORVIS** — eigene App, eigene Templates, eigenes CSS/JS, keine Berührung mit `styles.css` oder `main.js`.

Dazu gehören: `drafter/`, `templates/drafter/`, `static/drafter/`, die Route `path('draft/', include('drafter.urls'))` in `meinprojekt/urls.py`.

**Kein Build-Schritt.** Das Frontend sind ES-Module ohne Werkzeugkette:
```
docker compose run --rm --no-deps -T django-dev python manage.py collectstatic --noinput   # nur bei CSS/JS
docker compose restart django-dev
```

**Acht Dinge, die man wissen muss, bevor man dort etwas ändert:**

1. **`drafter/config.py` hält ALLE Zahlen.** Gewichte, Schwellen, Grenzen. Eine Zahl im Engine-Code ist unauffindbar — deshalb steht dort keine.
2. **Jede Score-Komponente liefert [-1, +1].** Roh-Winrates (0–1) und Attribute (0–100) werden nie direkt addiert. Die Umrechnung auf 0–100 passiert genau einmal, in `Empfehlung.anzeige_score`.
3. **Strafgewichte sind Beträge, nicht negative Zahlen.** Das Vorzeichen steckt im *Wert* der Komponente. Wären beide negativ, würde aus jeder Strafe ein Bonus — und das fällt beim Lesen nicht auf, weil die Zahlen einzeln richtig aussehen. Ein Test hält es fest.
4. **Verhaltenstests statt Platzierungstests.** `tests/test_modellverhalten.py` prüft Richtungen an den Score-Komponenten („gegen zwei Tanks muss der Anti-Tank-Beitrag *stärker* steigen als bei einem Kandidaten ohne Anti-Tank"), nie Ränge. Ein Platz hängt von allen Kandidaten ab — Tests darauf verleiten dazu, Gewichte zu drehen, bis ein Lieblingsbeispiel wieder oben steht.
5. **Die Engine liest nie Rohmatches.** Statistiken kommen ausschließlich über einen `StatProvider` (`services/providers/registry.py`, Standard `auto`: gemessen wenn vorhanden, sonst Demo, synthetisch nie). Eine neue Datenquelle ist ein neuer Provider bzw. Parser — keine Änderung an Engine, Coach oder Frontend. Rohdaten (`models/matches.py`) und Statistiken (`models/stats.py`) sind getrennte Tabellen; dazwischen liegt die Aggregation.
6. **Keine API-Felder erfinden.** Für die offizielle API ist bewusst kein Parser registriert. Erst echte Antworten mitschneiden (`OfficialBrawlAPIProvider.rohantwort_sichern`), ansehen, dann parsen — Weg und offene Fragen in `DRAFTER_DOKUMENTATION.md` §19–§20.
7. **Gemessene Counter zählen genau einmal.** Aus Partien berechnete Counter (`measured_counter_advantage`) sind die Abweichung von der log5-Erwartung, liegen je Paar nur in einer Richtung vor (kleinere Brawler-ID zuerst, per DB-Constraint erzwungen) und die Gegenrichtung ist ihr Negativ. Der 0,8-Abzug der Gegenrichtung gilt **nur** für gepflegte (`manual_counter_score`) und heuristische Counter — auf gemessene angewandt, zählte dasselbe Matchup 1,8-fach. Zuordnung beim Import: Katalog-`external_id` vor Namen, Partie-ID vor Zeittoleranz.
8. **`drafter/attributes.py` ist das einzige Vokabular.** Dieselben 32 Schlüssel beschreiben Brawler („was ich kann"), Maps („was hier zählt") und Teams („was uns fehlt"). Neue Eigenschaft nur dort eintragen — die Modelle validieren dagegen.

**Anzeigetexte mit echten Umlauten, Kommentare in ASCII-Umschrift.** Die Engine erzeugt ihre Sätze aus Attributen; sie landen unverändert auf der Seite. „Flaechenkontrolle zaehlt" sieht dort falsch aus.

**Demo-Daten:** Alles ist mit `source="demo"` gekennzeichnet, die Confidence dadurch auf 0,35 gedeckelt, und die Oberfläche weist oben darauf hin. `python manage.py seed_brawl_data [--reset]` legt sie an (idempotent; `--reset` löscht nur Demo-Zeilen, keine manuell gepflegten).

**Datenpipeline** (läuft komplett ohne API-Key):
```
python manage.py import_brawl_fixture PFAD            # Rohdaten: idempotent, dedupliziert
python manage.py aggregate_brawl_stats --quelle …     # Statistiken: gemessen | fixture | api | synthetisch
python manage.py rebuild_draft_stats --quelle …       # Patches neu zuordnen + alles neu aggregieren
```
Synthetische Testpartien (`drafter/testdaten/`) landen als `source="synthetic"` und werden nie mit echten gemischt. Mitgeschnittene API-Antworten gehören nach `data/brawl_api_raw/` (gitignored, enthalten Spieler-Tags). Test gegen die echte API: `python manage.py test_brawl_api --brawlers | --player "#TAG" | --analysiere DATEI` — ruft ab und speichert, importiert nichts. Der Key kommt nur aus `BRAWL_STARS_API_KEY` in der `.env`, nie als Argument.

Volle Erklärung: `DRAFTER_DOKUMENTATION.md`.

## Arbeits-Konventionen
- **Pro Feature ein Commit** (nicht in Batches), mit `Co-Authored-By`-Trailer.
- **Bei Bugs/Fehlern: erst Logs/Fehler holen, nie raten.**
- **Bei Unsicherheit oder riskanten Schritten: fragen statt blind durchlaufen.**
- Remote: `git push alex main` (SSH; `alex` und `origin` zeigen aufs selbe Repo `Taze00/django.git`).

## Test-Zugang
- `test` / `test1234` — Test-Account unter `/corvis-app/`
- `Alex` — Admin/Superuser

## Tech-Stack (kurz)
Backend: Django + DRF + PostgreSQL + JWT, in Docker (`django-dev`), gunicorn + WhiteNoise.
Frontend: React 19 + Vite, Zustand (`authStore`, `workoutStore`), React Router v7 (`basename="/corvis-app"`), Axios. Styling: handgeschriebene `fitness-frontend/src/index.css` (App) + inline in `fitness-landing.html` (Landing).

## Offene nächste Schritte
1. **Feature 4 (Wochen-Rückblick) fertigbauen** — der Endpoint `/weekly-review/` läuft, `workoutStore` lädt ihn bei jedem Start, die CSS-Klassen `.week-review*` stehen fertig in `index.css` — aber **keine `.jsx` rendert ihn**. Es fehlt nur das Bauteil in `HomeView.jsx`.
2. **Echtes Server-Push (Web-Push + VAPID)** — die PWA ist installierbar und zeigt *lokale* Benachrichtigungen (Pausenende). Eine Erinnerung, die ankommt **ohne** offene App, geht noch nicht: kein `push`-Handler im Service Worker, kein `PushManager.subscribe()`.
3. **`npm audit fix`** — 7 Findings (1 low, 6 high); 5 davon reines Build-Werkzeug, 2 (`react-router*`) landen im Bundle, betreffen aber nur den RSC-Modus, den CORVIS nicht nutzt.
4. **Offline-Modus** — `sw.js` hat bewusst *keinen* `fetch`-Handler.

*Erledigt:* Django 5.2.17 LTS + DRF 3.17.0 (Branch `django-upgrade`, in `main` gemerged). 134 Tests unter `fitness/tests/`. Migrationskette bis `0009` von null reproduzierbar. gunicorn statt `runserver`. `ALLOWED_HOSTS` ohne Wildcard. PWA installierbar. Registration-Key in der `.env`. geo-Reste entfernt.

## Tests
```
docker compose run --rm --no-deps -T django-dev python manage.py test fitness --settings=meinprojekt.settings_test
```
253 Tests, ~15 s. Für den Drafter:
```
docker compose run --rm --no-deps -T django-dev python manage.py test drafter --settings=meinprojekt.settings_test
```
256 Tests, ~2 min. **Vor jedem Dependency- oder Django-Upgrade beide laufen lassen** (zusammen 509). Nie zwei Testläufe gleichzeitig — beide legen `test_postgres` an.

> Frühere Fassungen dieser Datei nannten 134 Tests und „SQLite im Speicher". Beides stimmt nicht mehr bzw. stimmte nie: `settings_test` unterscheidet sich von `settings` **nur** im Passwort-Hasher, die Testdatenbank ist dieselbe Postgres-Instanz.

## Startlevel (häufiger Irrtum)
Neue Nutzer starten auf **Push-ups L4** (Standard Push-ups), **Pull-ups L1** (Dead Hang), **Planks L3** (Standard Plank) — gesetzt in `fitness/migrations/0009_*`, Konstante `STARTLEVEL`. Die gelöschte `FITNESS_APP_COMPLETE_SPEC.md` behauptete L3/L1; das war falsch. Die Trainings-**Ziele werden angezeigt** (`Ziel: 8 Wdh`), nicht versteckt.
