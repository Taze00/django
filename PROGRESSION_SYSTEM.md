# Progression System - Fitness Tracker

## ⚠️ WICHTIG: Nur Set 1 und Set 2 zählen für Upgrade/Downgrade!

**Drop-Sets sind TEIL des Trainings und absolut WICHTIG!**

Ein Trainingstag hat:
- **Set 1** ✅ zählt für Upgrade/Downgrade
- **Set 2** ✅ zählt für Upgrade/Downgrade
- **Drop-Set** ✅ Teil des Trainings! (für Extra-Volumen und Muskelaufbau)

**Es gibt KEIN Set 3! Nach Set 2 kommt sofort das Drop-Set!**

---

## 🎯 UPGRADE - Level erhöhen

### Bedingung

Du brauchst **3 erfolgreiche Trainingstage** (Sessions).

**Erfolgreich = Set 1 UND Set 2 erreichen beide das Target**

### Beispiel Push-ups (Target = 8 Reps)

| Trainingstag | Set 1 | Set 2 | Drop-Set | Zählt für Upgrade? | Grund |
|---|---|---|---|---|---|
| 1 | 8 Reps | 8 Reps | 5 Reps | ✅ Ja | Beide ≥ 8 |
| 2 | 8 Reps | 7 Reps | 8 Reps | ❌ Nein | Set 2 nur 7 |
| 3 | 9 Reps | 8 Reps | 10 Reps | ✅ Ja | Beide ≥ 8 |
| 4 | 8 Reps | 8 Reps | 6 Reps | ✅ Ja | Beide ≥ 8 |

Nach Tag 4 hast du 3 erfolgreiche Sessions → **UPGRADE zu Level 2!**

**Achtung:** Die Drop-Set Reps spielen KEINE Rolle für Upgrade. Nur Set 1 und Set 2 zählen!

### Upgrade Prozess

Wenn die Bedingung erfüllt ist:
1. ✅ **Progression wird erhöht** zum nächsten Level
2. ✅ **Zähler wird zurückgesetzt** auf 0/3 Sessions
3. ✅ **`is_first_session` Flag wird gesetzt** → Downgrade möglich in nächster Session
4. ✅ **`custom_target` wird gelöscht** → zurück zu Basis-Target

> **Beispiel:** Du hast Push-up Level 1 (Wall Push-ups) 3x trainiert und in einer Session beide Sets mit 8+ Reps geschafft → UPGRADE zu Level 2 (Incline Push-ups)

---

## ⬇️ Downgrade (Absteigen bei zu frühem Upgrade)

### Bedingung für Downgrade

Ein Downgrade passiert **nur in der ersten Session nach einem Upgrade**, wenn du nicht genug Reps/Zeit schaffst:

#### Reps-basierte Übungen:
- **Set 1 < 3 Reps** → Downgrade
- **Set 1 + Set 2 < 5 Reps insgesamt** → Downgrade

#### Zeit-basierte Übungen:
- **Set 1 < Target/3** → Downgrade
- **Set 1 + Set 2 < Target/2** → Downgrade

### Downgrade Prozess

Wenn die Bedingung erfüllt ist:
1. ⬇️ **Progression wird zurückgesetzt** zur vorherigen Stufe
2. ⬇️ **`custom_target` wird erhöht** (siehe unten)
3. ⬇️ **`is_first_session` wird zurückgesetzt** auf False
4. ⬇️ **Sessions-Zähler wird zurückgesetzt** auf 0/3

### Custom Target Anpassung (Penalty System)

Jedes Mal wenn du herabgestufst wirst, wird das Upgrade-Target erhöht (Penalty):

| Set 1 Reps/Zeit | Penalty | Neuer Custom Target |
|---|---|---|
| 0 Reps/Zeit | +6 | target_value + 6 |
| 1 Rep/Zeit | +4 | target_value + 4 |
| 2 Reps/Zeit | +2 | target_value + 2 |
| ≥ 3 Reps/Zeit | Kein Downgrade | — |

**Maximum:** custom_target ist auf 20 begrenzt (Höchststrafe)

> **Beispiel:** Du hast Push-up Level 2 mit nur 2 Reps in Set 1 geschafft → Downgrade zu Level 1, custom_target wird von 8 auf 10 erhöht. Nächster Upgrade braucht jetzt 10 statt 8 Reps!

---

## 📊 Beispiel: Push-ups Progression

### Level 1: Wall Push-ups
- **Zielwert:** 8 Reps
- **Upgrade:** 3 Sessions mit je 8+ Reps in Set 1 + Set 2
- **Downgrade:** < 3 Reps in Set 1 in der nächsten Session

### Level 2: Incline Push-ups
- **Zielwert:** 8 Reps
- **Upgrade:** 3 Sessions mit je 8+ Reps
- **Downgrade:** < 3 Reps in Set 1
  - Wenn 0 Reps → custom_target = 8 + 6 = **14 Reps für Upgrade**
  - Wenn 1 Rep → custom_target = 8 + 4 = **12 Reps für Upgrade**
  - Wenn 2 Reps → custom_target = 8 + 2 = **10 Reps für Upgrade**

### Level 3: Knee Push-ups
- **Zielwert:** 8 Reps
- **Upgrade:** 3 Sessions mit je 8+ Reps (oder custom_target wenn erhöht)
- **Downgrade:** Gleicher Mechanismus

Und so weiter für alle 7 Level...

---

## ⏱️ Beispiel: Pull-ups (Zeit-basiert)

### Level 1: Dead Hang
- **Zielwert:** 30 Sekunden
- **Upgrade:** 3 Sessions mit je 30+ Sekunden in Set 1 + Set 2
- **Downgrade:** < 10 Sekunden in Set 1 (30/3) in nächster Session

### Level 2: Scapular Pulls
- **Zielwert:** 30 Sekunden
- **Upgrade:** 3 Sessions mit je 30+ Sekunden
- **Downgrade:** < 10 Sekunden
  - Wenn 0 Sekunden → custom_target = 30 + 6 = **36 Sekunden für Upgrade**
  - Wenn 5 Sekunden → custom_target = 30 + 4 = **34 Sekunden für Upgrade**

---

## 🔄 Session Counter Logic

Der Counter zeigt: `X/3 Sessions` auf der Home-Seite

- **0/3:** Gerade upgraded oder herabgestuft
- **1/3:** 1 erfolgreiche Session auf diesem Level
- **2/3:** 2 erfolgreiche Sessions
- **3/3:** Ready für Upgrade! → Nächste Session triggert automatisch Upgrade

**Wichtig:** Der Counter zählt nur Sessions, wo BEIDE Sets 1 & 2 das Ziel erreicht haben!

---

## ⚠️ Edge Cases

### Struktur eines Trainings
Pro Übung machst du:
1. **Set 1** (regulär, zählt für Upgrade/Downgrade) ✅
2. **Set 2** (regulär, zählt für Upgrade/Downgrade) ✅
3. **Drop-Set** (nach Set 2, zählt NICHT für Upgrade, aber sehr wichtig!) 🎯

**Es gibt KEIN Set 3!**

### Was ist eine "erfolgreiche" Session?
- Du machst das komplette Workout mit beiden Sets für beide Übungen
- Drop-Sets sind obligatorisch (nach Set 2)
- Aber Drop-Set Reps beeinflussen Upgrade/Downgrade NICHT

### Drop-Sets - Warum sind sie so wichtig?
- **Nach Set 2** führst du sofort einen Drop-Set durch
- **Zweck:** Extra-Volumen, Muskelermüdung, Hypertrophie
- **Effekt auf Upgrade:** KEINE - werden ignoriert
- **Effekt auf Training:** SEHR wichtig für Muskelaufbau!

### Wenn du die Progression manuell änderst (via Exercises-Seite)
- Der `is_first_session` Flag wird NICHT automatisch gesetzt
- Das ist **nicht sicher** für Downgrades
- Besser: nur über regelmäßiges Training upgraden

---

## 📈 Visuelle Übersicht

```
START: Level 1 Push-ups (Target: 8 Reps)
Counter: 0/3

├─ TAG 1: Set 1=8, Set 2=8, Drop-Set=5 → ✅ Erfolg! (1/3)
│         (Drop-Set ignoriert)
│
├─ TAG 2: Set 1=8, Set 2=7, Drop-Set=9 → ❌ Fail! (Set 2 < 8)
│         Counter bleibt 1/3
│
├─ TAG 3: Set 1=9, Set 2=8, Drop-Set=6 → ✅ Erfolg! (2/3)
│         (Drop-Set ignoriert)
│
├─ TAG 4: Set 1=8, Set 2=8, Drop-Set=7 → ✅ Erfolg! (3/3)
│         (Drop-Set ignoriert)
│
└─ TAG 5: UPGRADE WIRD AUTOMATISCH AUSGELÖST!
   └─ Upgrade zu Level 2 ✅
   └─ is_first_session = True (Downgrade möglich!)
   └─ Counter: 0/3 reset
   └─ custom_target: 8 (normal)

   └─ Set 1=2, Set 2=5, Drop-Set=10 → DOWNGRADE! ⬇️
      (Drop-Set spielte keine Rolle)
      └─ Zurück zu Level 1
      └─ custom_target: 8 + 2 = 10 (Penalty!)
      └─ is_first_session = False
      └─ Counter: 0/3 reset

TAG 6: Jetzt brauchst du 10 Reps (nicht 8) für Upgrade!
└─ Set 1=10, Set 2=10, Drop-Set=8 → ✅ Erfolg! (1/3)
```

---

## 🎮 User Experience

### Home Dashboard
- Zeigt: "X/3 Sessions" - wie viele Sessions du noch brauchst
- Zeigt: "Current Level: XX" mit Upgrade-Progress
- KEIN "Target: 8" sichtbar (Überraschungs-Upgrades)

### Nach Upgrade
- 🎉 Modal erscheint: "Congratulations! Level upgraded to XX"
- `is_first_session = True` → Downgrade ist möglich
- Nächste Session wird engmaschig überwacht

### Nach Downgrade
- 💪 Modal erscheint: "Keep Building Strength! Let's get stronger first"
- custom_target erhöht sich
- Du hast Zeit zu trainieren mit erhöhtem Ziel

---

## 🔧 Backend Implementation

**Datei:** `fitness/views.py` → `complete()` Action

```python
# Simplified Logic:
IF is_first_session AND performance_too_low:
    downgrade_progression(user, exercise)
    adjust_custom_target(reps_achieved)
    is_first_session = False

IF upgrade_available:
    upgrade_progression(user, exercise)
    is_first_session = True
    custom_target = None (reset to default)
```

---

## 📝 Zusammenfassung

| Aspekt | Wert |
|--------|------|
| **Sessions für Upgrade** | 3 erfolgreiche Sessions |
| **Success Criteria** | Both Set 1 & Set 2 ≥ Target |
| **Downgrade Fenster** | Nur erste Session nach Upgrade |
| **Reps Downgrade Threshold** | < 3 Reps in Set 1 |
| **Zeit Downgrade Threshold** | < Target/3 Sekunden in Set 1 |
| **Max Custom Target Penalty** | +6 Reps/Sekunden |
| **Custom Target Cap** | +20 (absolute max) |

---

**Letzte Aktualisierung:** 2026-03-03
**Status:** ✅ Live und funktional
