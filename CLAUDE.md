# CLAUDE.md — CORVIS

> Diese Datei wird von Claude Code automatisch gelesen. Sie ist die **kompakte Arbeits-Referenz** für CORVIS. Die vollständige Erklärung steht in `CORVIS_DOCUMENTATION.md` (nur bei Bedarf lesen — diese Datei hier reicht für die meiste Arbeit).

## Was ist CORVIS?
Minimalistische Calisthenics-App: 3 Übungen (Push-ups, Pull-ups, Planks), adaptives 7-Stufen-Progressionssystem. Domain: `alex.volkmann.com`.

## ⚠️ WICHTIG: Was zu CORVIS gehört — und was NICHT
Dieses Django-Projekt bedient **7 unabhängige Seiten**. **Nur diese Pfade gehören zu CORVIS:**
- `fitness/` — Backend (Django-App: models, views, calibration, streak, serializers, urls)
- `fitness-frontend/` — Frontend (React-Quelle; der eigentliche Code in `fitness-frontend/src/`)
- `static/fitness/` — gebautes Frontend (generiert, gitignored)
- `templates/fitness.html` — Wrapper der React-App (`/corvis-app/`)
- `templates/fitness-landing.html` — Landing Page (`/corvis/`)
- API-Routen: `/api/fitness/`, `/api/token/`, `/api/register/`

**NICHT zu CORVIS gehört** (nicht lesen/ändern bei CORVIS-Arbeit): `static/css/styles.css`, `static/js/main.js`, `static/css/schubi.*`, `templates/index.html`, `schubi.html`, `impressum.html`, `skills.html`, `festival.html`, `aurelia-demo.html`, alles unter `static/geo/`. Siehe `PROJEKT_LANDKARTE.md` für die volle Übersicht.

CORVIS ist sauber isoliert — eine CORVIS-Änderung kann keine andere Seite brechen.

## 🔴 Build- & Deploy-Workflow (KRITISCH — seit WhiteNoise + gunicorn)
**Nach Frontend-Änderungen (React):**
```
./build-fitness.sh          # baut React → static/fitness/, aktualisiert fitness.html
# danach IMMER:
docker compose exec django-dev python manage.py collectstatic --noinput
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
  `docker compose exec django-dev bash -c "chmod 666 /code/PFAD"`
- **Git-Objects:** vor `git add` ggf. `docker compose exec django-dev bash -c "chmod -R 777 /code/.git/objects"`
- **Dateien NICHT vom Host löschen** (Permission denied) — im Container: `docker compose exec django-dev bash -c "rm ..."`
- **`Workout.date` ist `auto_now_add=True`** — Workouts mit vergangenem Datum brauchen rohes SQL.
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
1. **Registration-Key in die `.env` ziehen** — letzte Stelle mit echtem Wert im Code. Greift noch wegen Variablennamen-Tippfehler in `.env` (`REGISTRATION_SECRET_KEY` statt `DJANGO_REGISTRATION_KEY`). ~5 Min.
2. **PWA + Push-Notifications** — installierbar machen, Trainings-Reminder.
3. Optional: geo-Reste + tote Dokus aufräumen (siehe `PROJEKT_LANDKARTE.md`).
