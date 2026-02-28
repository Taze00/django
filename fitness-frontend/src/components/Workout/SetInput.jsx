import { useState } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';

export default function SetInput({
  exercise,
  setNumber,
  progression,
  onCompleted,
  isDropSet = false,
}) {
  const lastPerformances = useWorkoutStore((state) => state.lastPerformances);
  const addSet = useWorkoutStore((state) => state.addSet);
  const [reps, setReps] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!progression) {
    return null;
  }

  // Get last performance for this progression
  // progression.id is a number, but lastPerformances keys are strings
  const lastPerf = lastPerformances?.[String(progression.id)];

  console.log('[SetInput] DEBUG:', {
    'progression.id': progression?.id,
    'progression.id as string': String(progression?.id),
    'lastPerformances keys': Object.keys(lastPerformances),
    'lastPerformances': lastPerformances,
    'lastPerf result': lastPerf,
    'lastPerf truthy?': !!lastPerf
  });

  const handleSave = async () => {
    if (reps === 0) {
      setError('Please enter at least 1 rep');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await addSet(
        exercise.id,
        progression.id,
        reps,
        setNumber,
        isDropSet
      );

      if (result) {
        onCompleted(setNumber, { reps });
      } else {
        setError('Failed to save set');
      }
    } catch (err) {
      console.error('Error saving set:', err);
      setError('Error saving set');
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
          <p className="text-white text-lg font-bold">{lastPerf.last_reps || lastPerf.reps} reps</p>
        </div>
      )}
      {!lastPerf && !isDropSet && (
        <div className="bg-slate-700/30 border border-slate-600/30 rounded-lg p-3">
          <p className="text-slate-400 text-xs font-semibold">FIRST TIME AT THIS LEVEL!</p>
        </div>
      )}

      {/* Rep Counter */}
      <div className="space-y-2">
        <div className="flex items-center gap-3 justify-center bg-slate-800/50 rounded-xl p-3 border border-slate-700">
          <button
            onClick={handleDecrement}
            className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-bold transition"
          >
            −
          </button>
          <span className="text-4xl font-bold text-white w-20 text-center">{reps}</span>
          <button
            onClick={handleIncrement}
            className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-bold transition"
          >
            +
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={isLoading}
        className="w-full px-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold transition"
      >
        {isLoading ? 'Saving...' : 'Complete Set ✓'}
      </button>
    </div>
  );
}
