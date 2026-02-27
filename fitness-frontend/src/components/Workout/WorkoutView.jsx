import { useEffect, useState } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';
import ExerciseCard from './ExerciseCard';
import WarmupChecklist from './WarmupChecklist';
import ProgressionUpgradeModal from './ProgressionUpgradeModal';

// 6-Step Alternating Flow: Push1 → Pull1 → Push2 → Pull2 → Push3 → Pull3
// Rest times: 3 min between sets, 5 min after Set 3 (before drop set)

export default function WorkoutView() {
  const {
    currentWorkout,
    exercises,
    userProgressions,
    isLoading,
    error,
    initialize,
    completeWorkout,
    clearError,
  } = useWorkoutStore();

  const [currentStep, setCurrentStep] = useState(0); // 0-5 = 6 steps
  const [showRestTimer, setShowRestTimer] = useState(false);
  const [restTimeRemaining, setRestTimeRemaining] = useState(0);
  const [isCompleting, setIsCompleting] = useState(false);
  const [workoutCompleted, setWorkoutCompleted] = useState(false);
  const [upgrades, setUpgrades] = useState([]);
  const [downgrades, setDowngrades] = useState([]);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  // Rest timer countdown effect
  useEffect(() => {
    if (!showRestTimer || restTimeRemaining <= 0) return;

    const interval = setInterval(() => {
      setRestTimeRemaining(prev => {
        if (prev <= 1) {
          handleRestTimerComplete();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [showRestTimer, restTimeRemaining]);

  useEffect(() => {
    console.log('[WorkoutView] Initializing...');
    initialize().catch(err => {
      console.error('[WorkoutView] Initialize error:', err);
    });
  }, []);

  // Get today's schedule (2 exercises max)
  const getTodaysExercises = () => {
    const now = new Date();
    const dayOfWeek = now.getDay() === 0 ? 7 : now.getDay();

    const schedule = {
      1: ['Push-up', 'Pull-up'],   // Monday
      2: ['Push-up', 'Pull-up'],   // Tuesday
      3: ['Push-up', 'Pull-up'],   // Wednesday
      4: ['Push-up', 'Pull-up'],   // Thursday
      5: ['Push-up', 'Pull-up'],   // Friday
      // 6 = Saturday (Rest), 0/7 = Sunday (Rest)
    };

    const exerciseNames = schedule[dayOfWeek] || [];
    return exerciseNames
      .map(name => exercises.find(e => e.name === name))
      .filter(Boolean);
  };

  const todaysExercises = getTodaysExercises();
  const isRestDay = todaysExercises.length === 0;

  // Build 6-step workout flow
  const buildWorkoutFlow = () => {
    if (todaysExercises.length < 2) {
      // Single exercise: 3 sets + drop set
      return todaysExercises[0]
        ? [
            { exercise: todaysExercises[0], setNum: 1, type: 'regular' },
            { exercise: todaysExercises[0], setNum: 2, type: 'regular' },
            { exercise: todaysExercises[0], setNum: 3, type: 'regular' },
          ]
        : [];
    }

    // 2 exercises: alternating flow
    const [push, pull] = todaysExercises;
    return [
      { exercise: push, setNum: 1, type: 'regular' },
      { exercise: pull, setNum: 1, type: 'regular' },
      { exercise: push, setNum: 2, type: 'regular' },
      { exercise: pull, setNum: 2, type: 'regular' },
      { exercise: push, setNum: 3, type: 'regular' },
      { exercise: pull, setNum: 3, type: 'regular' },
    ];
  };

  const workoutFlow = buildWorkoutFlow();
  const currentStepData = workoutFlow[currentStep];

  const handleSetCompleted = () => {
    // Show rest timer
    const isAfterDropSet = currentStep === workoutFlow.length - 1;
    const restTime = isAfterDropSet ? 300 : 180; // 5 min after Set 3, 3 min between

    setRestTimeRemaining(restTime);
    setShowRestTimer(true);
  };

  const handleRestTimerComplete = () => {
    setShowRestTimer(false);

    // Move to next step
    if (currentStep < workoutFlow.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Workout complete - ask to finish
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
        const formattedUpgrades = result.upgrades.map((upgrade) => ({
          exercise_name: upgrade.exercise_name,
          old_progression: {
            level: upgrade.old_progression.level,
            name: upgrade.old_progression.name,
            description: upgrade.old_progression.description,
          },
          new_progression: {
            level: upgrade.new_progression.level,
            name: upgrade.new_progression.name,
            description: upgrade.new_progression.description,
          },
          sessions_at_target: upgrade.sessions_at_target,
          sessions_required: upgrade.sessions_required,
        }));

        setUpgrades(formattedUpgrades);
        setShowUpgradeModal(true);
      }

      if (result.downgrades && result.downgrades.length > 0) {
        setDowngrades(result.downgrades);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300">Loading workout...</p>
          <p className="text-slate-500 text-sm mt-2">Exercises: {exercises.length}</p>
        </div>
      </div>
    );
  }

  const now = new Date();
  const dayOfWeek = now.getDay() === 0 ? 7 : now.getDay();
  const dayName = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][dayOfWeek];

  if (isRestDay) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6 flex flex-col items-center justify-center">
        <div className="bg-gradient-to-r from-emerald-500/15 to-teal-500/15 backdrop-blur-sm border border-emerald-500/30 rounded-2xl p-8 text-center max-w-md">
          <p className="text-4xl mb-4">😎</p>
          <h2 className="text-2xl font-bold text-white mb-2">Rest Day!</h2>
          <p className="text-slate-300 text-sm">
            Great job pushing yourself! Take today to recover and prepare for your next workout.
          </p>
        </div>
      </div>
    );
  }

  if (!currentWorkout) {
    return (
      <div className="min-h-screen bg-slate-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400">No workout scheduled for today</p>
        </div>
      </div>
    );
  }

  if (!currentStepData) {
    return (
      <div className="min-h-screen bg-slate-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400">Workout flow not configured</p>
        </div>
      </div>
    );
  }

  const exercise = currentStepData.exercise;
  const userProg = userProgressions?.[exercise.id];
  const workoutSets = currentWorkout?.sets?.filter(s => s.exercise === exercise.id) || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4 sm:p-6 pb-20">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">
          💪 {dayName}'s Workout
        </h1>
        <p className="text-slate-400 text-sm">
          Step {currentStep + 1} of {workoutFlow.length}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-6 bg-slate-800/50 rounded-lg p-4 border border-slate-700/30">
        <div className="flex items-center justify-between mb-2">
          <p className="text-slate-300 text-sm font-semibold">Workout Progress</p>
          <p className="text-slate-400 text-xs">{currentStep + 1}/{workoutFlow.length}</p>
        </div>
        <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-300"
            style={{ width: `${((currentStep + 1) / workoutFlow.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Warmup - Show only on first step */}
      {currentStep === 0 && currentWorkout && (
        <div className="mb-6">
          <WarmupChecklist workout={currentWorkout} />
        </div>
      )}

      {/* Current Exercise */}
      <div className="mb-6">
        <ExerciseCard
          exercise={exercise}
          workoutSets={workoutSets}
          userProgression={userProg}
          exerciseIndex={0}
          onSetCompleted={handleSetCompleted}
          setNumber={currentStepData?.setNum}
        />
      </div>

      {/* Rest Timer */}
      {showRestTimer && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 max-w-sm w-full text-center">
            <p className="text-slate-400 text-sm mb-4">Next Exercise in</p>
            <div className="text-6xl font-bold text-blue-400 font-mono mb-4">
              {Math.floor(restTimeRemaining / 60)}:{(restTimeRemaining % 60).toString().padStart(2, '0')}
            </div>
            <button
              onClick={handleRestTimerComplete}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-all"
            >
              ▶ I'm Ready
            </button>
          </div>
        </div>
      )}

      {/* Navigation */}
      {!showRestTimer && !workoutCompleted && (
        <div className="fixed bottom-20 left-0 right-0 p-4 bg-slate-900/80 backdrop-blur-sm border-t border-slate-700/50">
          <div className="flex gap-3 max-w-md mx-auto">
            {/* Back Button - Always available if not first step */}
            {currentStep > 0 && (
              <button
                onClick={() => setCurrentStep(currentStep - 1)}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 px-4 rounded-lg transition-all"
                title="Go back to previous set"
              >
                ← Back
              </button>
            )}

            {/* Complete Button - Last step */}
            {currentStep === workoutFlow.length - 1 && (
              <button
                onClick={handleCompleteWorkout}
                disabled={isCompleting}
                className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-3 px-4 rounded-lg transition-all"
              >
                {isCompleting ? (
                  <span className="flex items-center justify-center">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>
                    Completing...
                  </span>
                ) : (
                  '✓ Complete Workout'
                )}
              </button>
            )}

            {/* Next Button - Middle steps */}
            {currentStep < workoutFlow.length - 1 && (
              <button
                onClick={() => setCurrentStep(currentStep + 1)}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-all"
              >
                Next Set →
              </button>
            )}
          </div>
        </div>
      )}

      {/* Workout Completed Message */}
      {workoutCompleted && (
        <div className="fixed bottom-20 left-0 right-0 p-4 bg-slate-900/80 backdrop-blur-sm border-t border-emerald-500/30">
          <div className="bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/50 rounded-lg p-4 text-center">
            <p className="text-emerald-300 font-bold">✓ Workout Completed!</p>
            <p className="text-slate-300 text-sm mt-1">Great effort today!</p>
          </div>
        </div>
      )}

      {/* Progression Upgrade Modal */}
      {showUpgradeModal && (
        <ProgressionUpgradeModal
          upgrades={upgrades}
          onClose={() => setShowUpgradeModal(false)}
        />
      )}

      {/* Error Message */}
      {error && (
        <div className="fixed bottom-32 left-4 right-4 bg-red-500/10 border border-red-500/30 text-red-300 px-4 py-3 rounded-lg text-sm">
          <div className="flex items-start justify-between">
            <span>{error}</span>
            <button
              onClick={clearError}
              className="text-red-300 hover:text-red-200 font-bold"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
