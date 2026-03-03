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

  const availableProgressions = exercise.progressions.filter(
    (p) => p.level < currentProgression.level
  );

  const handleSetCompleted = () => {
    setTimeout(onClose, 500);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-2xl border border-slate-700 max-w-sm w-full overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-600 to-red-600 px-4 py-2 flex-shrink-0">
          <h2 className="text-base font-bold text-white">🔥 Drop Set</h2>
        </div>

        {/* Content */}
        <div className="p-3 space-y-2 overflow-y-auto flex-1">
          {/* Current Progression Info */}
          <div className="bg-slate-700/50 rounded-lg p-2">
            <p className="text-slate-400 text-xs mb-0.5">Main Level</p>
            <p className="text-white text-sm font-semibold">{currentProgression.name}</p>
          </div>

          {/* Set Input (Collapsed by Default) */}
          {!isExpanded && workoutSet && (
            <div>
              <button
                onClick={() => setIsExpanded(true)}
                className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold text-sm transition-colors"
              >
                ✓ {workoutSet.drop_set_reps} reps completed
              </button>
              <button
                onClick={() => setIsExpanded(true)}
                className="w-full mt-2 px-4 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs transition-colors"
              >
                Edit
              </button>
            </div>
          )}

          {/* Set Input (Expanded) */}
          {isExpanded && (
            <div className="bg-slate-700/50 rounded-lg p-3">
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
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-2">
              <p className="text-blue-300 text-xs font-semibold mb-1">
                Drop Options
              </p>
              <div className="space-y-0.5">
                {availableProgressions.slice(0, 3).map((prog) => (
                  <p key={prog.id} className="text-blue-200 text-xs">
                    • {prog.name}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Close Button */}
        {!isExpanded && (
          <div className="bg-slate-700 px-3 py-1.5 border-t border-slate-600 flex-shrink-0">
            <button
              onClick={onClose}
              className="w-full px-3 py-1 bg-slate-600 hover:bg-slate-500 text-white rounded text-xs font-semibold transition-colors"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
