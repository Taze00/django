# 🗺️ Projekt-Landkarte — alex-django

> **Zweck:** Dieses eine Django-Projekt (`meinprojekt`) bedient **vier unabhängige Webseiten**. Diese Datei sagt dir auf einen Blick, **welche Datei zu welcher Seite gehört**. Stand: August 2026.
>
> **Wichtigste Erkenntnis:** **CORVIS und die Portfolio-Welt berühren sich nirgends** — du kannst an einer Seite arbeiten, ohne die andere zu gefährden. Innerhalb der Portfolio-Welt ist es umgekehrt: dort teilen sich *alle* Seiten dieselbe `styles.css` und `main.js`.

---

## Die vier Seiten im Überblick

| Seite | URL | Template | Eigene Dateien (CSS/JS/Assets) | Status |
|-------|-----|----------|-------------------------------|--------|
| **Portfolio / Startseite** | `/` | `index.html` | `static/css/styles.css`, `static/js/main.js`, `static/css/images/` | 🟡 teilt CSS/JS (s.u.) |
| **Filme** | `/filme/` | `filme.html` | *keine eigenen* — nutzt `styles.css` + `main.js` | 🟡 teilt CSS/JS (s.u.) |
| **Impressum** | `/impressum/` | `impressum.html` | *keine eigenen* — nutzt `styles.css` + `main.js` | 🟡 teilt CSS/JS (s.u.) |
| **CORVIS** (Fitness-App) | `/corvis/` + `/corvis-app/` | `fitness-landing.html` + `fitness.html` | siehe `CLAUDE.md` | 🟢 komplett isoliert |

Dazu `404.html` als Catch-All für alles Übrige — ebenfalls in der Portfolio-Gestaltung, also auch an `styles.css`/`main.js` hängend.

Die Portfolio-Seiten setzen sich aus gemeinsamen Bausteinen in `templates/includes/` zusammen:
`seitenkopf.html`, `seitenfuss.html`, `sektion-meta.html`, `regal.html`, `wertungsverteilung.html`
sowie den Kacheln `kachel-chronik.html`, `kachel-foto.html`, `kachel-poster.html`, `kachel-projekt.html`.

> Im Backend ist jede dieser Seiten fast nur **ein Einzeiler** (`render(request, 'xy.html')`) in `meinprojekt/views.py`. Ausnahme ist `/filme/`, das die `films`-App mit eigenen Views, Models und Migrations hat.

---

## ⚠️ Was man wissen muss

### 1. Alle Portfolio-Seiten teilen sich CSS + JS
`static/css/styles.css` und `static/js/main.js` werden von **Startseite, Filme, Impressum und 404** benutzt.
→ **Eine Änderung daran trifft alle vier gleichzeitig.**
Das ist gewollt — es ist eine Seitenfamilie mit gemeinsamer Gestaltung —, aber gut zu wissen, bevor man dort etwas ändert. Die Fallen beim Arbeiten in `styles.css` (Reihenfolge von Modifikator-Regeln, doppelte Blöcke) stehen in `CLAUDE.md` unter „Werkzeuge und Fallen".

### 2. Screenshots vor „fertig"
`tools/shots.py` nimmt Hero, Full-Page und Einzelsektionen in 1440px und 390px auf. Details und die bekannten Aufnahme-Fallen (Intro-Vorhang, leere Kacheln, Hero nur auf `*-hero.png` beurteilen) stehen in `CLAUDE.md`.

---

## 🗑 Toter Ballast (kann weg, wenn du mal aufräumst)

| Was | Wo | Hinweis |
|-----|-----|---------|
| Veraltete Dokus | `FITNESS_APP_COMPLETE_SPEC.md` (April), `BUILD_WORKFLOW.md` (März) | Beide überholt/widersprüchlich. Gültig sind nur `CLAUDE.md` und `CORVIS_DOCUMENTATION.md` |
| `staticfiles/`-Altlasten in der Git-Historie | — | 226 Blobs, ~57 MB. Nur per History-Rewrite zu entfernen — **bewusst nicht gemacht**, das Risiko lohnt den Gewinn nicht |

---

## 🧹 Im August 2026 entfernt

Diese Seiten und Dateien gibt es **nicht mehr** — falls dir irgendwo noch ein Verweis begegnet, ist der Verweis der Fehler, nicht die fehlende Datei:

- **Schubi** (`/schubi/`): `schubi.html`, `static/css/schubi.css`, `static/js/schubi.js`, `static/css/images/schubi/` inkl. des 299-MB-Videos
- **Skills** (`/skills/`) und **Festival** (`/festival/`): Inhalte sind in die Startseite gewandert
- **Aurelia** (`/aurelia/`): `aurelia-demo.html` — zwei ihrer Techniken leben in der CORVIS-Landing-Page weiter (`CORVIS_DOCUMENTATION.md` §10)
- **Club-Ranking** in der Berlin-Sektion samt `static/css/images/clubs/` (sechs Fotos)
- **geo-App**: `static/geo/`, `staticfiles/geo/`, `media/geo/`, `build-geo.sh` — inkl. der Favicon-Abhängigkeit in `urls.py`
- `create_test_user.py`, `staticfiles/workout/`, `tools/silhouetten.py`, `films/templatetags/film_text.py`, `static/css/images/header/berlin-crop.jpg`

---

## Ordnerstruktur (oberste Ebene)

```
alex-django/
├── data/              → Postgres-Datenbank — NICHT anfassen
├── docker/            → Dockerfile + requirements.txt
├── films/             → FILME-App (Models, Views, Daten für /filme/)
├── fitness/           → CORVIS BACKEND (Django-App)
├── fitness-frontend/  → CORVIS FRONTEND (React-Quelle)
├── media/             → Hochgeladene Dateien (Profilbilder)
├── meinprojekt/       → Django-KERN (settings, urls, wsgi) — bedient ALLE Seiten
├── static/            → Quell-Static aller Seiten (siehe Tabelle oben)
├── staticfiles/       → GENERIERT von collectstatic (WhiteNoise liefert von hier)
├── templates/         → ALLE HTML-Seiten + includes/ (siehe Tabelle oben)
└── tools/             → Hilfsskripte (shots.py u.a.), nicht Teil der Seite
```
