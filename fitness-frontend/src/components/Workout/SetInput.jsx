import { useState } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';

export default function SetInput({
  exercise,
  setNumber,
  userProgression,
  existingSet,
  onCompleted,
  isDropSet = false,
  currentProgression,
}) {
  const { addSet, lastPerformances } = useWorkoutStore();
  const [reps, setReps] = useState(existingSet?.reps || 7);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dropSetProgressionId, setDropSetProgressionId] = useState(
    existingSet?.drop_set_progression || userProgression?.current_progression || null
  );

  // Get current progression if not passed as prop
  const progression = currentProgression ||
    (Array.isArray(exercise?.progressions)
      ? exercise.progressions.find((p) => p?.id === userProgression?.current_progression)
      : null);

  // Get available progressions for drop set
  const availableProgressions = progression
    ? (exercise?.progressions || []).filter((p) => p?.level < progression.level)
    : [];

  // Get last performance for this progression
  const lastPerf = progression ? lastPerformances?.[progression.id] : null;

  const handleSave = async () => {
    if (reps === 0) {
      setError('Please enter at least 1 rep');
      return;
    }

    if (!userProgression) {
      setError('User progression data not loaded - please reload the page');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const progressionId = isDropSet ? dropSetProgressionId : userProgression.current_progression;

      if (!progressionId) {
        setError('Progression not found - please reload the page');
        return;
      }

      const result = await addSet(
        exercise.id,
        progressionId,
        reps,
        setNumber,
        isDropSet
      );

      if (result) {
        onCompleted(setNumber, { isUpdate: !!existingSet, reps: reps });
      } else {
        setError('Failed to save set - please try again');
      }
    } catch (err) {
      console.error('Error saving set:', err);
      setError('Error saving set - please check your connection and try again');
    } finally {
      setIsLoading(false);
    }
  };

  const handleIncrement = () => setReps((r) => r + 1);
  const handleDecrement = () => setReps((r) => (r > 0 ? r - 1 : 0));

  return (
    <div className="space-y-4">
      {/* Last Time Info */}
      {lastPerf && !isDropSet && (
        <div className="bg-slate-700/30 border border-slate-600/30 rounded-lg p-3">
          <p className="text-slate-400 text-xs font-semibold mb-1">LAST TIME</p>
          <p className="text-white text-lg font-bold">{lastPerf.last_reps} reps</p>
        </div>
      )}
      {!lastPerf && !isDropSet && (
        <div className="bg-slate-700/30 border border-slate-600/30 rounded-lg p-3">
          <p className="text-slate-400 text-xs font-semibold">FIRST TIME AT THIS LEVEL!</p>
        </div>
      )}

      {/* Rep Counter */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-slate-300">
          How many reps with perfect form?
        </label>
        <div className="flex items-center gap-3 justify-center bg-slate-800/50 rounded-xl p-3 border border-slate-700">
          <button
            onClick={handleDecrement}
            disabled={isLoading}
            className="w-12 h-12 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:opacity-50 text-white font-bold text-xl transition-all active:scale-90"
          >
            −
          </button>

          <div className="text-center min-w-28">
            <div className="text-5xl font-bold text-blue-400 font-mono leading-tight">
              {reps}
            </div>
            <p className="text-slate-400 text-xs mt-0.5 uppercase tracking-widest">reps</p>
          </div>

          <button
            onClick={handleIncrement}
            disabled={isLoading}
            className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 disabled:from-slate-600 disabled:to-slate-700 disabled:opacity-50 text-white font-bold text-xl transition-all shadow-lg shadow-blue-500/30 active:scale-90"
          >
            +
          </button>
        </div>
      </div>

      {/* Drop Set Progression Selector */}
      {isDropSet && availableProgressions.length > 0 && (
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-300">
            🔥 Drop Set Progression
          </label>
          <select
            value={dropSetProgressionId}
            onChange={(e) => setDropSetProgressionId(Number(e.target.value))}
            disabled={isLoading}
            className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded-lg text-white disabled:opacity-50"
          >
            {availableProgressions.map((prog) => (
              <option key={prog.id} value={prog.id}>
                {prog.name} (Level {prog.level})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 px-3 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={isLoading || reps === 0}
        className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 active:scale-95"
      >
        {isLoading ? (
          <span className="flex items-center justify-center">
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>
            Saving...
          </span>
        ) : existingSet?.reps ? (
          `✓ Update Set ${setNumber}`
        ) : (
          `✓ Save Set ${setNumber}`
        )}
      </button>
    </div>
  );
}
