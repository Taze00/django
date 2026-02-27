import { useEffect, useState } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';
import ExerciseCard from './ExerciseCard';
import WarmupChecklist from './WarmupChecklist';
import ProgressionUpgradeModal from './ProgressionUpgradeModal';

// Simple 2-exercise rotation
// Mo/We/Fr = PUSH (Push-ups), Tu/Th = PULL (Pull-ups)
const SCHEDULE = {
  1: ['Push-up', 'Pull-up'],   // Monday
  2: ['Pull-up'],               // Tuesday
  3: ['Push-up', 'Pull-up'],    // Wednesday
  4: ['Pull-up'],               // Thursday
  5: ['Push-up', 'Pull-up'],    // Friday
  // 6 = Saturday (Rest)
  // 0/7 = Sunday (Rest)
};

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

  const [isCompleting, setIsCompleting] = useState(false);
  const [workoutCompleted, setWorkoutCompleted] = useState(false);
  const [upgrades, setUpgrades] = useState([]);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  useEffect(() => {
    console.log('[WorkoutView] Initializing...');
    initialize().catch(err => {
      console.error('[WorkoutView] Initialize error:', err);
    });
  }, []);

  useEffect(() => {
    console.log('[WorkoutView] State:', { isLoading, error, currentWorkout: !!currentWorkout, exercises: exercises.length });
  }, [isLoading, error, currentWorkout, exercises]);

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

  // Wait for exercises to load before rendering
  if (exercises.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300">Loading exercises...</p>
        </div>
      </div>
    );
  }

  // Get current day (1=Monday, ..., 5=Friday, 6=Saturday, 7=Sunday)
  const now = new Date();
  const dayOfWeek = now.getDay() === 0 ? 7 : now.getDay();
  const isRestDay = dayOfWeek === 6 || dayOfWeek === 7;  // Saturday or Sunday
  const todaysExerciseNames = SCHEDULE[dayOfWeek] || [];

  // Get today's exercises from the exercises list
  const todaysExercises = todaysExerciseNames
    .map(name => exercises.find(e => e.name === name))
    .filter(Boolean);

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

  const dayName = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][dayOfWeek];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4 sm:p-6 pb-20">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">
          💪 {dayName}'s Workout
        </h1>
        <p className="text-slate-400 text-sm">
          {todaysExercises.length} exercise{todaysExercises.length !== 1 ? 's' : ''} scheduled
        </p>
      </div>

      {/* Warmup Section */}
      {currentWorkout && (
        <div className="mb-6">
          <WarmupChecklist workout={currentWorkout} />
        </div>
      )}

      {/* Exercises */}
      <div className="space-y-4 mb-6">
        {todaysExercises.map((exercise, index) => {
          const workoutSets = currentWorkout?.sets?.filter(s => s.exercise === exercise.id) || [];
          const userProg = userProgressions?.[exercise.id];

          return (
            <ExerciseCard
              key={exercise.id}
              exercise={exercise}
              workoutSets={workoutSets}
              userProgression={userProg}
              exerciseIndex={index}
            />
          );
        })}
      </div>

      {/* Complete Workout Button */}
      {!workoutCompleted && (
        <div className="fixed bottom-20 left-0 right-0 p-4 bg-slate-900/80 backdrop-blur-sm border-t border-slate-700/50">
          <button
            onClick={handleCompleteWorkout}
            disabled={isCompleting || !currentWorkout}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-4 px-6 rounded-xl transition-all duration-200 active:scale-95 text-lg"
          >
            {isCompleting ? (
              <span className="flex items-center justify-center">
                <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-3"></span>
                Completing...
              </span>
            ) : (
              '✓ Complete Workout'
            )}
          </button>
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
