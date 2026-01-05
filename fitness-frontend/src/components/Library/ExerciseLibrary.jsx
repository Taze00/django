import { useState, useEffect } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';
import ExerciseDetail from './ExerciseDetail';

export default function ExerciseLibrary() {
  const { exercises, userProgressions, isLoading } = useWorkoutStore();
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const filteredExercises =
    categoryFilter === 'ALL'
      ? exercises
      : exercises.filter((ex) => ex.category === categoryFilter);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300">Loading exercises...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 pb-32">
      {/* Header */}
      <div className="sticky top-0 bg-slate-800/95 backdrop-blur border-b border-slate-700 z-10">
        <div className="px-4 py-4">
          <h1 className="text-2xl font-bold text-white">📚 Exercise Library</h1>
          <p className="text-slate-400 text-sm mt-1">
            View all exercises and progression levels
          </p>
        </div>

        {/* Category Filter */}
        <div className="px-4 pb-4 flex gap-2">
          {['ALL', 'PUSH', 'PULL'].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                categoryFilter === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {cat === 'ALL'
                ? '🔄 All'
                : cat === 'PUSH'
                  ? '💪 Push'
                  : '🔥 Pull'}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 py-6 space-y-3">
        {filteredExercises.map((exercise) => {
          const userProgression = userProgressions[exercise.id];
          const currentProgression = exercise.progressions.find(
            (p) => p.id === userProgression?.current_progression
          );

          return (
            <button
              key={exercise.id}
              onClick={() => setSelectedExercise(exercise)}
              className="w-full text-left bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-2xl p-4 transition-all hover:scale-102 active:scale-95"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-lg font-bold text-white">
                    {exercise.name}
                  </h3>
                  <p className="text-slate-400 text-sm mt-1">
                    {exercise.description}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ml-2 ${
                    exercise.category === 'PUSH'
                      ? 'bg-blue-500/20 text-blue-300'
                      : 'bg-orange-500/20 text-orange-300'
                  }`}
                >
                  {exercise.category}
                </span>
              </div>

              {/* Current Progression */}
              {currentProgression && (
                <div className="bg-slate-700/50 rounded-lg p-2 mt-3">
                  <p className="text-slate-400 text-xs mb-1">Current Level</p>
                  <p className="text-white font-semibold text-sm">
                    Level {currentProgression.level}: {currentProgression.name}
                  </p>
                </div>
              )}

              {/* Progression Count */}
              <div className="mt-3 flex items-center justify-between">
                <p className="text-slate-400 text-xs">
                  {exercise.progressions.length} progressions available
                </p>
                <span className="text-slate-400">→</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Exercise Detail Modal */}
      {selectedExercise && (
        <ExerciseDetail
          exercise={selectedExercise}
          userProgression={userProgressions[selectedExercise.id]}
          onClose={() => setSelectedExercise(null)}
        />
      )}
    </div>
  );
}
