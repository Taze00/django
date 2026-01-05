import { useState } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';
import SetInput from './SetInput';

export default function DropSetModal({
  exercise,
  workoutSet,
  userProgression,
  onClose,
}) {
  const [isExpanded, setIsExpanded] = useState(!workoutSet);

  const currentProgression = exercise.progressions.find(
    (p) => p.id === userProgression?.current_progression
  );

  // Get available progressions for drop set (lower levels)
  const availableProgressions = exercise.progressions.filter(
    (p) => p.level < currentProgression.level
  );

  const handleSetCompleted = () => {
    // After drop set is saved, close modal after a brief delay
    setTimeout(onClose, 500);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-2xl border border-slate-700 max-w-sm w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-600 to-red-600 px-6 py-4">
          <h2 className="text-xl font-bold text-white">🔥 Drop Set (Set 3)</h2>
          <p className="text-orange-100 text-sm mt-1">
            Complete reps at a lower progression level
          </p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Current Progression Info */}
          <div className="bg-slate-700/50 rounded-lg p-3">
            <p className="text-slate-400 text-xs mb-1">Main Set Level</p>
            <p className="text-white font-semibold">{currentProgression.name}</p>
          </div>

          {/* Info Text */}
          <p className="text-slate-300 text-sm">
            After completing your main set, drop to an easier progression and
            complete as many reps as possible. This increases volume and muscle
            fatigue.
          </p>

          {/* Set Input (Collapsed by Default) */}
          {!isExpanded && workoutSet && (
            <div>
              <button
                onClick={() => setIsExpanded(true)}
                className="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition-colors"
              >
                ✓ {workoutSet.drop_set_reps} reps completed
              </button>
              <button
                onClick={() => setIsExpanded(true)}
                className="w-full mt-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
              >
                Edit
              </button>
            </div>
          )}

          {/* Set Input (Expanded) */}
          {isExpanded && (
            <div className="bg-slate-700/50 rounded-lg p-4">
              <SetInput
                exercise={exercise}
                setNumber={3}
                userProgression={userProgression}
                existingSet={
                  workoutSet
                    ? { ...workoutSet, reps: workoutSet.drop_set_reps }
                    : null
                }
                onCompleted={handleSetCompleted}
                isDropSet={true}
              />
            </div>
          )}

          {/* Available Progressions Info */}
          {availableProgressions.length > 0 && (
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
              <p className="text-blue-300 text-xs font-semibold mb-2">
                Available Drop Progressions
              </p>
              <div className="space-y-1">
                {availableProgressions.slice(0, 3).map((prog) => (
                  <p key={prog.id} className="text-blue-200 text-xs">
                    • {prog.name} (Level {prog.level})
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Close Button */}
        {!isExpanded && (
          <div className="bg-slate-700 px-6 py-3 border-t border-slate-600">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg font-semibold transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
