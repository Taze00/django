# 🗺️ Projekt-Landkarte — alex-django

> **Zweck:** Dieses eine Django-Projekt (`meinprojekt`) bedient **7 völlig unabhängige Webseiten**. Diese Datei sagt dir auf einen Blick, **welche Datei zu welcher Seite gehört**. Stand: Juni 2026.
>
> **Wichtigste Erkenntnis:** Die Seiten sind sauber voneinander getrennt. **CORVIS und die Portfolio-Welt berühren sich nirgends** — du kannst an einer Seite arbeiten, ohne die anderen zu gefährden. Es gibt keine gefährliche Verklebung zwischen verschiedenen Projekten.

---

## Die 7 Seiten im Überblick

| Seite | URL | Template | Eigene Dateien (CSS/JS/Assets) | Status |
|-------|-----|----------|-------------------------------|--------|
| **CORVIS** (Fitness-App) | `/corvis/` + `/corvis-app/` | `fitness-landing.html` + `fitness.html` | siehe eigene CLAUDE.md | 🟢 komplett isoliert |
| **Portfolio / Hauptseite** | `/` | `index.html` | `static/css/styles.css`, `static/js/main.js`, `static/css/images/about-me/` | 🟡 teilt CSS/JS mit Impressum |
| **Impressum** | `/impressum/` | `impressum.html` | *keine eigenen* — nutzt `styles.css` + `main.js` der Hauptseite | 🟡 hängt an Hauptseite |
| **Schubi** (Freundin-Seite) | `/schubi/` | `schubi.html` | `static/css/schubi.css`, `static/js/schubi.js`, `static/css/images/schubi/` (Bilder + Video) | 🟡 toter CSS-Verweis (s.u.) |
| **Skills** | `/skills/` | `skills.html` | *alles inline* (CSS+JS in der Datei, ~1434 Zeilen) | 🟢 eigenständig |
| **Festival** | `/festival/` | `festival.html` | *alles inline*, lädt keine lokale Datei | 🟢 eigenständig |
| **Aurelia** (Technik-Demo) | `/aurelia/` | `aurelia-demo.html` | *alles inline* (Three.js/GSAP nur von CDN) | 🟢 eigenständig |

> Im Backend ist jede dieser Seiten nur **ein Einzeiler** (`render(request, 'xy.html')`) in `meinprojekt/views.py`. Keine geteilte Logik, keine Datenbank. Die Trennung passiert rein über die HTML/CSS/JS-Dateien.

---

## ⚠️ Was man wissen muss (kein Notfall, nur Bewusstsein)

### 1. Hauptseite ↔ Impressum teilen sich CSS + JS
`static/css/styles.css` und `static/js/main.js` werden von **beiden** benutzt.
→ **Eine Änderung daran trifft Hauptseite UND Impressum gleichzeitig.**
Das ist gewollt/sinnvoll (das Impressum ist die Rechtsseite des Portfolios und soll gleich aussehen), aber gut zu wissen, bevor man dort etwas ändert.

### 2. Schubi lädt eine fehlende Datei
`schubi.html` verweist auf `static/css/general_settings.css` — **diese Datei existiert nicht** (404). Die Seite funktioniert trotzdem (Browser ignoriert die fehlende Datei), aber es ist ein verwaister Verweis.
→ **Optionaler Mini-Fix:** den `<link>`-Verweis auf `general_settings.css` aus `schubi.html` entfernen. Ein-Zeilen-Sache, wann immer Lust besteht.

### 3. Favicon kommt aus totem geo-Ordner
`meinprojekt/urls.py` zeigt für `apple-touch-icon.png` und `favicon.svg` noch auf `static/geo/` — Reste der gelöschten geo-App.
→ **Optionaler Aufräum-Schritt:** Favicon-Dateien an einen sinnvollen Ort verschieben und die Pfade in `urls.py` anpassen. Erst danach lassen sich die toten geo-Ordner (`static/geo/`, `staticfiles/geo/`, `media/geo/`, `build-geo.sh`) gefahrlos entfernen.

---

## 🗑 Toter Ballast (kann weg, wenn du mal aufräumst)

| Was | Wo | Hinweis |
|-----|-----|---------|
| geo-Reste | `static/geo/`, `staticfiles/geo/`, `media/geo/`, `build-geo.sh` | Erst Favicon-Abhängigkeit lösen (s.o.), dann löschen |
| `staticfiles/workout/` | Static-Output | Rest einer noch älteren App |
| `create_test_user.py` | Projekt-Root | loses Einzel-Skript |
| Veraltete Dokus | `FITNESS_APP_COMPLETE_SPEC.md` (April), `BUILD_WORKFLOW.md` (März) | Beide überholt/widersprüchlich. Einzige gültige Doku: `CORVIS_DOCUMENTATION.md` |

---

## Ordnerstruktur (oberste Ebene)

```
alex-django/
├── data/              → Postgres-Datenbank — NICHT anfassen
├── docker/            → Dockerfile + requirements.txt
├── fitness/           → CORVIS BACKEND (Django-App)
├── fitness-frontend/  → CORVIS FRONTEND (React-Quelle)
├── media/             → Hochgeladene Dateien (Profilbilder) + toter geo-Rest
├── meinprojekt/       → Django-KERN (settings, urls, wsgi) — bedient ALLE Seiten
├── static/            → Quell-Static aller Seiten (siehe Tabelle oben)
├── staticfiles/       → GENERIERT von collectstatic (WhiteNoise liefert von hier)
└── templates/         → ALLE HTML-Seiten (gemischt — siehe Tabelle oben)
```
