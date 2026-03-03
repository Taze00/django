import { useEffect, useState, useMemo, useCallback } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';
import ExerciseCard from './ExerciseCard';
import WarmupChecklist from './WarmupChecklist';
import ProgressionUpgradeModal from './ProgressionUpgradeModal';
import RestDayModal from './RestDayModal';
import Header from '../Layout/Header';

export default function WorkoutView() {
  const {
    currentWorkout,
    exercises,
    userProgressions,
    lastPerformances,
    isLoading,
    error,
    initialize,
    completeWorkout,
    clearError,
    setWorkoutActive,
  } = useWorkoutStore();

  const [warmupCompleted, setWarmupCompleted] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [showRestTimer, setShowRestTimer] = useState(false);
  const [restTimeRemaining, setRestTimeRemaining] = useState(0);
  const [isCompleting, setIsCompleting] = useState(false);
  const [workoutCompleted, setWorkoutCompleted] = useState(false);
  const [upgrades, setUpgrades] = useState([]);
  const [downgrades, setDowngrades] = useState([]);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showRestDayModal, setShowRestDayModal] = useState(false);
  const [allowRestDayTraining, setAllowRestDayTraining] = useState(false);
  const [hasShownRestDayModal, setHasShownRestDayModal] = useState(false);

  // Rest timer effect
  useEffect(() => {
    if (!showRestTimer || restTimeRemaining <= 0) return;
    const interval = setInterval(() => {
      setRestTimeRemaining(prev => (prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [showRestTimer, restTimeRemaining]);

  // Initialize only once on mount
  useEffect(() => {
    console.log('[WorkoutView] Initializing...');
    initialize();
  }, []);

  // Handle rest timer completion
  useEffect(() => {
    if (restTimeRemaining === 0 && showRestTimer) {
      handleRestTimerComplete();
    }
  }, [restTimeRemaining, showRestTimer]);

  // Set isWorkoutActive based on current step
  useEffect(() => {
    const isActive = currentStep > 0 || showUpgradeModal || showRestDayModal;
    setWorkoutActive(isActive);
    return () => {
      setWorkoutActive(false);
    };
  }, [currentStep, showUpgradeModal, showRestDayModal, setWorkoutActive]);

  const getTodaysExercises = useCallback((forceIncludeRestDay = false) => {
    const now = new Date();
    const dayOfWeek = now.getDay() === 0 ? 7 : now.getDay();
    const schedule = {
      1: ["Push-up", "Pull-up"],
      2: ["Push-up", "Pull-up"],
      3: ["Push-up", "Pull-up"],
      4: ["Push-up", "Pull-up"],
      5: ["Push-up", "Pull-up"],
    };

    if (!forceIncludeRestDay && !schedule[dayOfWeek]) {
      return [];
    }

    if (forceIncludeRestDay && !schedule[dayOfWeek]) {
      return (exercises || []).filter(e => e.name === 'Push-up' || e.name === 'Pull-up');
    }

    const exerciseNames = schedule[dayOfWeek] || [];
    return exerciseNames
      .map(name => (exercises || []).find(e => e.name === name))
      .filter(Boolean);
  }, [exercises]);

  if (isLoading || !exercises || exercises.length === 0) {
    return (
      <>
        <Header title="Workout" icon="💪" />
        <div className="min-h-screen bg-slate-900 flex items-center justify-center pb-20">
          <div className="text-white">Loading...</div>
        </div>
      </>
    );
  }

  const todaysExercises = getTodaysExercises(allowRestDayTraining);
  const isRestDay = todaysExercises.length === 0;

  if (isRestDay && !allowRestDayTraining && !hasShownRestDayModal) {
    return (
      <>
        <Header title="Workout" icon="💪" />
        <RestDayModal
          onContinue={() => {
            setAllowRestDayTraining(true);
            setHasShownRestDayModal(true);
            setWarmupCompleted(false);
          }}
        />
      </>
    );
  }

  if (isRestDay && !currentWorkout && hasShownRestDayModal) {
    return (
      <>
        <Header title="Workout" icon="💪" />
        <div className="min-h-screen bg-slate-900 pb-20 flex items-center justify-center p-4">
          <div className="text-center">
            <div className="text-6xl mb-4">😎</div>
            <p className="text-slate-300 mb-4">It's a rest day!</p>
            <p className="text-slate-400 text-sm">You clicked "Train Anyway" but the system needs a workout. Try again tomorrow!</p>
          </div>
        </div>
      </>
    );
  }

  const buildWorkoutFlow = () => {
    if (todaysExercises.length < 2) {
      return todaysExercises[0]
        ? [
            { exercise: todaysExercises[0], setNum: 1, type: "regular" },
            { exercise: todaysExercises[0], setNum: 2, type: "regular" },
            { exercise: todaysExercises[0], setNum: 3, type: "regular" },
          ]
        : [];
    }
    const [push, pull] = todaysExercises;
    return [
      { exercise: push, setNum: 1, type: "regular" },
      { exercise: pull, setNum: 1, type: "regular" },
      { exercise: push, setNum: 2, type: "regular" },
      { exercise: pull, setNum: 2, type: "regular" },
      { exercise: push, setNum: 3, type: "regular" },
      { exercise: pull, setNum: 3, type: "regular" },
    ];
  };

  const workoutFlow = buildWorkoutFlow();
  const currentStepData = workoutFlow[currentStep];

  const handleSetCompleted = () => {
    const isAfterDropSet = currentStep === workoutFlow.length - 1;
    const restTime = isAfterDropSet ? 300 : 180;
    setRestTimeRemaining(restTime);
    setShowRestTimer(true);
  };

  const handleRestTimerComplete = () => {
    setShowRestTimer(false);
    if (currentStep < workoutFlow.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleCompleteWorkout();
    }
  };

  const handleCompleteWorkout = async () => {
    setIsCompleting(true);
    const result = await completeWorkout();
    setIsCompleting(false);
    if (result) {
      setWorkoutCompleted(true);
      if (result.upgrades && result.upgrades.length > 0) {
        setUpgrades(result.upgrades);
      }
      if (result.downgrades && result.downgrades.length > 0) {
        setDowngrades(result.downgrades);
      }
      if ((result.upgrades && result.upgrades.length > 0) || (result.downgrades && result.downgrades.length > 0)) {
        setShowUpgradeModal(true);
      }
    }
  };

  const handleBackStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setShowRestTimer(false);
    }
  };

  if (!warmupCompleted) {
    return (
      <>
        <Header title="Workout" icon="💪" />
        <div className="p-4">
          <WarmupChecklist
            workout={currentWorkout || {}}
            onCompleted={() => setWarmupCompleted(true)}
          />
        </div>
      </>
    );
  }

  if (workoutCompleted) {
    return (
      <>
        <Header title="Workout" icon="💪" />
        {showUpgradeModal ? (
          <ProgressionUpgradeModal upgrades={upgrades} downgrades={downgrades} />
        ) : (
          <div className="min-h-screen bg-slate-900 pb-20 flex items-center justify-center">
            <div className="text-center">
              <div className="text-8xl mb-4">🎉</div>
              <h2 className="text-3xl font-bold text-white">Great Workout!</h2>
            </div>
          </div>
        )}
      </>
    );
  }

  if (workoutFlow.length === 0) {
    return (
      <>
        <Header title="Workout" icon="💪" />
        <div className="min-h-screen bg-slate-900 pb-20 flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl mb-4">🤔</div>
            <p className="text-slate-300">No exercises scheduled</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Workout" icon="💪" />
      {showRestTimer ? (
        <div className="min-h-screen bg-slate-900 pb-20 flex items-center justify-center p-4">
          <div className="text-center space-y-8">
            <div>
              <div className="text-6xl mb-4">⏱️</div>
              <div className="text-white">
                <p className="text-sm text-slate-400 mb-2">Rest Time</p>
                <p className="text-5xl font-bold">{Math.floor(restTimeRemaining / 60)}:{String(restTimeRemaining % 60).padStart(2, "0")}</p>
              </div>
            </div>
            <button
              onClick={handleRestTimerComplete}
              className="mx-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-all text-lg"
            >
              Skip
            </button>
          </div>
        </div>
      ) : currentStepData ? (
        <div className="min-h-screen bg-slate-900 pb-20 p-4 space-y-6">
          <ExerciseCard
            exercise={currentStepData.exercise}
            setNumber={currentStepData.setNum}
            progression={(() => {
              const userProg = userProgressions[currentStepData.exercise.id];
              if (!userProg) return null;
              return currentStepData.exercise.progressions?.find(p => p.id === userProg.current_progression);
            })()}
            onSetCompleted={handleSetCompleted}
          />
          <button
            onClick={handleBackStep}
            disabled={currentStep === 0}
            className="w-full px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white font-semibold transition"
          >
            Back
          </button>
        </div>
      ) : null}
    </>
  );
}
