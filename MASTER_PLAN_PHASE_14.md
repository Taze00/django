# 🎯 MASTER PLAN - Phase 14: Complete Workout System

**Status:** Sauberer Neustart für komplettes System
**Datum:** March 3, 2026
**Ziel:** Alle Komponenten exakt definieren und synchronisieren

---

## 📊 ARCHITEKTUR-ÜBERSICHT

```
┌─────────────────────────────────────────┐
│         REST API (Django)               │
├─────────────────────────────────────────┤
│ POST   /workouts/current/               │ ← Start Workout
│ GET    /workouts/current/               │ ← Get Workout Data
│ POST   /workouts/{id}/add_set/          │ ← Add Set
│ POST   /workouts/{id}/complete/         │ ← Complete Workout
│ GET    /workouts/last_performance/      │ ← Get Last Performance
│ GET    /exercises/                      │ ← Get Exercises + Progressions
└─────────────────────────────────────────┘
                    ↑ HTTP
┌─────────────────────────────────────────┐
│      STATE MANAGEMENT (Zustand)         │
├─────────────────────────────────────────┤
│ workoutStore (Zustand)                  │
│ - currentWorkout                        │
│ - exercises                             │
│ - userProgressions                      │
│ - lastPerformances                      │
│ - currentStep (0-5)                     │
│ - showRestTimer                         │
│ - restTimeRemaining                     │
└─────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────┐
│      UI COMPONENTS (React)              │
├─────────────────────────────────────────┤
│ WorkoutView                             │
│ ├─ ExerciseCard (Set 1+2)               │
│ │  ├─ SetInput (Reps)                   │
│ │  └─ TimerInput (Seconds)              │
│ ├─ RestTimer (3 Min)                    │
│ ├─ DropSetInstructions (Set 3)          │
│ └─ UpgradeModal (After Complete)        │
└─────────────────────────────────────────┘
```

---

## 🔄 WORKOUT FLOW - 6 STEPS

### **Step 0: Warmup Checklist**
```
USER SEES:
┌──────────────────────────┐
│ 🏋️ Warm-up Checklist    │
├──────────────────────────┤
│ ☐ 5 min cardio           │
│ ☐ Arm circles            │
│ ☐ Shoulder rolls         │
└──────────────────────────┘

ACTION: User klickt ✓ Checked
NEXT: Step 1
```

### **Step 1: PUSH SET 1**
```
API CALL (Start):
GET /workouts/current/ → Creates workout if not exists

RESPONSE:
{
  "id": 25,
  "date": "2026-03-03",
  "sets": [],
  "completed": false
}

GET /exercises/ → Gets exercises + progressions
GET /user/progressions/ → Gets user's current levels
GET /workouts/last_performance/ → Gets last reps/seconds

LAST_PERFORMANCE STRUCTURE:
{
  "3": {
    "set1": {"last_reps": 13, "last_seconds": null},
    "set2": {"last_reps": 11, "last_seconds": null}
  },
  "1": {
    "set1": {"last_reps": null, "last_seconds": 42},
    "set2": {"last_reps": null, "last_seconds": 38}
  }
}

UI SHOWS:
┌────────────────────────────┐
│ Push-up - Knee Push-ups    │
│ Level 3 • Set 1            │
├────────────────────────────┤
│ LAST TIME                  │
│ 13 reps                    │
├────────────────────────────┤
│ Enter reps: [14] ± [15]    │
│                            │
│ [✓ Complete Set]           │
└────────────────────────────┘

USER ACTION:
- Macht Set 1
- Gibt 14 reps ein
- Klickt "Complete Set"

BACKEND CALL:
POST /workouts/25/add_set/
{
  "exercise": 1,
  "progression": 3,
  "set_number": 1,
  "is_drop_set": false,
  "reps": 14
}

RESPONSE:
{
  "id": 101,
  "workout": 25,
  "exercise": 1,
  "progression": 3,
  "set_number": 1,
  "is_drop_set": false,
  "reps": 14,
  "seconds": null,
  "created_at": "2026-03-03T18:10:00Z"
}

STORE UPDATE:
- currentWorkout.sets.push(newSet)
- currentStep = 1 ✓

NEXT: Step 2 (Pull Set 1)
```

### **Step 2: PULL SET 1**
```
Same pattern as Step 1 but:
- Exercise: Pull-up (ID 2)
- Progression: Dead Hang (ID 8) or higher
- Set Number: 1
- Input: TimerInput (SECONDS, not reps!)

PULL SET 1 DISPLAY:
┌────────────────────────────┐
│ Pull-up - Dead Hang        │
│ Level 1 • Set 1            │
├────────────────────────────┤
│ LAST TIME                  │
│ 42 seconds                 │
├────────────────────────────┤
│ [Start Timer]              │
│ [3-2-1...] → [Timer: 45s]  │
│ [Stop & Save]              │
│ [✏️ Edit Time]              │
└────────────────────────────┘

After "Stop & Save":
POST /workouts/25/add_set/
{
  "exercise": 2,
  "progression": 8,
  "set_number": 1,
  "is_drop_set": false,
  "seconds": 45
}

NEXT: Step 3 (Rest Timer 3 Min)
```

### **Step 3: REST TIMER 3 MIN**
```
DISPLAY:
┌────────────────────────────┐
│ Rest Time                  │
│                            │
│ 3:00 ⏱️                     │
│                            │
│ [Skip]                     │
└────────────────────────────┘

LOGIC:
- Timer countdown: 3:00 → 2:59 → ... → 0:00
- User kann mit "Skip" vorspulen
- Nach 0:00 AUTOMATISCH → Step 4

STATE:
- showRestTimer = true
- restTimeRemaining = 180 (seconds)
- Effect: every 1 sec decrement

NEXT: Step 4 (Push Set 2)
```

### **Step 4: PUSH SET 2**
```
Same as Step 1 but:
- Set Number: 2
- LAST_PERFORMANCE uses set2: {last_reps: 11}

After Complete:
- currentStep = 4
- NEXT: Step 5 (Pull Set 2)
```

### **Step 5: PULL SET 2**
```
Same as Step 2 but:
- Set Number: 2
- LAST_PERFORMANCE uses set2: {last_seconds: 38}

After Complete:
- currentStep = 5
- NEXT: Step 6 (Push Set 3 DROP-SET)
```

### **Step 6: PUSH SET 3 DROP-SET (REST TIMER 5 MIN FIRST!)**
```
FIRST: REST TIMER 5 MIN (Longer!)

DISPLAY:
┌────────────────────────────┐
│ Rest Time (Extended)       │
│                            │
│ 5:00 ⏱️                     │
│                            │
│ [Skip]                     │
└────────────────────────────┘

LOGIC: Same as Step 3 but 300 seconds (5 min)

After Timer expires → Step 6.1 (Drop-Set Instructions)
```

### **Step 6.1: DROP-SET INSTRUCTIONS (Set 3)**
```
LOGIC: Check if progression.level > 1

IF level > 1:
  DISPLAY DROP-SET ANLEITUNG ✓

  ┌────────────────────────────┐
  │ 🔥 SET 3: DROP-SET          │
  ├────────────────────────────┤
  │ ⚠️ NO REST BETWEEN DROPS!   │
  │                            │
  │ 1. START: Knee Push-ups    │
  │    Go until failure!       │
  │                            │
  │ 2. DROP: Incline Push-ups  │
  │    Immediately! Go again!  │
  │                            │
  │ 3. DROP: Wall Push-ups     │
  │    Complete exhaustion!    │
  │                            │
  │ [✓ Drop-Set Complete]      │
  └────────────────────────────┘

  ACTION: User macht alle Drops non-stop
          Klickt "Complete"

  BACKEND CALL:
  POST /workouts/25/add_set/
  {
    "exercise": 1,
    "progression": 3,
    "set_number": 3,
    "is_drop_set": true,
    "reps": null,        ← KEIN REPS EINGEBEN!
    "seconds": null
  }

ELSE (level = 1, no drops possible):
  DISPLAY SIMPLE VERSION:

  ┌────────────────────────────┐
  │ SET 3: Wall Push-ups       │
  │                            │
  │ Go until failure!          │
  │                            │
  │ [✓ Complete]               │
  └────────────────────────────┘

NEXT: Step 7 (Pull Set 3)
```

### **Step 7: PULL SET 3 DROP-SET (REST TIMER 5 MIN FIRST!)**
```
SAME PATTERN AS STEP 6 aber für Pull-ups

ABER: Nach "Complete" → NO REST TIMER!
(ist letzter Set)

NEXT: Step 8 (Workout Complete)
```

### **Step 8: WORKOUT COMPLETE**
```
BACKEND CALL:
POST /workouts/25/complete/

LOGIC (Backend):
1. Mark workout.completed = true
2. Check upgrades/downgrades for each exercise
3. Return upgrades + downgrades

RESPONSE:
{
  "workout": 25,
  "completed": true,
  "upgrades": [
    {
      "exercise": "Push-up",
      "old_level": 3,
      "new_level": 4,
      "progression_name": "Standard Push-ups"
    }
  ],
  "downgrades": []
}

UI SHOWS:
IF upgrades:
  ┌────────────────────────────┐
  │ 🎉 UPGRADE!                 │
  ├────────────────────────────┤
  │ Push-up                    │
  │ Level 3 → Level 4          │
  │ Standard Push-ups!         │
  │                            │
  │ [✓ Continue]               │
  └────────────────────────────┘

ELSE IF downgrades:
  ┌────────────────────────────┐
  │ 💪 Keep Building Strength! │
  ├────────────────────────────┤
  │ You downgraded             │
  │ Pull-up: L2 → L1           │
  │ Back to basics!            │
  │                            │
  │ [✓ Continue]               │
  └────────────────────────────┘

ELSE:
  ┌────────────────────────────┐
  │ ✅ WORKOUT COMPLETE!        │
  ├────────────────────────────┤
  │ Great work today!          │
  │                            │
  │ [Back to Home]             │
  └────────────────────────────┘

NEXT: Home Page
```

---

## ⏱️ REST TIMER ZEITEN - EXACT

```
Step 1 (Push Set 1) → Step 2 (Pull Set 1):
  [3 MIN REST] ⏱️

Step 2 (Pull Set 1) → Step 3 (Push Set 2):
  [3 MIN REST] ⏱️

Step 3 (Push Set 2) → Step 4 (Pull Set 2):
  [3 MIN REST] ⏱️

Step 4 (Pull Set 2) → Step 5 (Push Set 3):
  [5 MIN REST] ⏱️⏱️⏱️ ← LÄNGER!
  (Before Drop-Set Instructions)

Step 5 (Push Set 3) → Step 6 (Pull Set 3):
  [5 MIN REST] ⏱️⏱️⏱️ ← LÄNGER!
  (Before Drop-Set Instructions)

Step 6 (Pull Set 3) → COMPLETE:
  [NO REST!] ✓
  (is letzter Set)
```

---

## 🔐 DROP-SET ERKENNUNG

```javascript
// Backend (views.py)
function should_show_drop_set_instructions(progression_level) {
  return progression_level > 1;
}

// Frontend (ExerciseCard.jsx)
if (setNumber === 3 && progression.level > 1) {
  return <DropSetInstructions />;
}

if (setNumber === 3 && progression.level === 1) {
  return <SimpleSetComplete />;
}
```

---

## 📝 LAST_PERFORMANCE FORMAT (EXAKT)

```json
{
  "progression_id_1": {
    "set1": {
      "last_reps": 8,
      "last_seconds": null
    },
    "set2": {
      "last_reps": 7,
      "last_seconds": null
    }
  },
  "progression_id_2": {
    "set1": {
      "last_reps": null,
      "last_seconds": 45
    },
    "set2": {
      "last_reps": null,
      "last_seconds": 40
    }
  }
}
```

---

## 🎮 KOMPONENTEN-STRUKTUR

### **WorkoutView.jsx**
```javascript
State:
- currentStep (0-7)
- showRestTimer (boolean)
- restTimeRemaining (seconds)
- restTimerDuration (180 or 300)
- isWorkoutActive (boolean, for tab warning)

Methods:
- getTodaysExercises() → [Push, Pull]
- getExerciseForStep(step) → Exercise
- handleSetCompleted() → nextStep
- handleRestTimerComplete() → nextStep
- handleCompleteWorkout() → POST /complete/

Flow:
Step 0 → Warmup
Step 1 → Push Set 1 → RestTimer(180) → Step 2
Step 2 → Pull Set 1 → RestTimer(180) → Step 3
Step 3 → Push Set 2 → RestTimer(180) → Step 4
Step 4 → Pull Set 2 → RestTimer(300) → Step 5
Step 5 → Push Set 3 → DropSet → RestTimer(300) → Step 6
Step 6 → Pull Set 3 → DropSet → Step 7 (COMPLETE!)
```

### **ExerciseCard.jsx**
```javascript
Props:
- exercise (Exercise object)
- setNumber (1, 2, or 3)
- progression (Progression object)
- onSetCompleted (function)

Logic:
if (setNumber <= 2):
  Show SetInput OR TimerInput

if (setNumber === 3):
  if (progression.level > 1):
    Show DropSetInstructions
  else:
    Show SimpleSetComplete
```

### **SetInput.jsx**
```javascript
Props:
- exercise
- setNumber (1 or 2)
- progression
- onCompleted

Display:
- LAST TIME: {lastPerformances[progressionId]['set' + setNumber].last_reps} reps
- Input: Reps counter
- Button: "Complete Set"

Logic:
const lastPerf = lastPerformances[progressionId][`set${setNumber}`];
const lastReps = lastPerf?.last_reps;
```

### **TimerInput.jsx**
```javascript
Props:
- exercise
- setNumber (1 or 2)
- progression
- onCompleted

Display:
- LAST TIME: {lastPerformances[progressionId]['set' + setNumber].last_seconds} seconds
- Timer: [Start] → [3-2-1] → [Running timer] → [Stop & Save]
- Edit: Can edit seconds after stopping

Logic:
const lastPerf = lastPerformances[progressionId][`set${setNumber}`];
const lastSeconds = lastPerf?.last_seconds;
```

### **RestTimer.jsx**
```javascript
Props:
- duration (180 or 300 seconds)
- onComplete (function)

Display:
- Countdown: 3:00 → 0:00
- Skip button

Logic:
useEffect: every 1 sec, decrement timeRemaining
When timeRemaining === 0, call onComplete()
```

### **DropSetInstructions.jsx**
```javascript
Props:
- exercise
- currentProgression
- onComplete

Logic:
availableDrops = exercise.progressions
  .filter(p => p.level < currentProgression.level)
  .sort((a,b) => b.level - a.level)
  .slice(0, 2) // nur erste 2 Drops zeigen

Display:
1. START: {currentProgression.name}
2. DROP 1: {availableDrops[0].name} (if exists)
3. DROP 2: {availableDrops[1].name} (if exists)

Button: "Drop-Set Complete"
Action: POST add_set with is_drop_set=true, reps=null
```

---

## 🔌 API ENDPOINTS (EXAKT)

### **1. GET /workouts/current/**
```
Response:
{
  "id": 25,
  "date": "2026-03-03",
  "sets": [],
  "completed": false
}
```

### **2. POST /workouts/{id}/add_set/**
```
Request:
{
  "exercise": 1,
  "progression": 3,
  "set_number": 1,
  "is_drop_set": false,
  "reps": 14          (optional)
  "seconds": null     (optional)
}

Response:
{
  "id": 101,
  "workout": 25,
  "exercise": 1,
  "progression": 3,
  "set_number": 1,
  "is_drop_set": false,
  "reps": 14,
  "seconds": null,
  "created_at": "2026-03-03T18:10:00Z"
}
```

### **3. GET /workouts/last_performance/**
```
Response:
{
  "3": {
    "set1": {"last_reps": 13, "last_seconds": null},
    "set2": {"last_reps": 11, "last_seconds": null}
  },
  "1": {
    "set1": {"last_reps": null, "last_seconds": 42},
    "set2": {"last_reps": null, "last_seconds": 38}
  }
}
```

### **4. POST /workouts/{id}/complete/**
```
Response:
{
  "workout": 25,
  "completed": true,
  "upgrades": [
    {
      "exercise": "Push-up",
      "old_level": 3,
      "new_level": 4,
      "progression_name": "Standard Push-ups"
    }
  ],
  "downgrades": []
}
```

---

## ✅ IMPLEMENTATION CHECKLIST

- [ ] Backend: API Endpoints exakt wie definiert
- [ ] Backend: last_performance() with per-set structure
- [ ] Frontend: WorkoutView 8-Step Flow
- [ ] Frontend: Rest Timer (3 & 5 min)
- [ ] Frontend: DropSetInstructions Component
- [ ] Frontend: SetInput per-set last performance
- [ ] Frontend: TimerInput per-set last performance
- [ ] Frontend: No Sessions Counter on Home
- [ ] Frontend: Tab-Switch Warning (isWorkoutActive)
- [ ] Testing: Complete full workout flow
- [ ] Testing: Upgrades work correctly
- [ ] Testing: Drop-sets show for level > 1
- [ ] Build & Deploy

---

**Status:** ✅ PLAN COMPLETE
**Ready for:** Implementation
