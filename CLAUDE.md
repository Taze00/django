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

- **Screenshots: `tools/shots.py`** — Playwright für Python, kein Node auf dieser Maschine. Macht Full-Page und Einzelsektionen in 1440px und 390px nach `screenshots/` (gitignored).
  ```
  python3 tools/shots.py                                   # Startseite, beide Breiten
  python3 tools/shots.py --url http://localhost:8000/filme/ --out screenshots/filme
  ```
  **Immer laufen lassen und die Bilder tatsächlich ansehen, bevor etwas als fertig gemeldet wird.**

- **Leere Kacheln im Screenshot sind meist ein Aufnahmefehler, kein Seitenfehler.** Chromium rasterisiert bei langen Seiten die *erste* Full-Page-Aufnahme unvollständig — Bilder weit unterhalb des Viewports fehlen, obwohl sie geladen und sichtbar sind, und welche fehlen wechselt von Lauf zu Lauf. `shots.py` nimmt deshalb zweimal auf und behält die zweite. Vor der Fehlersuche an der Seite: mit einem **Viewport**-Screenshot gegenprüfen.

- **Textersetzungen mit `index()`: erst prüfen, dass das Ende hinter dem Anfang liegt.**
  ```python
  start = s.index(ANFANGSMARKE)
  ende  = s.index(ENDMARKE)
  assert start < ende, "Endmarke liegt vor der Anfangsmarke - Abbruch"
  s = s[:start] + neu + s[ende:]
  ```
  `index()` liefert immer das *erste* Vorkommen. Liegt die Endmarke davor, wird der Bereich **dupliziert statt entfernt** — die Datei bleibt syntaktisch gültig, und in CSS/JS gewinnt die spätere Kopie, die Änderung wirkt also folgenlos. Ist zweimal passiert (`.verteilung`/`.filmsuche` in `styles.css`, `initReveals` in `main.js`).

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
