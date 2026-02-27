import { useState, useEffect } from 'react';
import { useStatsStore } from '../../store/statsStore';
import { useWorkoutStore } from '../../store/workoutStore';
import StatsCard from './StatsCard';
import ExerciseSelector from './ExerciseSelector';
import ExerciseProgressChart from './ExerciseProgressChart';
import ProgressionTimeline from './ProgressionTimeline';

export default function StatsView() {
  const [selectedExercise, setSelectedExercise] = useState(null);
  const { overview, fetchOverview, isLoading } = useStatsStore();
  const { exercises, fetchExercises } = useWorkoutStore();

  useEffect(() => {
    fetchOverview();
    if (!exercises || exercises.length === 0) {
      fetchExercises();
    }
  }, [fetchOverview, fetchExercises, exercises]);

  const formatDuration = (seconds) => {
    if (!seconds) return '0h 0m';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-slate-800/95 backdrop-blur border-b border-slate-700 z-10">
        <h1 className="text-2xl font-bold text-white p-4">📊 Statistics</h1>
      </div>

      {/* Overview Cards */}
      {isLoading ? (
        <div className="p-4 text-center text-slate-400">Loading statistics...</div>
      ) : overview ? (
        <div className="p-4 grid grid-cols-2 gap-3">
          <StatsCard
            label="Workouts"
            value={overview.total_workouts}
            icon="💪"
          />
          <StatsCard
            label="Current Streak"
            value={`${overview.current_streak}🔥`}
            icon={null}
          />
          <StatsCard
            label="Total Time"
            value={formatDuration(overview.total_time_seconds)}
            icon="⏱️"
          />
          <StatsCard
            label="Total Reps"
            value={overview.total_reps}
            icon="🔢"
          />
          <StatsCard
            label="Total Sets"
            value={overview.total_sets}
            icon="📦"
          />
        </div>
      ) : null}

      {/* Exercise Selector */}
      <ExerciseSelector
        exercises={exercises}
        selected={selectedExercise}
        onSelect={setSelectedExercise}
      />

      {/* Charts */}
      {selectedExercise && (
        <>
          <ExerciseProgressChart exerciseId={selectedExercise.id} />
          <ProgressionTimeline exerciseId={selectedExercise.id} />
        </>
      )}

      {/* Empty State */}
      {!selectedExercise && (
        <div className="p-4 text-center text-slate-400 mt-8">
          <p>📈 Select an exercise to view progress</p>
        </div>
      )}
    </div>
  );
}
