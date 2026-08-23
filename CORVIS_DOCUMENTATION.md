# CORVIS — Vollständige Projektdokumentation

> **Zweck dieses Dokuments:** Eine KI oder Entwickler*in mit **null Vorwissen** vollständig auf den aktuellen Stand des CORVIS-Projekts bringen — Konzept, Technik, Architektur, jedes Feature, Designentscheidungen, Workflow und offene Punkte. Stand: **August 2026**.

---

## 1. Was ist CORVIS?

**CORVIS** ist eine **minimalistische Calisthenics-Fitness-App** (Eigengewichtstraining ohne Geräte). Die Kernphilosophie: **maximaler Effekt mit minimaler Komplexität.**

- **Nur 3 Übungen:** Push-ups (Liegestütze), Pull-ups (Klimmzüge), Planks (Unterarmstütz).
- **3 Kategorien:** PUSH (Brust/Trizeps/Schultern), PULL (Rücken/Bizeps), CORE (Rumpf).
- **Trainingsrhythmus:** ~5× pro Woche, ca. 30 Minuten pro Einheit.
- **Komplett kostenlos**, kein Abo, kein Equipment, kein Gym.
- **Zielgruppe:** Menschen, die Gym-Mitgliedschaften zahlen ohne hinzugehen, die von zu vielen Trainingsoptionen überfordert sind, oder denen Zeit/Motivation fehlt.

**Das zentrale Alleinstellungsmerkmal (USP):** *"CORVIS denkt mit."* Andere Fitness-Apps sind passive Tracker — der Nutzer trägt Werte ein, die App speichert sie. CORVIS dagegen **reagiert** auf den Nutzer:
- Es **kalibriert** das Startlevel anhand eines echten Tests.
- Es **stuft automatisch hoch und runter** je nach Leistung.
- Es **schützt die Trainingsserie** bei bewussten Ruhetagen.
- Es **protokolliert die Reise** (Meilensteine, Level-Ups).
- Es **lernt aus dem Drop-Set**.

Dieses adaptive **Progressionssystem** (automatische Ein- und Abstufung in 7 Stufen pro Übung) ist der technische und konzeptionelle Kern und das, was CORVIS von Wettbewerbern unterscheidet.

---

## 2. Wo läuft das Projekt? (URLs)

Die Domain ist **alex.volkmann.com**. Relevante Routen:

| URL | Inhalt |
|-----|--------|
| `/corvis/` | **Landing Page** der Fitness-App (Marketing, Django-Template) |
| `/corvis-app/` | **Die React-App** selbst (Login, Training, Statistiken) |
| `/corvis-app/*` | Catch-All für React-Router (Sub-Routen wie `/corvis-app/workout`) |
| `/api/fitness/...` | Die REST-API der Fitness-App |
| `/api/token/`, `/api/token/refresh/`, `/api/register/` | Auth (JWT) |
| `/admin/` | Django-Admin |
| `/`, `/filme/`, `/impressum/` | Andere, projektfremde Seiten des Besitzers (Portfolio) |

**Wichtig:** Die URLs hießen früher `/fitness/` und `/fitness-landing/` und wurden zu `/corvis-app/` bzw. `/corvis/` umbenannt.

---

## 3. Tech-Stack

### Backend
- **Django 5.2.17** (LTS-Linie) + **Django REST Framework 3.17.0** für die API.
  Das Upgrade von 4.2 auf 5.2 lief im August 2026 (4.2 hatte am 7. April 2026 EOL erreicht).
  Abgesichert war es durch die 134 Tests aus §16 — sie liefen vor und nach dem Sprung grün.
- **PostgreSQL** als Datenbank.
- **JWT-Authentifizierung** via `rest_framework_simplejwt` (TokenObtainPair / TokenRefresh).
- **WhiteNoise** liefert die statischen Dateien aus (`STATIC_ROOT`/`staticfiles/`) — nötig, damit Static auch bei `DEBUG=False` funktioniert.
- Läuft in **Docker** (Container-Name: `django-dev`, Service via `docker compose`).

### Infrastruktur / Deployment
- **Reverse Proxy: Traefik** (NICHT nginx) — terminiert HTTPS (Let's Encrypt via certresolver), leitet alles auf den Django-Container Port 80. Traefik macht **kein** Static-Serving, reicht alles an Django durch. Konfiguriert über `labels:` in `docker-compose.yml` (Host-Regel `alex.volkmann.com`, HTTP→HTTPS-Redirect, Netzwerk `proxy` extern).
- **App-Server: gunicorn** (kein `runserver` mehr). Der Start steht in `docker-compose.yml`:
  `gunicorn meinprojekt.wsgi:application --bind 0.0.0.0:80 --workers 3 --timeout 60`.
  **Folge für den Alltag:** gunicorn hat **kein Auto-Reload**. Das früher übliche
  `touch wsgi.py` bewirkt nichts mehr — nach jeder Backend- oder Template-Änderung
  muss der Container neu gestartet werden (siehe §4).

### Frontend (die App unter `/corvis-app/`)
- **React 19** + **Vite** (Build-Tool).
- **Zustand** als State-Management (zwei Stores: `authStore`, `workoutStore`).
- **React Router DOM v7** (mit `basename="/corvis-app"`).
- **Axios** für API-Calls.
- TailwindCSS ist installiert, aber das tatsächliche Styling läuft fast komplett über **eine große handgeschriebene `index.css`** (CORVIS-Designsystem, siehe §8).

### Landing Page (`/corvis/`)
- **Reines Django-Template** (`templates/fitness-landing.html`) — ein einzelnes großes HTML-File mit Inline-CSS und Inline-JS.
- **Three.js** (WebGL-Shader für den Hero-Hintergrund mit Lichtstrahlen).
- **GSAP + ScrollTrigger** für Scroll-Animationen.

### Verzeichnisstruktur (Auszug)
```
/media/docker/alex-django/
├── fitness/                    # Django-App (Backend)
│   ├── models.py               # Datenmodelle
│   ├── views.py                # API-Views (ViewSets + Function-Views)
│   ├── urls.py                 # API-Routen
│   ├── serializers.py          # DRF-Serializer
│   ├── calibration.py          # Onboarding-Kalibrierungslogik (Feature 1)
│   ├── streak.py               # Streak-Berechnung (Feature 2)
│   ├── admin.py
│   ├── migrations/             # 0001 bis 0009
│   ├── tests/                  # 134 Tests (siehe §16)
│   └── management/commands/    # seed_exercises u.a.
├── fitness-frontend/           # React-App (Source)
│   ├── src/
│   │   ├── views/              # Seiten-Komponenten
│   │   ├── components/         # Wiederverwendbare Komponenten
│   │   ├── stores/             # authStore.js, workoutStore.js
│   │   ├── index.css           # Das CORVIS-Designsystem (groß!)
│   │   ├── App.jsx             # Router + Routen
│   │   ├── data/               # exerciseInfo.js (Form-Tipps)
│   │   ├── utils/notify.js     # Benachrichtigungen über den Service Worker
│   │   └── api.js              # Axios-Instanz
│   ├── public/                 # PWA: manifest.json, sw.js, Icons (siehe §17)
│   └── index.html              # Vite-Entry (Titel: CORVIS)
├── templates/
│   ├── fitness-landing.html    # Landing Page /corvis/
│   ├── fitness.html            # Wrapper der gebauten React-App /corvis-app/
│   └── 404.html                # Eigene 404-Seite (Portfolio-Gestaltung)
├── meinprojekt/                # Django-Projekt-Settings
│   ├── settings.py
│   ├── urls.py                 # Haupt-URL-Konfiguration
│   └── views.py                # Seiten-Views (Templates rendern)
├── meinprojekt/settings_test.py  # Settings nur für den Testlauf (SQLite)
├── tools/shots_corvis.py       # Screenshot-Werkzeug für CORVIS (Playwright)
├── static/fitness/             # Gebaute React-Assets (Build-Output, gitignored)
└── build-fitness.sh            # Build- und Deploy-Skript
```

---

## 4. Der Build- und Deploy-Workflow (KRITISCH)

Die React-App muss nach **jeder** Frontend-Änderung neu gebaut werden:

```bash
./build-fitness.sh
```

Dieses Skript:
1. Baut die React-App mit Vite (Output nach `static/fitness/`).
2. Aktualisiert `templates/fitness.html` mit den neuen Asset-Dateinamen (gehashte JS/CSS).
3. **Muss vom Host ausgeführt werden, NICHT im Container** (sonst `docker: command not found`).

> **⚠️ NEU seit WhiteNoise + DEBUG=False (Juni 2026):** WhiteNoise liefert Static aus `staticfiles/` aus und scannt dieses Verzeichnis **nur beim Container-Start**. Nach einem Frontend-Build reicht `build-fitness.sh` allein NICHT mehr — sonst gibt das neue (gehashte) Bundle einen 404. Der vollständige Frontend-Deploy ist jetzt:
> ```bash
> ./build-fitness.sh
> docker compose exec django-dev python manage.py collectstatic --noinput
> docker compose restart django-dev
> ```
> (`collectstatic` kopiert die neuen Assets nach `staticfiles/` + komprimiert sie; der Restart lässt WhiteNoise sie neu einlesen.)

Für **Backend- und Template-Änderungen** (Python, Landing Page, 404) reicht ein Neustart:
```bash
docker compose restart django-dev
```

> **⚠️ Seit dem Umstieg auf gunicorn (§3): `touch wsgi.py` reicht NICHT mehr.**
> Der frühere `runserver` hatte Auto-Reload und hat auf das Antippen der `wsgi.py`
> reagiert — gunicorn tut das nicht. Ein `touch` bleibt heute **wirkungslos**: die
> Seite antwortet weiter mit dem alten Code, ohne Fehlermeldung. Genau daran verliert
> man Zeit, weil nichts kaputtgeht — es ändert sich nur nichts. Immer `restart`.

Nach dem Neustart braucht der Server ein paar Sekunden (ggf. kurz HTTP 502, dann 200).

> **Image-Rebuild:** Wenn sich `docker/requirements.txt` ändert (neue Python-Pakete), muss das Image neu gebaut werden: `docker compose build django-dev`, danach `docker compose up -d django-dev`. Ein reiner Reload reicht dann nicht.

### Von Hand bauen (wenn `build-fitness.sh` streikt)

Das Skript nimmt einem nur die Handgriffe ab — hier sind sie einzeln:

```bash
# 1. React bauen (im Container, dort liegt node)
docker compose exec -T django-dev bash -c "cd /code/fitness-frontend && npm run build"

# 2. Build-Ergebnis nach static/ kopieren
docker compose exec -T django-dev bash -c "cp -r /code/fitness-frontend/dist/. /code/static/fitness/"

# 3. Die neuen Hashes in templates/fitness.html eintragen.
#    Die richtigen Namen stehen in fitness-frontend/dist/index.html:
grep -o 'index-[A-Za-z0-9_-]*\.\(js\|css\)' fitness-frontend/dist/index.html

# 4. Danach IMMER (siehe oben) - sonst 404 auf das neue Bundle:
docker compose exec django-dev python manage.py collectstatic --noinput
docker compose restart django-dev
```

**Zu committen ist nur `templates/fitness.html`** (mit den neuen Hashes).
`static/fitness/` ist gitignored und gehört **nicht** in den Commit — ein früheres
`BUILD_WORKFLOW.md` behauptete beides gleichzeitig und lag mit dem `git add
static/fitness/` falsch.

**Gegenprobe, dass Template und Build zusammenpassen:**
```bash
ls static/fitness/assets/
grep -o 'index-[A-Za-z0-9_-]*\.js' templates/fitness.html   # muss dieselbe Datei nennen
```

---

### Wichtige Workflow-Eigenheiten / Stolperfallen
- **Dateiberechtigungen:** Viele Frontend-Dateien gehören `root`. Vor dem Schreiben vom Host aus muss man sie im Container freigeben:
  `docker compose exec django-dev bash -c "chmod 666 /code/pfad/zur/datei"`
- **Git-Objects-Permissions:** Vor `git add` manchmal nötig:
  `docker compose exec django-dev bash -c "chmod -R 777 /code/.git/objects"`
- **Dateien NICHT vom Host löschen** (Permission denied) — stattdessen im Container: `docker compose exec django-dev bash -c "rm -rf /code/..."`.
- **`static/fitness/` ist gitignored** — nicht versuchen zu committen.
- **Workflow-Regel:** Nach jedem Feature committen (nicht in Batches). Bei Bugs immer erst die Logs/Fehler holen, nie raten.

---

## 5. Datenmodell (fitness/models.py)

### Exercise
Die 3 Übungen. Felder: `name`, `category` (PUSH/PULL/CORE), `order`.

### Progression
Eine Schwierigkeitsstufe einer Übung (7 pro Übung = 21 gesamt). Felder:
- `exercise` (FK), `level` (1–7), `name` (z.B. "Standard Push-ups").
- `target_type`: `"reps"` oder `"time"` (Sekunden).
- `target_value`: Zielwert (z.B. 8 Reps oder 60 Sekunden).
- `sets_required` (Standard 2), `sessions_required` (Standard 3).
- `user_starts_here`: markiert die Default-Startstufe.

### UserExerciseProgression
Der aktuelle Stand eines Nutzers für **eine** Übung. Felder:
- `user` (FK), `exercise` (FK), `current_progression` (FK).
- `sessions_at_target`: wie oft hintereinander das Ziel erreicht wurde (für Upgrade).
- `custom_target`: optionaler angepasster Zielwert (z.B. nach Downgrade).
- `is_first_session`: ob es die erste Einheit auf diesem Level ist.
- `effective_target` (Property): liefert `custom_target` falls gesetzt, sonst `current_progression.target_value`.

### Workout
Ein Trainingstag. Felder: `user`, `date` (**`auto_now_add=True`** — siehe Stolperfalle unten), `completed`, `completed_at`, `duration_seconds`. `unique_together = [user, date]`.

> **STOLPERFALLE:** `Workout.date` ist `auto_now_add=True`. Das bedeutet, beim Erstellen via ORM bekommt der Workout IMMER das heutige Datum, egal was man übergibt. Um Workouts mit vergangenem Datum anzulegen (z.B. für Tests/Demo), muss man **rohes SQL** verwenden (`INSERT INTO fitness_workout ...`).

### WorkoutSet
Ein einzelner Satz innerhalb eines Workouts. Felder: `workout`, `exercise`, `progression`, `set_number`, `reps`, `seconds`, `is_drop_set`, `drop_set_completed`, `rest_time_seconds`.

### WarmupChecklist
Aufwärm-Checkliste pro Workout (wrists, shoulders, elbows, back, legs).

### UserProfile
Profil mit `profile_picture`, `training_days` (JSON, z.B. `[1,2,4,5,6]` = Mo/Di/Do/Fr/Sa), `onboarding_completed`. Wochentage: 1=Montag … 7=Sonntag.

### RestDay (Feature 2)
Ein bewusster Ruhetag ("Heute pausieren"). Felder: `user`, `date`. `unique_together = [user, date]`. Wird genutzt, um die Streak bei entschuldigten Pausen NICHT abreißen zu lassen.

### LevelEvent (Feature 3)
Ein Meilenstein auf der Fortschritts-Timeline. Felder:
- `event_type`: `journey_start` | `level_up` | `streak_milestone` | `first_time`.
- `exercise` (FK, optional), `from_level`, `to_level`, `progression_name`.
- `streak_value` (für Streak-Meilensteine), `label` (Freitext), `created_at`.

---

## 6. Die Progressionslogik (DER KERN)

### Die 7 Stufen pro Übung (aktueller DB-Stand)

**Push-ups** (alle `reps`):
1. Wall Push-ups (Ziel 8) · 2. Incline Push-ups (8) · 3. Knee Push-ups (8) · 4. Standard Push-ups (8) · 5. Diamond Push-ups (6) · 6. Decline Push-ups (6) · 7. Pseudo Planche Push-ups (5)

**Pull-ups** (gemischt time/reps):
1. Dead Hang (time, 30s) · 2. Scapular Shrugs (reps, 10) · 3. Active Hang (time, 20s) · 4. Pull-up Negatives (reps, 5) · 5. Band-Assisted Pull-ups (reps, 8) · 6. Standard Pull-ups (reps, 5) · 7. Chest-to-Bar (reps, 5)

**Planks** (alle `time`/Sekunden):
1. Knee Plank (30s) · 2. Incline Plank (45s) · 3. Standard Plank (60s) · 4. Feet-Elevated Plank (60s) · 5. Extended Plank (45s) · 6. RKC Plank (30s) · 7. One-Arm Plank (20s)

### Wo ein neuer Nutzer startet (Startlevel)

Ohne Kalibrierung startet ein neuer Nutzer auf diesen Stufen — markiert über das
Feld `Progression.user_starts_here`, gesetzt in Migration `0009`:

| Übung | Startlevel | Variante | Ziel |
|-------|-----------|----------|------|
| Push-ups | **Level 4** | Standard Push-ups | 8 Wdh |
| Pull-ups | **Level 1** | Dead Hang | 30 s |
| Planks | **Level 3** | Standard Plank | 60 s |

> **⚠️ Achtung, hartnäckiger Irrtum:** Ältere Notizen (u.a. die inzwischen
> gelöschte `FITNESS_APP_COMPLETE_SPEC.md`) behaupteten **Push-ups Level 3**
> (Knee Push-ups) und **Planks Level 1** (Knee Plank). Das ist **falsch** und war
> der schädlichste Fehler in der alten Doku: Wer danach eine Migration oder einen
> Seed schreibt, setzt jeden neuen Nutzer zwei Stufen zu tief an. Maßgeblich ist
> die Tabelle oben — nachprüfbar in `fitness/migrations/0009_seed_exercises_and_progressions.py`
> (Konstante `STARTLEVEL`) und in der laufenden Datenbank:
> ```bash
> docker compose exec django-dev python manage.py shell -c \
>   "from fitness.models import Progression; print(list(Progression.objects.filter(user_starts_here=True).values_list('exercise__name','level')))"
> ```

Die meisten Nutzer sehen dieses Startlevel allerdings nie: Das Onboarding (Feature 1,
§7) kalibriert direkt beim ersten Start und überschreibt es. Der Wert greift als
Fallback, wenn eine Progression ohne Kalibrierung angelegt wird.

> **Wichtig:** Die Zielwerte sind **NICHT monoton steigend**. Höhere Level haben teils niedrigere Zahlen (z.B. Diamond Push-ups L5 = 6 Reps ist schwerer als Standard L4 = 8 Reps). Das ist Absicht — die Schwierigkeit steigt durch die Variante, nicht durch die Zahl. Diese Targets wurden gegen Calisthenics-Fachliteratur geprüft und als sinnvoll bestätigt.

### Trainings-Schwelle (Upgrade/Downgrade beim Workout)
Logik im `complete`-Endpoint (`WorkoutViewSet.complete`):
- Gewertet werden **Satz 1 und Satz 2** (das Drop-Set, Satz 3, zählt NICHT für die Progression).
- **Upgrade:** Wenn beide Sätze ≥ `effective_target`, wird `sessions_at_target` erhöht. Erreicht es `sessions_required` (Standard 3), steigt der Nutzer eine Stufe auf — sofern Level < 7. Bei Level 7 = Max-Level-Meldung.
- **Downgrade:** Nur in der ersten Einheit auf einem Level (`is_first_session`), und nur wenn Level > 1. Wenn die Leistung deutlich unter Ziel liegt (definierte Schwellen, z.B. `val1 < 3` bei Reps), steigt man eine Stufe ab und bekommt einen leicht angepassten `custom_target`.
- Diese Regel ("8 Reps × 2 Sätze, 3 Mal hintereinander → Aufstieg") stammt aus den Original-Trainingsvideos des Besitzers und ist **bewusst unangetastet** geblieben.

**Die Downgrade-Schwellen im Detail** (`WorkoutViewSet.complete`, Satz 1 = `val1`, Satz 2 = `val2`):
- Bei `reps`: `val1 < 3` **oder** `val1 + val2 < 5`.
- Bei `time`: `val1 < effective_target // 3` **oder** `val1 + val2 < effective_target // 2`.
- Nach dem Abstieg bekommt die niedrigere Stufe einen **Zuschlag** auf `custom_target`
  (Reps: +6/+4/+2 bei 0/1/2 geschafften Wiederholungen; Zeit: +15/+10/+5 s je nach Haltezeit).
  So ist die leichtere Stufe nicht sofort wieder trivial.
- `is_first_session` wird auf `False` gesetzt — das verhindert eine Abstiegs-Schleife.

### Der Trainingsablauf (9 Schritte)

Die Schritte werden **dynamisch** aus den Übungen gebaut (`buildWorkoutSteps` in
`WorkoutView.jsx`), nicht hart kodiert. Bei den drei Standard-Übungen ergibt das:

```
AUFWÄRMEN (Checkliste, 5 Punkte)

 1. Push-ups  Satz 1   → Pause 180 s
 2. Pull-ups  Satz 1   → Pause 180 s
 3. Push-ups  Satz 2   → Pause 180 s
 4. Pull-ups  Satz 2   → Pause 180 s
 5. Push-ups  Satz 3   DROP-SET → Pause 300 s
 6. Pull-ups  Satz 3   DROP-SET → Pause 300 s
 7. Planks    Satz 1   → Pause 180 s
 8. Planks    Satz 2   → Pause 180 s
 9. Planks    Satz 3   DROP-SET → fertig

ABWÄRMEN (Dehn-Checkliste, 5 Punkte)
```

Das Muster: die Hauptübungen (PUSH/PULL) werden über die Sätze **verschränkt**, die
CORE-Übung kommt geschlossen am Ende. Pausen: **180 s** nach den normalen Sätzen,
**300 s** nach einem Drop-Set (`REST_TIMES` in `WorkoutView.jsx`).

> **Die Ziele werden angezeigt.** Im Trainingsbildschirm steht über dem Eingabefeld
> `Ziel: 8 Wdh` bzw. `Ziel: 60 s` (CSS-Klasse `.wv-target`). Die alte SPEC forderte
> das Gegenteil ("TARGETS ARE HIDDEN — only 'Last time: X'"). Diese Regel wurde
> **verworfen**; wer sie wiederherstellt, baut ein Feature zurück, das bewusst so ist.

---

## 7. Die 5 Features (Roadmap — 4 davon sichtbar, siehe Feature 4)

Diese 5 Features wurden in dieser Reihenfolge (nach "Wow-Effekt") gebaut. Sie sind das, was CORVIS einzigartig macht. Roter Faden: **"CORVIS denkt mit."**

> **Stand August 2026:** Die Features 1, 2, 3 und 5 sind vollständig — Backend **und**
> sichtbare Oberfläche. **Feature 4 ist nur im Backend fertig** und wird nirgends
> angezeigt. Frühere Doku führte alle fünf als erledigt; das stimmt nicht.

### Feature 1 — 🎯 Onboarding-Test (Kalibrierung)
**Datei:** `fitness/calibration.py`, `OnboardingView.jsx`, Endpoint `POST /onboarding/calibrate/`.

**Das Problem:** Wo startet ein neuer Nutzer? Reine Selbsteinschätzung ist ungenau, reines Austesten ist umständlich (und scheitert am "0-Reps-Problem": Wenn die Standardübung 1 Klimmzug ist und man 0 schafft, ist der Test wertlos).

**Die Lösung (Hybrid):** Der Nutzer
1. wählt seine Trainingstage,
2. **schätzt sich pro Übung selbst ein** (wählt eine Variante),
3. macht **einen echten Test-Satz** dieser Variante (Reps-Counter oder Hold-Timer),
4. CORVIS **justiert automatisch** hoch oder runter.

**Die Justier-Logik** (`calibrate_level` in `calibration.py`): Sie vergleicht das Test-Ergebnis mit dem **app-eigenen Zielwert** der gewählten Stufe (kein fremder Maßstab!). `ratio = test_result / target_value`:
- `ratio < 0.5` → 2 Level runter
- `0.5 ≤ ratio < 0.85` → 1 Level runter
- `0.85 ≤ ratio < 2.0` → bleibt (15% Toleranzband, damit ein knappes Verfehlen nicht bestraft wird)
- `2.0 ≤ ratio < 3.0` → 1 Level hoch
- `ratio ≥ 3.0` → 2 Level hoch
- Ergebnis wird auf den gültigen Bereich (1–7) geclampt.

Beispiel: Nutzer sagt "Standard Push-ups" (L4, Ziel 8), schafft aber nur 2 → 2/8 = 0.25 → 2 Level runter → L2. Das löst auch das 0-Reps-Problem.

Die Logik wurde gegen mehrere Calisthenics-Quellen recherchiert (30s/60s-Hold-Schwellen, Cali Move, r/bodyweightfitness u.a.) — bewusst nicht auf einer einzigen Quelle aufgebaut.

### Feature 2 — 🔥 Streak + "Heute pausieren"
**Datei:** `fitness/streak.py`, Endpoints `GET /streak/`, `POST /rest-day/`, `DELETE /rest-day/remove/`. UI in `HomeView.jsx` (Flammen-Anzeige im Header + Button).

**Streak-Definition (trainingstage-basiert):** Die Serie zählt **aufeinanderfolgende geplante Trainingstage**, an denen trainiert wurde.
- Ein Nicht-Trainingstag (z.B. Mittwoch bei Mo/Di/Do/Fr/Sa) bricht die Serie **nie** — er wird übersprungen.
- Ein verpasster Trainingstag bricht die Serie — **außer** er ist als `RestDay` markiert ("Heute pausieren"), dann gilt er als entschuldigt und die Serie läuft weiter.
- Der heutige Tag bricht die Serie nie (der Tag ist noch nicht vorbei).

**"Heute pausieren":** Schützt die Serie komplett. Die App **bestraft** also bewusste Pausen (Krankheit, Stress) nicht — das löst das #1-Problem der Landing-Page-Argumentation ("man gibt auf").

Die alte, fehlerhafte Streak-Berechnung in `StatisticsView` (zählte nur Kalendertage) wurde durch die korrekte Backend-Streak ersetzt.

### Feature 3 — 📈 Fortschritt-Timeline
**Datei:** Modell `LevelEvent`, Endpoint `GET /timeline/`, UI in `StatisticsView.jsx` (Abschnitt "Deine Reise").

Eine vertikale Zeitleiste der Meilensteine, **ab jetzt vorwärts protokolliert** (nicht rückwirkend rekonstruiert):
- **journey_start** — beim Kalibrieren angelegt ("Deine Reise beginnt 🚀").
- **level_up** — jeder Aufstieg ("Push-ups L3 → L4").
- **streak_milestone** — bei 7/14/30/50/100/200/365 Tagen Serie.
- **first_time** — bei ikonischen Schwellen-Varianten ("Erster Standard Push-up", "Erster echter Pull-up", "Standard Plank gemeistert").

Die Events werden in der `complete`-Logik geloggt. Beim Onboarding-Reset werden Timeline + RestDays gelöscht (sauberer Neustart). **Bonus-Fix:** Bei dieser Gelegenheit wurde ein `from_level`-Off-by-One-Bug in der Upgrade-Logik behoben (Level wurde nach dem Überschreiben gelesen).

### Feature 4 — 📊 Wochen-Rückblick ⚠️ **nur Backend — wird nirgends angezeigt**
**Datei:** Endpoint `GET /weekly-review/` (`fitness/views.py:609`).

> **⚠️ Dieses Feature ist unfertig, auch wenn frühere Doku es als erledigt führte.**
> Es existiert **kein** Bauteil, das den Wochen-Rückblick rendert. Nachprüfbar:
> ```bash
> grep -rn "weeklyReview" fitness-frontend/src --include=*.jsx   # findet nichts
> ```

Was tatsächlich da ist:
- **Backend:** Der Endpoint `GET /weekly-review/` funktioniert und liefert die
  Wochenzahlen (Trainings absolviert vs. geplant, Level-Ups, Serie, Volumen aus
  Push-Reps/Pull-Reps/Plank-Minuten, dazu ein `is_weekend`-Flag).
- **Store:** `workoutStore.initialize()` ruft ihn bei **jedem** App-Start mit ab und
  legt das Ergebnis unter `weeklyReview` ab (`stores/workoutStore.js`).
- **CSS:** Die Klassen `.week-review*` stehen fertig in `index.css` (Zeile ~162).
- **Frontend:** **Nichts.** Keine `.jsx` liest `weeklyReview`, keine nutzt die
  CSS-Klassen. Der Wert wird geladen, gespeichert — und nie gelesen.

Der geplante Zustand war ein **Wochenend-Banner** auf der Startseite (nur Sa/So
sichtbar, per `localStorage` pro ISO-Woche wegtippbar). Zum Fertigbauen fehlt nur
das Bauteil in `HomeView.jsx` — Daten, Styling und Endpoint liegen bereit.

### Feature 5 — 💧 Drop-Set-Intelligenz
**Datei:** `DropSetInstructions.jsx`, `WorkoutView.jsx`, `last_performance`-Endpoint.

Das Drop-Set (3. Satz, bis zur Erschöpfung durch leichtere Varianten) war vorher binär ("✓ / übersprungen"). Jetzt **wählt der Nutzer, welche Variante er bis zur Erschöpfung erreicht hat**. Diese erreichte Stufe wird gespeichert (als `progression` des Drop-Set-Sets — kein neues DB-Feld nötig) und angezeigt:
- in der Trainings-History ("Drop → Incline Push-ups"),
- als "Letztes Mal"-Vergleich beim nächsten Drop-Set.

Je weniger tief man fallen muss, desto stärker ist man geworden — ein **sichtbares Fortschritts-Signal**.

> **Wichtige, forschungsbasierte Designentscheidung:** Das Drop-Set-Ergebnis fließt **NICHT** in die Level-Logik ein. Recherche ergab: Drop-Sets messen Erschöpfung, nicht saubere Kraft. Es zur Progression heranzuziehen würde die bewährte 8-Reps/3-Sessions-Logik verschlechtern. Daher ist es ein rein ergänzendes Anzeige-Signal.

### Verworfene Feature-Ideen (nicht erneut vorschlagen!)
- **Adaptiver Rest-Timer** — bei nur 2 Sätzen + Drop-Set kein spürbarer Nutzen.
- **Persönliche Rekorde (PRs)** — durch das ständige Auto-Up/Downgrade entsteht nie eine stabile Bestmarke.
- **Push-Benachrichtigungen aufs Handy** — ⚠️ **Diese Begründung ist überholt.**
  CORVIS ist seit August 2026 eine installierbare PWA und zeigt **lokale**
  Benachrichtigungen (siehe §17). Was weiterhin fehlt, ist echtes **Server-Push**
  (Web-Push mit VAPID) — also eine Erinnerung, die ankommt, ohne dass die App offen
  war. Das ist offen, nicht verworfen.

---

## 8. Das CORVIS-Designsystem

Dunkel, brutal-sportlich, mit Orange-Akzent. Definiert über CSS-Variablen (`:root`) in `fitness-frontend/src/index.css` (App) und inline in `fitness-landing.html` (Landing).

**Farb-Tokens:**
- `--bg: #080808` (fast schwarz), `--bg2: #0f0f0f`, `--bg3: #161616`
- `--orange: #FF4D00` (Signalfarbe), `--orange2: #ff6a2a`
- `--white: #f0ede8` (cremeweiß, kein reines Weiß)
- `--muted: #555`, `--muted2: #333`, `--muted3: #444` (App) — **Achtung:** `--muted3` existiert nur in der App-CSS, NICHT in der Landing-Page-CSS (dort führte das zu unsichtbaren Elementen → durch `#444` ersetzt).

**Schriften:**
- **Bebas Neue** (`--display`) — die große, kantige Headline-Schrift (Übungsnamen, Level-Zahlen, Logo).
- **DM Mono** (`--mono`) — die technische Mono-Schrift für Fließtext/Labels.

**Logo-Konvention:** "COR" weiß + "VIS" orange, zusammengeschrieben (`COR<span class="logo-vis">VIS</span>`), `letter-spacing: 0`. Wichtig: Im `<title>`-Tag und in Meta-Tags KEIN `<span>` verwenden (wird sonst als roher Text angezeigt).

**Wichtige Komponenten/Effekte:**
- Level-Up-Modal mit **Konfetti-Animation** (`ProgressionModal.jsx`).
- **Startseite:** eine große **Gesamtstärke-Zahl** (Summe der drei Level) und darunter
  das **Stärke-Dreieck** — ein Radar-SVG über PUSH / PULL / CORE, dessen Fläche mit
  den Leveln wächst. **Keine Übungskarten** (frühere Doku behauptete das; die
  Karten-Ansicht liegt heute unter `/exercises`).
- Konsistente deutsche UI-Sprache.

---

## 9. Die Landing Page (`/corvis/`)

Ein einzelnes Django-Template (`templates/fitness-landing.html`) mit Inline-CSS/JS. Sektionen-Reihenfolge (bewusst nach Storytelling **Problem → Lösung → Beweis → CTA** sortiert):

1. **Hero** — WebGL-Shader-Hintergrund (Three.js, orangene Lichtstrahlen). Headline "DEIN [WORT]. DEINE WAFFE." wobei das orange Wort per **Typewriter-Animation im Loop** wechselt: KÖRPER. → WILLE. → ANTRIEB. → FOKUS. → KAMPF. (kursiv, mit blinkendem Cursor). Hero-Typo nutzt `mix-blend-mode: screen`, damit der Text mit den Lichtstrahlen verschmilzt.
2. **Marquee** — Laufband mit Schlagworten.
3. **Intro** — These ("Das System ist das Problem, nicht du").
4. **Das Problem** — Schmerzpunkte + Stats (67% kündigen, etc.).
5. **CORVIS vs. Gym** — direkter Vergleich (zwei Spalten).
6. **Was CORVIS kann** — horizontaler Scroll-Bereich mit 4 Features, jeweils mit einem **CSS-Mockup** der echten App (Level-Up-Karte, Wochenplan-Grid, Statistik-Mockup mit Balkengraph, Übungs-Karten).
7. **Deine Verwandlung** — eine **Scroll-Flythrough-Sektion** (aus der inzwischen gelöschten AURELIA-Demo adaptiert, siehe §10): beim Scrollen "fährt" man durch emotionale Stationen Tag 1 → Tag 7 → Tag 30 → Tag 90 → Für immer (Zoom-Effekt, große Hintergrund-Zahl, Fortschritts-Ticks).
8. **Gemeinsam stärker** — eine **CMS-artige Live-Stats-Sektion** (ebenfalls aus AURELIA adaptiert): fetcht den öffentlichen Endpoint `GET /api/fitness/community-stats/` und zählt echte Aggregat-Zahlen über alle Nutzer hoch (Athleten, Workouts, Push-ups, Pull-ups, Plank-Minuten, Level-Ups) mit animierten Balken.
9. **CTA** — "Hör auf zu warten." + Button (magnetisch, folgt dem Cursor).
10. **Footer**.

**Verworfen / entfernt:** Ein Custom-Cursor (war eingebaut, auf Wunsch wieder raus — normaler Browser-Cursor). Die ursprüngliche "Drei Übungen"-Karten-Sektion wurde entfernt (zeigte zu viel App-Inhalt). Das SVG-Strichmännchen-Logo wurde durch reinen Text ersetzt.

---

## 10. Die AURELIA-Demo — gelöscht (August 2026)

`templates/aurelia-demo.html` unter `/aurelia/` war eine eigenständige Demo-Seite für eine fiktive Luxus-Immobilie ("AURELIA"), gebaut als Technik-Showcase (WebGL-Overlay, Scroll-Flythrough, mix-blend-mode-Typo, CMS-artige Daten, magnetische Buttons, golden Grading, Fake-Drohnen-Loop). **Die Seite existiert nicht mehr.**

Der Abschnitt bleibt stehen, weil §9 auf ihn verweist: zwei Sektionen der CORVIS-Landing-Page ("Deine Verwandlung", "Gemeinsam stärker") stammen von dort. Diese Technik lebt in der Landing Page weiter — nur die Demo-Seite selbst ist weg.

---

## 11. API-Referenz (alle Endpoints unter `/api/fitness/`)

**Auth (unter `/api/`):** `POST /api/token/` (Login), `POST /api/token/refresh/`, `POST /api/register/` (braucht einen geheimen `registration_key`).

**ViewSets:**
- `GET /exercises/` — Übungen mit Progressionen (öffentlich).
- `/user-progressions/` — die Level des Nutzers (PATCH zum Ändern).
- `/workouts/` + Custom-Actions:
  - `GET /workouts/current/` — heutiges Workout (get_or_create).
  - `POST /workouts/{id}/add_set/` — Satz hinzufügen/aktualisieren.
  - `POST /workouts/{id}/complete/` — Workout abschließen (löst Up/Downgrade + LevelEvents + Streak-Meilenstein aus, gibt `upgrades`/`downgrades` zurück).
  - `POST /workouts/{id}/reset/` — Workout löschen.
  - `GET /workouts/last_performance/` — letzte Werte je Übung (inkl. `drop_reached`).
  - `PUT /workouts/{id}/warmup/` — Aufwärm-Checkliste.

**Function-Views:**
- `GET /user/` — Nutzerdetails (inkl. `onboarding_completed`).
- `PUT /profile/picture/upload/`, `/profile/picture/delete/`, `/profile/settings/`.
- `POST /onboarding/calibrate/` — **Feature 1** (kalibriert + speichert + schließt Onboarding ab).
- `POST /onboarding/complete/`, `POST /onboarding/reset/`.
- `GET /streak/`, `POST /rest-day/`, `DELETE /rest-day/remove/` — **Feature 2**.
- `GET /timeline/` — **Feature 3**.
- `GET /weekly-review/` — **Feature 4**. ⚠️ Funktioniert, wird aber vom Frontend zwar geladen, aber nie angezeigt (siehe §7).
- `GET /community-stats/` — **Landing-Page Live-Stats** (öffentlich, kein Auth).

---

## 12. Frontend-Architektur (React)

**Routing** (`App.jsx`, `basename="/corvis-app"`): `/login`, `/register`, `/onboarding`, `/` (Home), `/workout`, `/exercises`, `/statistics`, `/profile`, `/training-days`, `/set-progression`. Geschützte Routen via `PrivateRoute`.

**State (Zustand):**
- `authStore` — eingeloggter User, Token.
- `workoutStore` — die zentrale Quelle der Wahrheit. Lädt in `initialize()` parallel: exercises, user-progressions, workouts, profile-settings, **streak, timeline, weekly-review**. (`weeklyReview` wird dabei bei jedem Start
mitgeladen und **nirgends gelesen** — siehe Feature 4 in §7.) Pattern: `isInitialized: false` + `initialize()` erzwingt nach Level-Änderungen ein frisches Neuladen, damit z.B. ein manuell geändertes Level sofort im Dashboard erscheint (nichts ist hardcoded). Actions u.a.: `getCurrentWorkout`, `addSet`, `completeWorkout` (lädt danach Workouts/Streak/Timeline neu), `markRestDay`, `unmarkRestDay`, `refreshStreak`, `updateTrainingDays`.

**Wichtige Views:**
- `HomeView` — Logo, **Wochentage-Leiste** (erledigte/heutige Tage), **Gesamtstärke**
  (Summe der drei Level) + **Stärke-Dreieck** (Radar über PUSH/PULL/CORE), drei
  Kennzahlen (🔥 Serie · Workouts · Ø Level), "Training starten", "Ruhetag einlegen".
  **Keine Übungskarten** und **kein** Wochenend-Banner — der Wochen-Rückblick wird
  zwar geladen, aber nicht gerendert (siehe Feature 4 in §7).
- `WorkoutView` — der Trainingsablauf. **`WORKOUT_STEPS` werden dynamisch** via `buildWorkoutSteps(exercises)` aus dem Store gebaut (NICHT hardcoded): 2 normale Sätze interleaved über die Hauptübungen, dann Drop-Sets, dann Core (CORE-Kategorie separat). Aufwärmen → Sätze (Reps-Input oder Timer) → Drop-Set → Abschluss-Modal.
- `StatisticsView` — Volumen-Stats, Streak (vom Backend), Timeline ("Deine Reise"), Workout-History.
- `OnboardingView` — der Kalibrierungs-Flow (Feature 1).
- `SetProgressionView` — manuelles Level-Ändern (setzt danach `isInitialized: false` + `initialize()`).
- `TrainingDaysView` — Trainingstage wählen.

**Komponenten:** `BottomNav`, `SetInput`, `TimerInput`, `RestTimer`, `WarmupChecklist`,
`CooldownChecklist` (Dehn-Checkliste nach dem Training), `DropSetInstructions`,
`FormTip` (aufklappbarer Form-Hinweis je Variante, Texte in `data/exerciseInfo.js`),
`IosInstallHint` (Installations-Tipp nur für iOS-Safari, siehe §17),
`ProgressionModal` (mit Konfetti).

---

## 13. Accounts & Test-Zugang

- **Alex** — Admin/Superuser (Haupt-Account des Besitzers).
- **test** / Passwort **test1234** — Test-Account zum Einloggen unter `/corvis-app/`.

(Frühere Test-User Sophie, Eric, Laura wurden gelöscht. Django speichert Passwörter nur als Hash — bestehende Passwörter können nicht ausgelesen, nur neu gesetzt werden.)

**DB-Aufräumung:** Es gab früher eine zweite Django-App "geo" (Geographie-Quiz), die komplett entfernt wurde — Code, Frontend, `INSTALLED_APPS`-Eintrag, URLs und 8 verwaiste DB-Tabellen (`geo_*`).

---

## 14. Sicherheit (Stand August 2026)

Ein dedizierter Security-/Technik-Durchgang hat die folgenden Punkte **erledigt** (jeweils ein eigener Commit):

- **✅ `DEBUG` ist jetzt `False` live.** Gesteuert über die Env-Var `DJANGO_DEBUG` (Default `True` für lokale Entwicklung; `docker-compose.yml` setzt `DJANGO_DEBUG=False` für den Live-Container). Stacktraces werden nicht mehr geleakt.
- **✅ WhiteNoise** liefert die statischen Dateien aus (Middleware direkt nach `SecurityMiddleware`, `STORAGES` mit `whitenoise.storage.CompressedStaticFilesStorage` — bewusst **ohne** Manifest/Hashing, damit die hart kodierten `/static/`-Pfade in den Templates inkl. des gehashten React-Bundles weiter funktionieren). Static läuft jetzt gzip-komprimiert mit Cache-Headern, auch bei `DEBUG=False`.
- **✅ Secrets aus settings.py in Env-Vars ausgelagert:** `SECRET_KEY` liest `DJANGO_SECRET_KEY`, `REGISTRATION_SECRET_KEY` liest `DJANGO_REGISTRATION_KEY` (jeweils mit dem alten Wert als Fallback für lokal). Der Registration-Key war **nie** im Frontend-Bundle (der User tippt ihn in ein Eingabefeld). In Produktion sollten echte Werte via Env gesetzt werden.
- **✅ `ALLOWED_HOSTS` eingeschränkt — kein Wildcard mehr.** Früher stand dort `["*"]`.
  Heute:
  ```python
  ALLOWED_HOSTS = os.environ.get(
      'DJANGO_ALLOWED_HOSTS', 'alex.volkmann.com,localhost,127.0.0.1').split(',')
  ```
  Überschreibbar per Env-Var (kommagetrennt). Dazu `CSRF_TRUSTED_ORIGINS` für
  `https://alex.volkmann.com` und `http://localhost:8000`.
- **✅ gunicorn statt `runserver`.** Der Django-Dev-Server ist nicht mehr im Einsatz
  (siehe §3) — er war nie für Produktion gedacht (Single-Thread, kein Härtung).
- **✅ Django auf 5.2.17 LTS** (August 2026). 4.2 hatte am 7. April 2026 EOL erreicht
  und bekam keine Sicherheitspatches mehr. Dazu **DRF 3.17.0**.
- **✅ Verwundbare Dependencies aktualisiert** (siehe §3): axios 1.18.1,
  react-router-dom 7.18.0, vite 7.3.5.
- **Eigene 404-Seite** (`templates/404.html`): `handler404 = 'meinprojekt.views.not_found'` (greift bei DEBUG=False) + Catch-All `re_path(r'^.*$', views.not_found)` am Ende der URLconf (Fallback). Echte Routen haben Vorrang, da die Catch-All zuletzt steht. Verhindert das Leaken der URL-Liste.

### Noch offen (bewusst aufgeschoben)
- **Git-Historie:** Die alten Secrets (SECRET_KEY, Registration-Key) stehen weiterhin in alten Commits. Echte Bereinigung (BFG / git filter-repo) + Rotation der Keys ist ein separater, invasiver Schritt (alle Commit-Hashes ändern sich, force-push nötig). **Empfehlung:** vor einer etwaigen Veröffentlichung des Repos nachholen + neue Keys generieren.
- **npm-Findings: 7, nicht 1.** Frühere Doku sprach von "1 verbleibender low-Vuln
  (esbuild)". Der tatsächliche Stand (`npm audit` im Container, August 2026) ist
  **7 Findings: 1 low + 6 high**:

  | Paket | Schwere | Kommt aus | Landet im Browser-Bundle? |
  |-------|---------|-----------|---------------------------|
  | `brace-expansion` | high | eslint | ❌ nein |
  | `esbuild` | low | vite | ❌ nein |
  | `js-yaml` | high | eslint | ❌ nein |
  | `nanoid` | high | postcss | ❌ nein |
  | `postcss` | high | Build-Kette | ❌ nein |
  | `react-router` | high | — | ✅ **ja** |
  | `react-router-dom` | high | zieht `react-router` | ✅ **ja** |

  **Einordnung:** **5 der 7** sind reines Build-Werkzeug (`devDependencies`) — sie
  laufen nur beim Bauen und Linten, nie im Browser des Nutzers. Die zwei
  verbleibenden (`react-router` / `react-router-dom` 7.18.0) sind echte
  Produktions-Abhängigkeiten und **werden mit ausgeliefert**. Ihr Advisory betrifft
  allerdings einen **CSRF-Bypass im RSC-Modus** (React Server Components) — den
  CORVIS nicht benutzt: die App ist eine reine SPA gegen ein Django-Backend. Damit
  ist das Finding hier **nicht ausnutzbar**, aber es sollte bei Gelegenheit
  mit `npm audit fix` weggeräumt werden (die Fixes gelten als nicht-breaking).

  ```bash
  docker compose exec django-dev bash -c "cd /code/fitness-frontend && npm audit"
  ```

- **Echtes Server-Push fehlt** — die PWA kann nur lokale Benachrichtigungen zeigen
  (siehe §17).

---

## 15. Git / Versionierung

- Remote: `git@github.com:Taze00/django.git` (SSH-Remote heißt `alex`, HTTPS-Remote `origin`). Push via `git pull alex main` / `git push alex main`.
- Commit-Konvention: pro Feature/Fix ein Commit, mit `Co-Authored-By`-Trailer.
- Wichtige Commit-Reihen: das CORVIS-Redesign + Entfernung der geo-App → die 5 CORVIS-Features (je ein Commit) → Landing-Page-Überarbeitung → **der Security-Durchgang** (4 Commits: WhiteNoise/DEBUG, Secrets-Env, Dependency-Updates, Cleanup) → **der Branch `django-upgrade`** (August 2026): 134 Tests, reproduzierbare Migrationskette, DRF 3.17, Django 5.2.17, dazu `tools/shots_corvis.py`. Der Branch ist in `main` gemerged.

---

## 16. Tests

Seit August 2026 gibt es eine echte Testabdeckung — sie ist das Sicherheitsnetz,
das das Django-Upgrade 4.2 → 5.2 überhaupt vertretbar gemacht hat.

```bash
docker compose exec django-dev python manage.py test fitness \
    --settings=meinprojekt.settings_test
```

**134 Tests** in `fitness/tests/`, Laufzeit ~5 Sekunden:

| Datei | Deckt ab |
|-------|----------|
| `test_calibration.py` | Die Justier-Logik aus Feature 1 (alle `ratio`-Bänder, Clamping auf 1–7, das 0-Reps-Problem) |
| `test_streak.py` | Serien-Berechnung: übersprungene Nicht-Trainingstage, Ruhetage, der heutige Tag |
| `test_level_changes.py` | Auf- und Abstieg: Schwellen, `custom_target`-Zuschlag, Abstiegs-Schleifen-Schutz, Max-Level |
| `test_api_smoke.py` | Alle Endpoints: Auth, Workout-Ablauf, Onboarding, Profil |

**Warum eigene Settings?** `meinprojekt/settings_test.py` existiert nur, damit der
Testlauf **nicht** die PostgreSQL-Instanz braucht (er nutzt SQLite im Speicher) und
damit er unabhängig von den Env-Vars des Live-Containers läuft. Für alles andere
gilt weiter `meinprojekt/settings.py`.

> **Migrationskette:** Migration `0009_seed_exercises_and_progressions` legt Übungen,
> die 21 Progressionen und die Startlevel **per Migration** an. Vorher kamen die
> Stammdaten nur über ein Management-Command in die Datenbank — eine frische
> Datenbank war damit nicht reproduzierbar, und genau daran scheiterten die Tests.
> `0009` arbeitet durchgehend mit `get_or_create` auf `(exercise, level)`: auf der
> Produktionsdatenbank ändert die Migration **nichts**, auf einer leeren baut sie
> alles auf.

---

## 17. PWA & Benachrichtigungen

CORVIS ist seit August 2026 eine **installierbare Progressive Web App**. Das war der
Punkt, an dem die alte Absage an Reminder (§7, "verworfene Ideen") hinfällig wurde.

**Was fertig ist:**
- **`manifest.json`** (`fitness-frontend/public/`): `display: standalone`,
  `start_url` und `scope` auf `/corvis-app/`, `orientation: portrait-primary`,
  Theme/Background `#0a0a0a`. Icons in 192 und 512 px, das 512er zusätzlich als
  `maskable`. Android/Chrome bietet damit "Zum Startbildschirm hinzufügen" an.
- **Service Worker** (`public/sw.js`) — **bewusst minimal**: `install` +
  `activate` (mit `skipWaiting` / `clients.claim`) und ein `notificationclick`-Handler,
  der eine bereits offene CORVIS-Ansicht in den Vordergrund holt statt einen zweiten
  Tab zu öffnen. Registriert wird er in `main.jsx` unter `/static/fitness/sw.js`.
- **Lokale Benachrichtigungen** (`src/utils/notify.js`): Am Ende der Pause meldet
  sich `showRestDoneNotification()` mit "Pause vorbei 💪" — auch wenn der Bildschirm
  aus ist oder die App im Hintergrund liegt. Die Erlaubnis wird **nie** ungefragt
  abgefragt, sondern nur per Tap im Profil ("Pausen-Benachrichtigung", `ProfileView.jsx`)
  — iOS verlangt eine echte Nutzer-Geste.
- **Sauberer Fallback:** Ohne Erlaubnis oder Unterstützung gibt die Funktion `false`
  zurück (kein Fehler), und `RestTimer` fällt auf **Ton + Vibration** zurück.
- **`IosInstallHint.jsx`:** iOS zeigt keinen automatischen Install-Prompt. Der Hinweis
  erscheint deshalb nur auf iOS-Safari, nicht auf Desktop/Android, nicht wenn die App
  schon `standalone` läuft, und nicht mehr nach dem Wegtippen (`localStorage`).

> **iOS-Eigenheit:** Web-Benachrichtigungen funktionieren dort **nur als installierte
> PWA** ("Zum Home-Bildschirm") und erst ab iOS 16.4. Im normalen Safari-Tab greift
> stumm der Ton-Fallback — das ist kein Fehler.

**Was NICHT drin ist (und warum):**
- **Kein Offline-Caching.** Der Service Worker hat **absichtlich keinen
  `fetch`-Handler** (so steht es auch als Kommentar in `sw.js`). Ein halbherziger
  Cache hätte veraltete Bundles ausgeliefert — das Thema ist auf später vertagt.
- **Kein echtes Server-Push.** Es gibt keinen `push`-Handler im Service Worker und
  kein `PushManager.subscribe()`. Alle Benachrichtigungen entstehen **im Browser des
  Nutzers**, während die App läuft. Eine Erinnerung "du hast heute noch nicht
  trainiert", die ohne offene App ankommt, ist damit **nicht** möglich. Dafür bräuchte
  es Web-Push mit VAPID-Schlüsseln und ein Abo-Modell im Backend (siehe §18).

> **Nach jeder Änderung an `public/`** (Manifest, Icons, `sw.js`) gilt der volle
> Frontend-Deploy aus §4 — die Dateien wandern über den Vite-Build nach
> `static/fitness/` und müssen danach durch `collectstatic` + `restart`.

---

## 18. Mögliche nächste Schritte (Ideenraum für die andere KI)

Bereits abgedeckt: adaptive Progression, Kalibrierung, Streak-Schutz, Timeline, Wochen-Rückblick, Drop-Set-Tracking. Verworfen wurde: adaptiver Rest-Timer, PRs, native Push-Notifications (siehe §7).

Bereits erledigt im Security-Durchgang (siehe §14): DEBUG=False + WhiteNoise, Secrets in Env-Vars, Dependency-Updates, Cleanup (.bak-Dateien + totes CSS).

**Inzwischen ebenfalls erledigt (August 2026):** gunicorn statt `runserver`,
`ALLOWED_HOSTS` eingeschränkt, Django 5.2 LTS + DRF 3.17, PWA installierbar mit
lokalen Benachrichtigungen, 134 Tests (§16).

Offene Baustellen, nach Aufwand sortiert:

1. **Feature 4 fertigbauen** — der Wochen-Rückblick wird bei jedem App-Start geladen
   und dann weggeworfen. Das Bauteil in `HomeView.jsx` fehlt, Daten und CSS liegen
   bereit (siehe §7). Der billigste sichtbare Gewinn im ganzen Projekt.
2. **`npm audit fix`** — 7 Findings, davon 5 reines Build-Werkzeug (siehe §14).
3. **Echtes Server-Push (Web-Push + VAPID)** — Trainings-Erinnerungen, die auch
   ankommen, wenn die App zu ist. Braucht `pywebpush`, VAPID-Schlüsselpaar,
   ein `PushSubscription`-Modell und einen `push`-Handler im Service Worker (§17).
4. **Offline-Modus** — der Service Worker hat bewusst **keinen** `fetch`-Handler.
   Ein Cache für die App-Shell würde das Training auch ohne Netz ermöglichen.
5. **Git-Historie der Secrets bereinigen** + Keys rotieren (siehe §14).
6. **Soziale Komponente** (Freunde, geteilte Streaks) — die `community-stats` sind
   erst der Anfang.
7. **Mehr Übungen / Trainingspläne** ohne die "minimal & effektiv"-Philosophie zu
   verwässern.
8. **Audio/Voice-Guidance** während des Workouts.

---

## Historie dieser Datei

Bis August 2026 lagen neben dieser Doku noch `FITNESS_APP_COMPLETE_SPEC.md` und
`BUILD_WORKFLOW.md` im Repo, beide oben als „VERALTET" markiert. Sie wurden
**gelöscht**, ihr brauchbarer Inhalt steht jetzt hier:

- Der **9-Schritte-Trainingsablauf** und die **Pausenzeiten** (180 s / 300 s) aus der
  SPEC stehen in §6.
- Die **manuellen Build-Schritte** aus `BUILD_WORKFLOW.md` stehen in §4 — dort
  allerdings **vollständig**: Die alte Datei kannte `collectstatic` nicht und
  widersprach sich selbst (sie nannte `static/fitness/` gitignored und forderte zwei
  Zeilen später `git add static/fitness/`).
- Die **Startlevel-Tabelle** der SPEC war schlicht falsch (Push-ups L3, Planks L1
  statt L4/L3) — die richtige Tabelle steht in §6, mitsamt Warnung.

---

*Ende der Dokumentation. Bei Unklarheiten: der echte Code in `fitness/` (Backend) und
`fitness-frontend/src/` (Frontend) ist die maßgebliche Quelle — diese Doku beschreibt
den Stand **August 2026**.*
