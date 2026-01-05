import { useState, useEffect } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';

export default function SetInput({
  exercise,
  setNumber,
  userProgression,
  existingSet,
  onCompleted,
  isDropSet = false,
}) {
  const { addSet } = useWorkoutStore();
  const [reps, setReps] = useState(existingSet?.reps || 0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // For drop sets, we might use a different progression
  const [dropSetProgressionId, setDropSetProgressionId] = useState(
    existingSet?.drop_set_progression || userProgression?.current_progression
  );

  const currentProgression = exercise.progressions.find(
    (p) => p.id === userProgression?.current_progression
  );

  // Get available progressions for drop set
  const availableProgressions = exercise.progressions.filter(
    (p) => p.level < currentProgression.level
  );

  const handleSave = async () => {
    if (reps === 0) {
      setError('Please enter at least 1 rep');
      return;
    }

    setIsLoading(true);
    setError(null);

    const result = await addSet(
      exercise.id,
      isDropSet ? dropSetProgressionId : userProgression.current_progression,
      reps,
      setNumber,
      isDropSet
    );

    setIsLoading(false);

    if (result) {
      onCompleted(setNumber);
    } else {
      setError('Failed to save set');
    }
  };

  const handleIncrement = () => setReps((r) => r + 1);
  const handleDecrement = () => setReps((r) => (r > 0 ? r - 1 : 0));

  return (
    <div className="space-y-4">
      {/* Rep Counter */}
      <div className="space-y-2">
        <label className="block text-sm font-semibold text-slate-300">
          Reps Completed
        </label>
        <div className="flex items-center gap-3 justify-center">
          <button
            onClick={handleDecrement}
            disabled={isLoading}
            className="w-12 h-12 rounded-lg bg-slate-600 hover:bg-slate-500 disabled:bg-slate-700 text-white font-bold text-xl transition-colors"
          >
            −
          </button>

          <div className="text-center min-w-32">
            <div className="text-5xl font-bold text-blue-400 font-mono">
              {reps}
            </div>
            <p className="text-slate-400 text-xs mt-2">reps</p>
          </div>

          <button
            onClick={handleIncrement}
            disabled={isLoading}
            className="w-12 h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-bold text-xl transition-colors"
          >
            +
          </button>
        </div>
      </div>

      {/* Drop Set Progression Selector */}
      {isDropSet && availableProgressions.length > 0 && (
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-300">
            Drop Set Progression
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
        ) : (
          `✓ Save Set ${setNumber}`
        )}
      </button>
    </div>
  );
}
