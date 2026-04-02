# 🏋️ FITNESS APP - COMPLETE SPECIFICATION

**Version:** 1.1 (Updated Apr 2, 2026)
**Status:** MVP Complete & Tested
**Location:** `/code/`

---

# 📖 TABLE OF CONTENTS

1. [Core Concept](#core-concept)
2. [Exercises & Progressions](#exercises--progressions)
3. [Workout Structure](#workout-structure)
4. [Progression Logic (Upgrade/Downgrade)](#progression-logic)
5. [UI/UX Specifications](#uiux-specifications)
6. [User Flows](#user-flows)
7. [API Endpoints](#api-endpoints)
8. [Database Models](#database-models)
9. [Frontend Architecture](#frontend-architecture)

---

# 1. CORE CONCEPT

## Philosophy: "Minimal & Effective"

The fitness app is designed around **maximum effectiveness with minimum complexity**.

### Core Principles
- **3 Main Exercises:** Push-ups (Push) + Pull-ups (Pull) + Planks (Core)
- **Frequency:** 5 times per week (Monday - Friday)
- **Same routine every day:** Push → Pull → Plank sequence
- **Duration:** ~30 minutes per workout
- **Progressive difficulty:** 7 progression levels per exercise
- **Adaptive difficulty:** Auto-downgrade if form breaks (first session only)

---

# 2. EXERCISES & PROGRESSIONS

## Exercise #1: PUSH-UPS 🚀

**Category:** PUSH (chest, triceps, shoulders)

| Level | Name | Type | Target | User Starts Here |
|-------|------|------|--------|------------------|
| 1 | Wall Push-ups | Reps | 8 | ❌ |
| 2 | Incline Push-ups | Reps | 8 | ❌ |
| **3** | **Knee Push-ups** | **Reps** | **8** | **✅ START** |
| 4 | Standard Push-ups | Reps | 8 | ❌ |
| 5 | Diamond Push-ups | Reps | 6 | ❌ |
| 6 | Decline Push-ups | Reps | 6 | ❌ |
| 7 | Pseudo Planche Push-ups | Reps | 5 | ❌ |

---

## Exercise #2: PULL-UPS 🔥

**Category:** PULL (back, biceps, lats)

| Level | Name | Type | Target | User Starts Here |
|-------|------|------|--------|------------------|
| **1** | **Dead Hang** | **Time** | **30s** | **✅ START** |
| 2 | Scapular Shrugs | Reps | 10 | ❌ |
| 3 | Active Hang | Time | 20s | ❌ |
| 4 | Pull-up Negatives | Reps | 5 | ❌ |
| 5 | Band-Assisted Pull-ups | Reps | 8 | ❌ |
| 6 | Standard Pull-ups | Reps | 5 | ❌ |
| 7 | Chest-to-Bar | Reps | 5 | ❌ |

---

## Exercise #3: PLANKS 💪

**Category:** CORE (stabilizers, core strength)

| Level | Name | Type | Target | User Starts Here |
|-------|------|------|--------|------------------|
| **1** | **Knee Plank** | **Time** | **30s** | **✅ START** |
| 2 | Incline Plank | Time | 45s | ❌ |
| 3 | Standard Plank | Time | 60s | ❌ |
| 4 | Feet-Elevated Plank | Time | 60s | ❌ |
| 5 | Extended Plank | Time | 45s | ❌ |
| 6 | RKC Plank | Time | 30s | ❌ |
| 7 | One-Arm Plank | Time | 20s | ❌ |

---

# 3. WORKOUT STRUCTURE

## Workout Schedule

- **Frequency:** Monday - Friday (5 days/week)
- **Rest Days:** Saturday, Sunday
- **Same routine every day**
- **Duration:** ~30 minutes

## Complete Workout Flow (UPDATED Apr 2)

```
WARM-UP (5 min)
├─ Wrist circles
├─ Shoulder circles
├─ Elbow circles
├─ Back stretches
└─ Leg stretches

WORKOUT (25 min)

Step 1: PUSH-UPS Set 1
├─ RIR 1-2 (1-2 reps in reserve)
└─ Rest 3 min (180s)

Step 2: PULL-UPS Set 1
├─ Reps or Time (depends on level)
└─ Rest 3 min (180s)

Step 3: PUSH-UPS Set 2
├─ Same performance as Set 1
└─ Rest 3 min (180s)

Step 4: PULL-UPS Set 2
├─ Same performance as Set 1
└─ Rest 3 min (180s)

Step 5: PUSH-UPS Set 3 (DROP-SET)
├─ Go to FAILURE
├─ Drop to easier progression (NO REST!)
└─ Rest 5 min (300s)

Step 6: PULL-UPS Set 3 (DROP-SET)
├─ Go to FAILURE
├─ Drop to easier progression (NO REST!)
└─ Rest 5 min (300s)

Step 7: PLANKS Set 1
├─ Time-based (e.g., 30 seconds)
└─ Rest 3 min (180s)

Step 8: PLANKS Set 2
├─ Same performance as Set 1
└─ Rest 3 min (180s)

Step 9: PLANKS Set 3 (DROP-SET)
├─ Go to FAILURE
├─ Drop to easier progression (NO REST!)
└─ DONE! ✅
```

## Rest Times (FINAL)

| Situation | Duration |
|-----------|----------|
| After Sets 1+2 (all exercises) | 180 seconds (3 min) |
| After Set 3 (drop-set) | 300 seconds (5 min) |

---

# 4. PROGRESSION LOGIC

## 4A. UPGRADE LOGIC (Level Up! 🎉)

### Condition for Upgrade

**User upgrades when:**
```
Set 1 >= Target AND Set 2 >= Target
IN 3 CONSECUTIVE WORKOUTS
```

### What Happens on Upgrade

1. User sees "🎉 LEVEL UP!" modal
2. New level updates (e.g., Knee Push-ups → Standard Push-ups)
3. sessions_at_target resets to 0
4. is_first_session set to True (allows downgrade if needed)

### Important: Set 3 Does NOT Count!

❌ Drop-set performance is ignored for progression

---

## 4B. DOWNGRADE LOGIC (Keep Building Strength 💪)

### Condition for Downgrade

**Downgrade happens ONLY on FIRST workout at new level:**

```
IF (Set 1 < 3 reps) OR (Set 1 + Set 2 < 5 total)
THEN DOWNGRADE
```

### Prevents Downgrade Loop

- After downgrade: `is_first_session = False`
- Prevents infinite downgrade loops
- Next upgrade can happen normally

---

## 4C. Drop-Set Rules (Set 3)

### What Gets Saved

```
✅ SAVED:
  - is_drop_set: True
  - drop_set_completed: True

❌ NOT SAVED:
  - Individual drop reps
  - Drop count
```

---

# 5. UI/UX SPECIFICATIONS

## Design System

### Colors (Dark Mode)
```
Background:    #0f172a (slate-900)
Text:          #f1f5f9 (slate-100)
Accent (UI):   #3b82f6 (blue-500)
Action (Btn):  #10b981 (emerald-500)
```

### Key UI Rules

1. **TARGETS ARE HIDDEN** — Only "Last time: X" shown
2. **Minimal UI** — Exercise, progression, counter only
3. **One Action Per Screen** — Start, Complete, Skip
4. **No Progress Bars** — Surprise level-up modals instead

---

# 6. USER FLOWS

## Complete Workout Flow

```
1. User starts workout
2. Warm-up checklist (5 items)
3. Step 1: Push-ups Set 1 → Rest 180s
4. Step 2: Pull-ups Set 1 → Rest 180s
5. Step 3: Push-ups Set 2 → Rest 180s
6. Step 4: Pull-ups Set 2 → Rest 180s
7. Step 5: Push-ups Set 3 (DROP-SET) → Rest 300s
8. Step 6: Pull-ups Set 3 (DROP-SET) → Rest 300s
9. Step 7: Planks Set 1 → Rest 180s
10. Step 8: Planks Set 2 → Rest 180s
11. Step 9: Planks Set 3 (DROP-SET) → DONE!
12. Check for upgrade/downgrade
13. Show modal if applicable
14. Dashboard refreshes
```

---

# 7. API ENDPOINTS

## Base URL
```
/api/fitness/
```

## Key Endpoints
```
GET /exercises/
  Returns: List of all exercises with progressions

GET /user-progressions/
  Returns: User's current level for each exercise

GET /workouts/current/
  Returns: Today's workout (or creates new)

POST /workouts/{workout_id}/add_set/
  Creates: New workout set with reps/time

POST /workouts/{workout_id}/complete/
  Marks: Workout as completed, returns upgrade/downgrade data
```

---

# 8. DATABASE MODELS

## Key Models
```
Exercise: name, category (PUSH/PULL/CORE), order
Progression: exercise, level (1-7), target_type, target_value
UserExerciseProgression: user, exercise, current_progression, sessions_at_target
Workout: user, date, completed, completed_at, duration_seconds
WorkoutSet: workout, exercise, progression, set_number, reps, seconds, is_drop_set, rest_time_seconds
```

---

# 9. FRONTEND ARCHITECTURE

## Components
- **SetInput:** Reps input (0-99) with +/- buttons
- **TimerInput:** Auto-tracked seconds with start/pause/reset
- **RestTimer:** Circular progress, auto-complete at 0
- **DropSetInstructions:** Progression sequence modal
- **ProgressionModal:** Level-up or level-down notifications

## Views
- **HomeView:** Dashboard with week plan & current levels
- **WorkoutView:** 9-step workout flow
- **ExercisesView:** Progression ladder per exercise
- **StatisticsView:** Workout history & streaks

---

# RECENT CHANGES (Apr 2, 2026)

✅ **Change 1: Increase rest time**
- Normal sets (1+2): 120s → 180s (3 minutes)
- Drop-set rest: 300s (unchanged)

✅ **Change 2: Reorder workout structure**
- Old: Push → Plank → Pull → repeat (alternating)
- New: Push → Pull → repeat, then Plank at end
- Benefit: Build strength on main lifts first, finish with core work

---

# END OF SPECIFICATION

**Everything is implemented and tested.** ✅
