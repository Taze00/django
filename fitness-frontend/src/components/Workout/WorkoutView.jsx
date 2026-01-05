import { useEffect, useState } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';
import ExerciseCard from './ExerciseCard';
import WarmupChecklist from './WarmupChecklist';
import ProgressionUpgradeModal from './ProgressionUpgradeModal';

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

  // Initialize on mount
  useEffect(() => {
    console.log('WorkoutView mounting, calling initialize...');
    initialize().catch(err => {
      console.error('Initialize error:', err);
    });
  }, []);

  // Debug logging
  useEffect(() => {
    console.log('WorkoutView state:', { isLoading, error, currentWorkout: !!currentWorkout, exercises: exercises.length });
  }, [isLoading, error, currentWorkout, exercises]);

  const handleCompleteWorkout = async () => {
    setIsCompleting(true);
    const result = await completeWorkout();
    setIsCompleting(false);

    if (result) {
      setWorkoutCompleted(true);

      // Check for progression upgrades
      if (result.upgrades && result.upgrades.length > 0) {
        // Format upgrades data for display
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
          qualifying_workouts: upgrade.qualifying_workouts,
          average_reps: upgrade.average_reps,
        }));

        setUpgrades(formattedUpgrades);
        setShowUpgradeModal(true);
      }

      // Show completion message for 3 seconds
      setTimeout(() => {
        setWorkoutCompleted(false);
      }, 3000);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300">Lade Training...</p>
          <p className="text-slate-500 text-sm mt-2">Exercises: {exercises.length}, Progressions: {Object.keys(userProgressions).length}</p>
        </div>
      </div>
    );
  }

  if (!currentWorkout) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center space-y-4">
          <p className="text-slate-300 text-lg">Kein aktives Training gefunden</p>
          <p className="text-slate-400 text-sm">Loading={String(isLoading)}, Error={error || 'keine'}</p>
          {error && (
            <div className="bg-red-500/10 border border-red-500 px-4 py-2 rounded text-red-300 text-sm max-w-sm">
              {error}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Get workout type (PUSH or PULL) - default to today's day
  const workoutType = currentWorkout.workout_type;
  const todaysExercises = Array.isArray(exercises)
    ? exercises.filter((ex) => ex.category === workoutType)
    : [];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Error banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 px-4 py-3 rounded-lg mx-4 mt-4 flex justify-between items-center">
          <span>{error}</span>
          <button
            onClick={clearError}
            className="text-red-400 hover:text-red-300 font-bold"
          >
            ×
          </button>
        </div>
      )}

      {/* Completion banner */}
      {workoutCompleted && (
        <div className="bg-green-500/10 border border-green-500/30 text-green-300 px-4 py-3 rounded-lg mx-4 mt-4">
          ✓ Workout completed successfully!
        </div>
      )}

      {/* Header */}
      <div className="sticky top-0 bg-slate-800/95 backdrop-blur border-b border-slate-700 z-10">
        <div className="px-4 py-4">
          <h1 className="text-2xl font-bold text-white">
            {workoutType === 'PUSH' ? '💪 Push Workout' : '🔥 Pull Workout'}
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {new Date(currentWorkout.date).toLocaleDateString('en-US', {
              weekday: 'long',
              month: 'short',
              day: 'numeric',
            })}
          </p>
        </div>
      </div>

      <div className="px-4 py-6 space-y-6 pb-24">
        {/* Weekly Schedule */}
        <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700">
          <h2 className="text-lg font-bold text-white mb-4">📅 Wochenplan</h2>
          <div className="grid grid-cols-7 gap-2">
            {['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'].map((day, idx) => {
              const schedule = ['PUSH', 'PULL', 'Rest', 'PUSH', 'PULL', 'Rest', 'Rest'];
              const type = schedule[idx];
              const isToday = new Date().getDay() === (idx + 1) % 7;

              return (
                <div
                  key={day}
                  className={`flex flex-col items-center p-3 rounded-lg border-2 transition-all ${
                    isToday
                      ? 'border-blue-500 bg-blue-500/10'
                      : type === 'Rest'
                      ? 'border-slate-600 bg-slate-700/30'
                      : 'border-slate-600 bg-slate-700/50'
                  }`}
                >
                  <p className="text-slate-300 text-xs font-semibold mb-1">{day}</p>
                  <p className={`text-sm font-bold ${
                    type === 'Rest'
                      ? 'text-slate-400'
                      : type === 'PUSH'
                      ? 'text-blue-300'
                      : 'text-red-300'
                  }`}>
                    {type === 'Rest' ? '😴' : type === 'PUSH' ? '💪' : '🔥'}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">{type === 'Rest' ? 'Rest' : type}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Warmup Checklist */}
        <WarmupChecklist workout={currentWorkout} />

        {/* Exercises */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-white px-2">Exercises</h2>
          {todaysExercises.map((exercise, index) => (
            <ExerciseCard
              key={exercise.id}
              exercise={exercise}
              workoutSets={
                currentWorkout.sets?.filter((s) => s.exercise === exercise.id) ||
                []
              }
              userProgression={userProgressions[exercise.id]}
              exerciseIndex={index}
            />
          ))}
        </div>

        {/* Complete Workout Button */}
        <div className="pt-4 pb-4">
          <button
            onClick={handleCompleteWorkout}
            disabled={isCompleting || workoutCompleted}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-4 px-4 rounded-lg transition-all duration-200 active:scale-95"
          >
            {isCompleting ? (
              <span className="flex items-center justify-center">
                <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>
                Completing...
              </span>
            ) : workoutCompleted ? (
              '✓ Completed!'
            ) : (
              'Complete Workout'
            )}
          </button>
        </div>
      </div>

      {/* Progression Upgrade Modal */}
      {showUpgradeModal && (
        <ProgressionUpgradeModal
          upgrades={upgrades}
          onClose={() => setShowUpgradeModal(false)}
        />
      )}
    </div>
  );
}
