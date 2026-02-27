# 🏋️ CALISTHENICS TRACKER — Komplette Systemdokumentation

**Status:** Phase 6 + 7 abgeschlossen (Feb 27, 2026)
**Live:** https://alex.volkmann.com/fitness/
**Git:** https://github.com/...

---

## 📋 INHALTSVERZEICHNIS

1. [Übersicht](#übersicht)
2. [Trainingsplan](#trainingsplan)
3. [Progressives Overload System](#progressives-overload-system)
4. [Technische Architektur](#technische-architektur)
5. [REST API](#rest-api)
6. [Offline-Modus (PWA)](#offline-modus-pwa)
7. [User Flows](#user-flows)
8. [Datenbank-Schema](#datenbank-schema)
9. [Bekannte Limitationen](#bekannte-limitationen)
10. [Build & Deployment](#build--deployment)

---

## 1. ÜBERSICHT

### Was ist die App?
**Calisthenics Tracker** ist eine Progressive Web App zum Tracken von Calisthenics-Training (Körpergewicht-Training) mit automatischer Progression.

**Kernfeatures:**
- ✅ 5-Tages-Trainingsplan (Mo-Fr trainieren, Sa-So Ruhe)
- ✅ 6 Calisthenics-Übungen mit jeweils 3-7 Progressionsstufen
- ✅ Set-Tracking (Reps oder Sekunden je nach Übung)
- ✅ Automatische Progression (Progressive Overload)
- ✅ 90-Sekunden-Rest-Timer zwischen Sets
- ✅ PWA (installierbar auf Mobile, Offline-Funktion)
- ✅ JWT-basierte Authentifizierung

### Tech-Stack

**Backend:**
- Django 4.2 + Django REST Framework
- PostgreSQL (Datenbank)
- JWT (Token-basierte Auth)
- Python 3.11

**Frontend:**
- React 18 + React Router v6
- Vite (Build-Tool)
- Tailwind CSS v4 (Styling)
- Zustand (State Management)
- Axios (HTTP-Client mit JWT-Interceptor)
- Chart.js (für zukünftige Stats-Visualisierung)

**Deployment:**
- Docker Compose (lokale Entwicklung)
- Nginx (Reverse Proxy / Static Files)
- Let's Encrypt (HTTPS)

---

## 2. TRAININGSPLAN

### 📅 5-Tages-Rotation

| Tag | Übungen | Rest? |
|-----|---------|-------|
| **Montag** | Push-up, Pull-up, Squat, Hanging Knee Raise | ❌ |
| **Dienstag** | Push-up, Pull-up, Lunge, Hollow Hold | ❌ |
| **Mittwoch** | Pull-up, Push-up, Squat, Hollow Hold | ❌ |
| **Donnerstag** | Pull-up, Push-up, Squat, Hanging Knee Raise | ❌ |
| **Freitag** | Push-up, Pull-up, Squat, Hanging Knee Raise, Hollow Hold | ❌ |
| **Samstag** | - | ✅ Rest Day |
| **Sonntag** | - | ✅ Rest Day |

### 🏋️ Die 6 Calisthenics-Übungen

#### 1. **Push-up** (Drücken)
- **Zieltyp:** Reps (Wiederholungen)
- **Progressionen (7 Stufen):**
  1. Wall Push-up (an der Wand)
  2. Incline Push-up (erhöht)
  3. Knee Push-up (auf den Knien)
  4. Standard Push-up (normal)
  5. Diamond Push-up (schwieriger)
  6. Decline Push-up (Füße erhöht)
  7. Pike Push-up (noch schwieriger)

#### 2. **Pull-up** (Ziehen)
- **Zieltyp:** Reps
- **Progressionen (7 Stufen):**
  1. Dead Hang (30s halten)
  2. Active Hang (Schultern aktiviert)
  3. Scapular Pull-up (Schulterblattzug)
  4. Negative Pull-up (negativ)
  5. Pull-up (standard)
  6. Chest-to-Bar (Brust zur Stange)
  7. Weighted Pull-up (mit Gewicht)

#### 3. **Squat** (Beine)
- **Zieltyp:** Reps
- **Progressionen (5 Stufen):**
  1. Assisted Squat (mit Hilfe)
  2. Bodyweight Squat (normal)
  3. Reverse Lunge (alternative)
  4. Bulgarian Split Squat (eine Seite)
  5. Pistol Squat (Einbein)

#### 4. **Lunge** (Beine - alternative)
- **Zieltyp:** Reps
- **Progressionen (5 Stufen):**
  1. Assisted Lunge
  2. Bodyweight Lunge
  3. Reverse Lunge
  4. Bulgarian Split Lunge
  5. Jumping Lunge

#### 5. **Hanging Knee Raise** (Core)
- **Zieltyp:** Reps
- **Progressionen (5 Stufen):**
  1. Dead Hang (vorbereitung)
  2. Scapular Pull (Schulterblattzug)
  3. Knee Raise (Knie heben)
  4. Leg Raise (Beine heben)
  5. Toes-to-Bar (Zehen zur Stange)

#### 6. **Hollow Hold** (Core - Halten)
- **Zieltyp:** Seconds (Sekunden halten)
- **Progressionen (3 Stufen):**
  1. Hollow Hold (Grund-Position, 20s)
  2. Extended Hollow Hold (30s)
  3. Hollow Hold Plus (40s+)

---

## 3. PROGRESSIVES OVERLOAD SYSTEM

### 🔄 Wie funktioniert Progressive Überload?

**Progressive Overload** = Sicherstelle, dass die Übung immer schwieriger wird, indem man:
1. Mehr Wiederholungen macht (Volume)
2. Schwierigere Variante macht (Progression Level)
3. Besser Form (Quality)

### 📊 Upgrade-Bedingungen

Eine Übung wird nur dann **upgraded**, wenn folgende Bedingungen erfüllt sind:

```
Upgrade verfügbar wenn:
- ✅ Letzten 3 Workouts: mindestens 2 Sets mit ≥ target_value Reps/Sekunden
- ✅ UND pain_level < 4 (keine Verletzungen)
- ✅ UND form_ok = True (saubere Form)

Beispiel (Push-up, target = 8 Reps):
- Workout 1: Set 1: 8 Reps ✓, Set 2: 8 Reps ✓ → sessions_at_target = 1
- Workout 2: Set 1: 9 Reps ✓, Set 2: 8 Reps ✓ → sessions_at_target = 2
- Workout 3: Set 1: 10 Reps ✓, Set 2: 9 Reps ✓ → sessions_at_target = 3
→ UPGRADE verfügbar! 🎉
```

### 📈 Sessions-Tracking

**Session = ein komplettes Workout für eine Übung**

Jede `UserExerciseProgression` hat:
```python
{
  user: User,
  exercise: Exercise (z.B. Push-up),
  current_progression: Progression (z.B. "Standard Push-up"),
  sessions_at_target: int (wie viele Sessions die target_value erfüllt haben),
}
```

**Beispiel:**
- Push-up: current_progression = "Standard Push-up", target = 8 Reps, sessions_required = 3
- User trainiert 3x die Woche Push-up
- Nach 3 Trainings mit jeweils ≥8 Reps → Upgrade möglich auf "Diamond Push-up"

### 🎯 Upgrade-Prozess (Manuell)

1. User completet Workout
2. Backend prüft: "Kann user upgrades machen?"
3. Wenn ja → Modal zeigt: "Diamond Push-up verfügbar!"
4. User klickt "Upgrade" oder "Skip"
5. `sessions_at_target` wird reset, neue Progression wird gesetzt

---

## 4. TECHNISCHE ARCHITEKTUR

### 🏗️ System-Überblick

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (React App)                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ WorkoutView | ProfileView | Login                  │ │
│  │ (React Router, Zustand Store, Offline-Support)     │ │
│  └─────────────────────────────────────────────────────┘ │
│              ↓↑                                            │
│         Service Worker (PWA)                              │
│         (Offline Cache, Sync)                             │
└─────────────────────────────────────────────────────────┘
              ↓↑ (REST API + JWT)
┌─────────────────────────────────────────────────────────┐
│              DJANGO REST API (Backend)                    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ /api/fitness/workouts/                             │ │
│  │ /api/fitness/exercises/                            │ │
│  │ /api/fitness/user/progressions/                    │ │
│  │ /api/fitness/user/profile/                         │ │
│  │ /api/fitness/stats/overview/                       │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
              ↓↑
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Exercise | Progression | UserExerciseProgression   │ │
│  │ Workout | WorkoutSet | WarmupChecklist             │ │
│  │ User | UserProfile                                  │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 5. REST API

### 🔐 Authentifizierung

**JWT Token-basiert (Token Obtain Pair)**

```bash
# 1. Login (get token)
POST /api/fitness/auth/login/
{
  "username": "alex",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# 2. Alle zukünftigen Requests: Header hinzufügen
Authorization: Bearer <access_token>
```

### 📚 API Endpoints

#### **Exercises (Read-Only)**

```bash
# Alle Exercises mit Progressionen abrufen
GET /api/fitness/exercises/

Response:
[
  {
    "id": 1,
    "name": "Push-up",
    "category": "PUSH",
    "description": "...",
    "progressions": [
      {
        "id": 1,
        "name": "Wall Push-up",
        "level": 1,
        "target_type": "reps",
        "target_value": 8,
        "sets_required": 2,
        "sessions_required": 3
      },
      ...
    ]
  },
  ...
]

# Einzelnes Exercise
GET /api/fitness/exercises/{id}/

# Filtern nach Kategorie
GET /api/fitness/exercises/?category=PUSH
```

#### **Workouts (CRUD)**

```bash
# Heute's Workout abrufen/erstellen
GET /api/fitness/workouts/current/

Response:
{
  "id": 123,
  "user": 1,
  "date": "2026-02-27",
  "workout_type": "PUSH",
  "completed": false,
  "completed_at": null,
  "duration_seconds": 0,
  "sets": [
    {
      "id": 1,
      "exercise": 1,  // Push-up
      "set_number": 1,
      "reps": 8,
      "seconds": null,
      "is_drop_set": false
    },
    ...
  ],
  "warmup": {
    "id": 1,
    "completed_shoulder_rolls": true,
    "completed_arm_circles": true,
    ...
  }
}

# Set speichern/updaten
POST /api/fitness/sets/
{
  "workout": 123,
  "exercise": 1,
  "set_number": 1,
  "reps": 10,
  "is_drop_set": false
}

# Workout als completed markieren
POST /api/fitness/workouts/{id}/complete/

Response:
{
  "success": true,
  "workout": {...},
  "upgrades": [
    {
      "exercise_id": 1,
      "exercise_name": "Push-up",
      "old_progression": {...},
      "new_progression": {...},
      "qualifying_workouts": 3,
      "average_reps": 8.5
    }
  ]
}
```

#### **User Progressions**

```bash
# Alle User Progressions abrufen
GET /api/fitness/user/progressions/

Response:
[
  {
    "id": 1,
    "user": 1,
    "exercise": 1,
    "current_progression": 4,  // ID des aktuellen Levels
    "sessions_at_target": 2,
  },
  ...
]

# Progression upgraden
POST /api/fitness/user/upgrade-progression/
{
  "exercise_id": 1,
  "progression_id": 5  // Neue Progression
}

# Verfügbare Upgrades prüfen
GET /api/fitness/user/check-upgrades/

Response:
{
  "upgrades": [
    {
      "exercise_id": 1,
      "exercise_name": "Push-up",
      "current_progression": 4,
      "next_progression": 5,
      "next_progression_name": "Diamond Push-up"
    }
  ]
}
```

#### **User Profile**

```bash
# Profile abrufen
GET /api/fitness/user/profile/

Response:
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "alex",
    "email": "alex@example.com"
  },
  "avatar": "https://...",
  "bio": "Calisthenics enthusiast"
}

# Profile updaten
PUT /api/fitness/user/profile/
{
  "bio": "New bio",
  "avatar": <file>
}
```

#### **Stats (Read-Only)**

```bash
# Overview Stats
GET /api/fitness/stats/overview/

Response:
{
  "total_workouts": 15,
  "total_time_seconds": 43200,  // 12 Stunden
  "total_reps": 450,
  "total_sets": 90,
  "current_streak": 3  // Tage hintereinander
}

# Exercise Progress (Zeit-Verlauf)
GET /api/fitness/stats/exercise-progress/?exercise_id=1&days=30

Response:
{
  "exercise_name": "Push-up",
  "current_progression": "Standard Push-up",
  "data_points": [
    {
      "date": "2026-02-25",
      "set1_reps": 8,
      "set2_reps": 8,
      "total_reps": 16
    },
    {
      "date": "2026-02-26",
      "set1_reps": 9,
      "set2_reps": 8,
      "total_reps": 17
    },
    ...
  ]
}

# Progression History
GET /api/fitness/stats/progression-history/?exercise_id=1

Response:
{
  "exercise_name": "Push-up",
  "progressions": [
    {
      "progression_name": "Wall Push-up",
      "level": 1,
      "started_at": "2026-01-15",
      "ended_at": "2026-02-01",
      "total_workouts": 10
    },
    ...
  ]
}
```

---

## 6. OFFLINE-MODUS (PWA)

### 🔌 Progressive Web App Features

**Die App funktioniert auch ohne Internet!**

#### Service Worker Caching-Strategie

```javascript
// vite-plugin-pwa generiert automatisch
// Workbox-basierte Caching

Precache (sofort verfügbar):
- index.html
- App Shell (JS, CSS)
- Icons, Manifest

Network-First (Online bevorzugt):
- API Calls
- /api/fitness/...

Cache-First (Offline möglich):
- Static Assets
- Images
```

#### Wie funktioniert es?

1. **Online-Zustand:**
   - Normale API-Calls → Backend
   - Daten werden gecacht
   - Alles funktioniert wie normal

2. **Offline-Zustand:**
   - API-Calls schlagen fehl
   - Frontend nutzt gecachte Daten
   - Set-Eingaben werden **lokal im IndexedDB gespeichert**
   - Ikonöff markiert den Status

3. **Rückkehr zu Online:**
   - Frontend prüft Auto-Sync
   - Offline-Daten werden hochgeladen
   - Cache wird aktualisiert

#### IndexedDB (Lokaler Speicher)

```javascript
// Offline-Daten werden hier gespeichert:
IndexedDB {
  "fitness-workouts": [
    { workout_id: 123, sets: [...], synced: false }
  ],
  "fitness-cache": [
    { key: "exercises", data: [...], timestamp: ... }
  ]
}
```

### 📱 PWA Installation

**Auf Android (Chrome):**
1. App öffnen: https://alex.volkmann.com/fitness/
2. Menü (3 Punkte) → "Zum Startbildschirm hinzufügen"
3. App wird wie native App installiert

**Auf iOS (Safari):**
1. Share → "Zum Home-Bildschirm"
2. App-Icon erscheint auf dem Screen

**Funktionalität:**
- App lädt schneller (aus lokalem Cache)
- Funktioniert offline
- Kann Push-Notifications erhalten (zukünftig)
- Speicher auf dem Gerät

---

## 7. USER FLOWS

### 🔄 Kompletter Workout-Flow

#### **Schritt 1: Login**
```
[Browser] → GET /fitness/
          ↓
        [Login Component]
          ↓
      [Username + Password eingeben]
          ↓
    POST /api/fitness/auth/login/
          ↓
      [JWT Token erhalten]
          ↓
    [Token in localStorage speichern]
          ↓
   [Redirect zu /fitness/ (WorkoutView)]
```

#### **Schritt 2: Workout laden**
```
[WorkoutView Mount]
          ↓
  initialize() aufgerufen
          ↓
  fetchCurrentWorkout()
  ├─ GET /api/fitness/workouts/current/
  └─ Erstellt Workout für heute falls nicht vorhanden
          ↓
  fetchUserProgressions()
  ├─ GET /api/fitness/user/progressions/
  └─ Lädt aktuellen Progress Status
          ↓
  fetchExercises()
  ├─ GET /api/fitness/exercises/
  └─ Lädt alle Übungen + Progressionen
          ↓
  [Workout wird angezeigt]
```

#### **Schritt 3: Set Input**
```
[User klickt auf "Set 1"]
          ↓
    [Set Input expandiert]
          ↓
[User gibt 8 Reps ein + speichern drückt]
          ↓
   POST /api/fitness/sets/
   {
     "workout": 123,
     "exercise": 1,
     "set_number": 1,
     "reps": 8
   }
          ↓
[Set wird in Backend gespeichert]
          ↓
[Rest Timer zeigt: 90 Sekunden]
          ↓
[Set Button wird grün (✓ 8 reps)]
```

#### **Schritt 4: Workout Complete**
```
[User klickt "Complete Workout"]
          ↓
  setIsCompleting(true)
          ↓
 POST /api/fitness/workouts/{id}/complete/
 {
   "completed": true
 }
          ↓
[Backend prüft: Upgrades verfügbar?]
   ├─ Für jede Übung
   ├─ Schaut letzte 3 Workouts
   └─ Wenn sessions_at_target = 3 → Upgrade!
          ↓
[Response mit upgrades Array]
          ↓
[Wenn upgrades.length > 0]
  ├─ Modal zeigt: "Push-up → Diamond Push-up"
  └─ User can "Upgrade" oder "Skip"
          ↓
[Button wird grün mit ✓]
[Button wird disabled (heute nicht mehr clickbar)]
```

#### **Schritt 5: Progression Upgrade (Optional)**
```
[User sieht Modal: "Push-up upgraden?"]
          ↓
    [User klickt "Upgrade"]
          ↓
POST /api/fitness/user/upgrade-progression/
{
  "exercise_id": 1,
  "progression_id": 5
}
          ↓
[Backend ändert: UserExerciseProgression.current_progression = 5]
[sessions_at_target wird reset = 0]
          ↓
[Modal schliesst]
[Nächsten Tag: Standard Push-up wird mit neuer Progression angezeigt]
```

---

## 8. DATENBANK-SCHEMA

### 📊 Tabellen-Struktur

#### **User (Django Default)**
```python
User {
  id: int,
  username: str,
  email: str,
  password_hash: str,
  first_name: str,
  last_name: str,
  is_active: bool,
  date_joined: datetime
}
```

#### **UserProfile (Zusatz)**
```python
UserProfile {
  id: int,
  user: ForeignKey[User],
  avatar: ImageField (nullable),
  bio: TextField,
  created_at: datetime,
  updated_at: datetime
}
```

#### **Exercise**
```python
Exercise {
  id: int,
  name: str (z.B. "Push-up"),
  category: str (PUSH, PULL, LEGS, CORE),
  description: str,
  equipment: str (NONE, BAR, RINGS),
  is_timed: bool (False = Reps, True = Seconds)
}
```

#### **Progression**
```python
Progression {
  id: int,
  exercise: ForeignKey[Exercise],
  name: str (z.B. "Diamond Push-up"),
  level: int (1, 2, 3...),
  order: int,
  target_type: str (reps | hold),
  target_value: int (z.B. 8 = 8 Reps),
  sets_required: int (mindestens 2 Sets mit target_value),
  sessions_required: int (mindestens 3 Sessions),
  description: str
}
```

#### **UserExerciseProgression**
```python
UserExerciseProgression {
  id: int,
  user: ForeignKey[User],
  exercise: ForeignKey[Exercise],
  current_progression: ForeignKey[Progression],
  sessions_at_target: int (Default: 0),

  Constraints: UNIQUE(user, exercise)
}

# Beispiel:
{
  id: 1,
  user: alex,
  exercise: Push-up,
  current_progression: Progression(4),  // Standard Push-up
  sessions_at_target: 2  // 2 von 3 erforderlich
}
```

#### **Workout**
```python
Workout {
  id: int,
  user: ForeignKey[User],
  date: date (z.B. 2026-02-27),
  workout_type: str (optional, z.B. PUSH/PULL),
  week_number: int,
  completed: bool (False bis Complete-Button geklickt),
  completed_at: datetime (nullable),
  duration_seconds: int (berechnet aus created_at bis completed_at),
  created_at: datetime,
  updated_at: datetime
}

# Beispiel:
{
  id: 123,
  user: alex,
  date: 2026-02-27,
  completed: true,
  duration_seconds: 2400,  // 40 Minuten
  sets: [Set(...), Set(...), ...]
}
```

#### **WorkoutSet**
```python
WorkoutSet {
  id: int,
  workout: ForeignKey[Workout],
  exercise: ForeignKey[Exercise],
  set_number: int (1, 2, 3),
  reps: int (nullable, z.B. 8),
  seconds: int (nullable, z.B. 45),
  is_drop_set: bool (True für Set 3),
  created_at: datetime,
  updated_at: datetime
}

# Beispiel:
{
  id: 1,
  workout: 123,
  exercise: 1 (Push-up),
  set_number: 1,
  reps: 8,
  seconds: null
}
```

#### **WarmupChecklist**
```python
WarmupChecklist {
  id: int,
  workout: ForeignKey[Workout],
  completed_shoulder_rolls: bool,
  completed_arm_circles: bool,
  completed_jumping_jacks: bool,
  completed_inchworms: bool,
  completed_bodyweight_squats: bool
}
```

### 🔑 Relationships (Diagramm)

```
User
├─ UserProfile (1:1)
├─ UserExerciseProgression (1:N)
│  └─ Exercise (M:1)
│     └─ Progression (1:N)
├─ Workout (1:N)
│  ├─ WorkoutSet (1:N)
│  │  └─ Exercise (M:1)
│  └─ WarmupChecklist (1:1)

Beispiel:
user = alex
├─ UserExerciseProgression(Push-up → Standard Push-up, sessions=2)
├─ Workout(2026-02-27, completed)
│  ├─ WorkoutSet(Push-up, Set 1, 8 Reps)
│  ├─ WorkoutSet(Push-up, Set 2, 8 Reps)
│  └─ WarmupChecklist(all_completed=true)
```

---

## 9. BEKANNTE LIMITATIONEN

### ⚠️ Drop Sets
**Was sind Drop Sets?**
- Set 3 nennt sich "Drop Set" 🔥
- Das ist ein Calisthenics-Konzept, aber hier wird es wie ein normales Set behandelt
- **Problem:** Nicht klar erklärt, was ein Drop Set wirklich ist

**Zukünftige Verbesserung:**
- Drop Set Modal mit Erklärung
- Leichtere Variante tracken (z.B. "Incline Push-up nach Standard")

### ⚠️ Stats im Hintergrund
**Was bedeutet das?**
- Stats-Tab existiert nicht mehr in der Navigation
- Daten werden aber trotzdem im Hintergrund gespeichert
- User kann seine Progress nicht sehen

**Zukünftige Verbesserung:**
- Stats-Tab in Profile integrieren
- Graphische Darstellung der Progression
- Export-Funktion (PDF/CSV)

### ⚠️ Keine Anpassung nach Schmerz
**Was bedeutet das?**
- pain_level und form_ok sind noch im Code, aber nicht im UI sichtbar
- User kann nicht angeben, ob Form sauber war oder ob Schmerz vorhanden

**Zukünftige Verbesserung:**
- Nach Workout: "Form war sauber?" + "Schmerz Level?"
- Wenn Schmerz > 3 → keine Zählung

### ⚠️ Keine Rest-Tage Anpassung
- Sa/So sind immer Ruhetage
- User kann nicht ändern
- Zukünftig: Custom Schedule

---

## 10. BUILD & DEPLOYMENT

### 🔨 Lokale Entwicklung

```bash
# 1. Repo clonen
git clone ...
cd alex-django

# 2. Docker starten
docker compose up -d

# 3. Datenbank initialisieren
docker compose exec django-dev python3 manage.py migrate
docker compose exec django-dev python3 manage.py createsuperuser

# 4. Daten laden
docker compose exec django-dev python3 manage.py seed_exercises

# 5. Frontend entwickeln
docker compose exec django-dev bash -c "cd fitness-frontend && npm install && npm run dev"

# 6. Öffnen in Browser
http://localhost:3000/fitness/
```

### 🚀 Production Deploy

#### **Frontend Build & Deploy**

```bash
cd fitness-frontend

# Build (neue JS/CSS mit Hashes)
npm run deploy

# Das macht automatisch:
# 1. npm run build → Vite buildet zu dist/
# 2. rm -rf ../static/fitness/assets → alte Assets löschen
# 3. rm -f ../static/fitness/sw.js workbox-* → alte SW löschen
# 4. cp -r dist/* ../static/fitness/ → neue Dateien kopieren

# ⚠️ WICHTIG: Hash manuell updaten!
# Neuen Hash auslesen aus: static/fitness/index.html
# In templates/fitness.html Zeile 16 updaten:
# <script src="/static/fitness/assets/index-[NEW_HASH].js">
```

#### **Django Deployment**

```bash
# Collectstatic (Static Files sammeln)
python3 manage.py collectstatic --noinput

# Migrations runnen
python3 manage.py migrate

# Server starten
gunicorn meinprojekt.wsgi:application --bind 0.0.0.0:8000
```

#### **Nginx Konfiguration**

```nginx
server {
  listen 443 ssl http2;
  server_name alex.volkmann.com;

  # SSL Zertifikate
  ssl_certificate /etc/letsencrypt/live/alex.volkmann.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/alex.volkmann.com/privkey.pem;

  # Reverse Proxy zu Django
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }

  # Static Files (nicht proxies, direkt von Disk)
  location /static/ {
    alias /var/www/alex-django/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
  }

  # Media Files
  location /media/ {
    alias /var/www/alex-django/media/;
    expires 7d;
  }
}
```

### 📋 Build-Checkliste

```
Nach JEDEM Frontend-Change:

☐ npm run deploy (in fitness-frontend/)
☐ Neuer Hash aus static/fitness/index.html auslesen
☐ templates/fitness.html Line 16 updaten
☐ Hard Refresh (Ctrl+Shift+R) im Browser
☐ DevTools → Application → Clear Site Data (falls Cache-Problem)
☐ Test auf Mobile (F12 Responsive Mode)
```

---

## 🎓 ZUSAMMENFASSUNG FÜR NEUE ENTWICKLER

**Die App in 30 Sekunden:**

1. **Was:** Calisthenics-Workout-Tracker mit Progressive Overload
2. **Wie:** React Frontend + Django Backend + PostgreSQL
3. **5-Tages-Plan:** Mo-Fr (4 Übungen/Tag), Sa-So Rest
4. **Progression:** 3 Sessions mit target Reps → Upgrade möglich
5. **Offline:** PWA mit Service Worker Caching
6. **API:** REST mit JWT Auth
7. **Tech:** React, Django, Docker, Tailwind, Zustand

**Wichtig zu wissen:**
- Build-Process hat Cache-Probleme → npm run deploy + Hash updaten!
- Stats funktionieren im Hintergrund aber sind nicht sichtbar
- Drop Sets sind noch nicht gut erklärt
- Offline-Modus nutzt IndexedDB für lokale Daten

---

**Weitere Dokumentation:**
- Siehe: `/code/SYSTEM_DOCUMENTATION.md` (diese Datei)
- Code-Comments: Überall in den Komponenten
- Memory: `/home/alex/.claude/projects/.../memory/MEMORY.md`

**Fragen?** Frag Claude oder schau den Code! 🚀
