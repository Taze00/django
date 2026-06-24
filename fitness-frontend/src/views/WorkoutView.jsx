import { useState, useEffect, useMemo } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import { useNavigate } from 'react-router-dom';
import SetInput from '../components/SetInput';
import TimerInput from '../components/TimerInput';
import RestTimer from '../components/RestTimer';
import DropSetInstructions from '../components/DropSetInstructions';
import WarmupChecklist from '../components/WarmupChecklist';
import CooldownChecklist from '../components/CooldownChecklist';
import ProgressionModal from '../components/ProgressionModal';
import FormTip from '../components/FormTip';
import { requestWakeLock, releaseWakeLock } from '../utils/wakeLock';

const REST_TIMES = { normal: 180, afterDrop: 300 };

function buildWorkoutSteps(exercises) {
  const steps = [];
  const main = exercises.filter(e => e.category !== 'CORE');
  const core = exercises.filter(e => e.category === 'CORE');
  // 2 normal sets interleaved across main exercises
  for (let s = 1; s <= 2; s++) {
    for (const ex of main) {
      steps.push({ exerciseName: ex.name, setNumber: s, type: 'set' });
    }
  }
  // Drop sets for main
  for (const ex of main) {
    steps.push({ exerciseName: ex.name, setNumber: 3, type: 'drop' });
  }
  // Core: 2 sets + drop
  for (const ex of core) {
    steps.push({ exerciseName: ex.name, setNumber: 1, type: 'set' });
    steps.push({ exerciseName: ex.name, setNumber: 2, type: 'set' });
    steps.push({ exerciseName: ex.name, setNumber: 3, type: 'drop' });
  }
  return steps;
}

export default function WorkoutView() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isResting, setIsResting] = useState(false);
  const [currentWorkout, setCurrentWorkout] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [progressionData, setProgressionData] = useState(null);
  const [isWarmupComplete, setIsWarmupComplete] = useState(false);
  const [showCooldown, setShowCooldown] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const isInitialized = useWorkoutStore(state => state.isInitialized);
  const lastPerformance = useWorkoutStore(state => state.lastPerformance);
  const workouts = useWorkoutStore(state => state.workouts);
  const streak = useWorkoutStore(state => state.streak);
  const trainingDays = useWorkoutStore(state => state.trainingDays);
  const getCurrentWorkout = useWorkoutStore(state => state.getCurrentWorkout);
  const addSet = useWorkoutStore(state => state.addSet);
  const completeWorkout = useWorkoutStore(state => state.completeWorkout);
  const getLastPerformance = useWorkoutStore(state => state.getLastPerformance);

  const WORKOUT_STEPS = useMemo(() => buildWorkoutSteps(exercises), [exercises]);

  // Wake Lock für die gesamte Workout-Session: anfordern beim Betreten der View,
  // freigeben beim Verlassen (egal ob Abschluss, Abbruch oder Navigation).
  // visibilitychange: nach Hintergrund re-akquirieren, weil der Browser den Lock
  // beim Tab-Wechsel automatisch aufhebt.
  useEffect(() => {
    requestWakeLock();
    const onVisibility = () => { if (!document.hidden) requestWakeLock(); };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      releaseWakeLock();
    };
  }, []);

  useEffect(() => {
    if (isInitialized && exercises.length > 0) initializeWorkout();
  }, [isInitialized, exercises.length]);

  const initializeWorkout = async () => {
    try {
      const workout = await getCurrentWorkout();
      setCurrentWorkout(workout);
      try { await getLastPerformance(); } catch {}
    } catch {}
    setIsLoading(false);
  };

  const getProgInfo = exerciseName => {
    const exercise = exercises.find(e => e.name === exerciseName);
    if (!exercise) return null;
    const userProg = userProgressions[String(exercise.id)];
    if (!userProg?.current_progression) return null;
    return {
      exercise,
      currentProgression: userProg.current_progression,
      lowerProgressions: exercise.progressions
        .filter(p => p.level < userProg.current_progression.level)
        .reverse(),
    };
  };

  const getLastTime = (exerciseName, setNumber) =>
    lastPerformance?.[exerciseName]?.[`set${setNumber}`] ?? null;

  const getNextLabel = nextStep => {
    if (!nextStep) return 'Fertig!';
    if (nextStep.type === 'drop') return `${nextStep.exerciseName} Drop-Set`;
    return getProgInfo(nextStep.exerciseName)?.currentProgression?.name || nextStep.exerciseName;
  };

  const handleSetComplete = async (value = null) => {
    setIsLoading(true);
    try {
      const step = WORKOUT_STEPS[currentStep];
      const isDropSet = step.type === 'drop';
      const progInfo = getProgInfo(step.exerciseName);
      if (!progInfo) { setIsLoading(false); return; }

      // For drop-sets, `value` is the reached progression id (or false = skip).
      // We store that reached variant as the drop-set's progression so history
      // shows how far down the user had to go. This is a progress signal only —
      // it does NOT feed the level logic.
      const dropCompleted = isDropSet && value !== false;
      const dropProgressionId = (isDropSet && value !== false)
        ? value
        : progInfo.currentProgression.id;

      const reps = (!isDropSet && progInfo.currentProgression.target_type === 'reps') ? value : null;
      const secs = (!isDropSet && progInfo.currentProgression.target_type === 'time') ? value : null;

      await addSet(
        currentWorkout.id,
        progInfo.exercise.id,
        isDropSet ? dropProgressionId : progInfo.currentProgression.id,
        step.setNumber,
        reps,
        secs,
        isDropSet ? REST_TIMES.afterDrop : REST_TIMES.normal,
        isDropSet,
        dropCompleted
      );

      if (currentStep === WORKOUT_STEPS.length - 1) {
        setShowCooldown(true);
      } else {
        setIsResting(true);
      }
    } catch (err) {
      console.error('Error saving set:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestComplete = () => { setIsResting(false); setCurrentStep(s => s + 1); };
  const handleExit = () => { if (window.confirm('Workout beenden?')) navigate('/'); };
  const handleModalClose = () => { setShowModal(false); navigate('/'); };

  const handleCooldownDone = async () => {
    setIsLoading(true);
    try {
      const result = await completeWorkout(currentWorkout.id);
      setProgressionData(result);
      setShowCooldown(false);
      setShowModal(true);
    } catch (err) {
      console.error('Error completing workout:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !isInitialized || !currentWorkout || WORKOUT_STEPS.length === 0) {
    return (
      <div className="loading-shell">
        <div className="loading-logo">COR<span>VIS</span></div>
        <div className="loading-spinner" />
        <p className="loading-text">Lade Training</p>
      </div>
    );
  }

  if (!isWarmupComplete) {
    return <WarmupChecklist onComplete={() => setIsWarmupComplete(true)} />;
  }

  if (showCooldown) {
    return <CooldownChecklist onComplete={handleCooldownDone} />;
  }

  if (isResting) {
    const step = WORKOUT_STEPS[currentStep];
    const nextStep = WORKOUT_STEPS[currentStep + 1];
    return (
      <RestTimer
        seconds={step.type === 'drop' ? REST_TIMES.afterDrop : REST_TIMES.normal}
        nextExercise={getNextLabel(nextStep)}
        onComplete={handleRestComplete}
      />
    );
  }

  const step = WORKOUT_STEPS[currentStep];
  const progInfo = getProgInfo(step.exerciseName);
  if (!progInfo) return <div className="loading-shell"><p className="loading-text">Fehler: Übung nicht gefunden</p></div>;

  const progressPct = ((currentStep + 1) / WORKOUT_STEPS.length) * 100;

  if (step.type === 'drop') {
    return (
      <div className="workout-shell">
        <header className="workout-header">
          <button className="workout-exit-btn" onClick={handleExit}>✕</button>
          <div className="workout-header-meta">
            <p className="workout-step-label">Schritt {currentStep + 1} / {WORKOUT_STEPS.length}</p>
            <div className="workout-progress-bar">
              <div className="workout-progress-fill" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        </header>
        <DropSetInstructions
          exercise={progInfo.exercise}
          progressions={[progInfo.currentProgression, ...progInfo.lowerProgressions]}
          lastReachedName={lastPerformance?.[String(progInfo.exercise.id)]?.drop_reached}
          onComplete={handleSetComplete}
        />
        {showModal && <ProgressionModal upgrades={progressionData?.upgrades || []} downgrades={progressionData?.downgrades || []} workouts={workouts} streak={streak} trainingDays={trainingDays} onClose={handleModalClose} />}
      </div>
    );
  }

  return (
    <div className="workout-shell">
      <header className="workout-header">
        <button className="workout-exit-btn" onClick={handleExit}>✕</button>
        <div className="workout-header-meta">
          <p className="workout-step-label">Schritt {currentStep + 1} / {WORKOUT_STEPS.length}</p>
          <div className="workout-progress-bar">
            <div className="workout-progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
      </header>

      <div className="workout-main">
        <p className="workout-exercise-cat">{progInfo.exercise.category}</p>
        <p className="workout-exercise-name">{progInfo.exercise.name}</p>
        <p className="workout-set-label">
          {progInfo.currentProgression.name} · Satz {step.setNumber}
        </p>
        <FormTip progressionName={progInfo.currentProgression.name} />
        {progInfo.currentProgression.target_type === 'reps' ? (
          <SetInput
            setNumber={step.setNumber}
            exerciseName={step.exerciseName}
            progressionName={progInfo.currentProgression.name}
            lastTime={getLastTime(step.exerciseName, step.setNumber)}
            onComplete={handleSetComplete}
          />
        ) : (
          <TimerInput
            setNumber={step.setNumber}
            exerciseName={step.exerciseName}
            progressionName={progInfo.currentProgression.name}
            targetSeconds={progInfo.currentProgression.target_value}
            lastTime={getLastTime(step.exerciseName, step.setNumber)}
            onComplete={handleSetComplete}
          />
        )}
      </div>

      {showModal && <ProgressionModal upgrades={progressionData?.upgrades || []} downgrades={progressionData?.downgrades || []} workouts={workouts} streak={streak} trainingDays={trainingDays} onClose={handleModalClose} />}
    </div>
  );
}
