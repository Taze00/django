import { useState } from 'react';
import SetInput from './SetInput';
import RestTimer from './RestTimer';
import DropSetModal from './DropSetModal';

export default function ExerciseCard({
  exercise,
  workoutSets,
  userProgression,
  exerciseIndex,
}) {
  const [expandedSetIndex, setExpandedSetIndex] = useState(null);
  const [showRestTimer, setShowRestTimer] = useState(false);
  const [showDropSetModal, setShowDropSetModal] = useState(false);
  const [lastCompletedSetNumber, setLastCompletedSetNumber] = useState(null);

  // Debug logging
  if (!userProgression) {
    console.warn(`[ExerciseCard] No userProgression for exercise ${exercise?.id} (${exercise?.name})`);
  }

  // Get current progression level
  const currentProgression = Array.isArray(exercise?.progressions)
    ? exercise.progressions.find((p) => p?.id === userProgression?.current_progression)
    : null;

  const handleSetCompleted = (setNumber, info = {}) => {
    setLastCompletedSetNumber(setNumber);
    setExpandedSetIndex(null);

    // Only show rest timer and drop set modal for NEW sets, not updates
    if (info.isUpdate) {
      console.log(`[ExerciseCard] Set ${setNumber} updated with ${info.reps} reps`);
      return; // Don't show timer for updates
    }

    // Show rest timer after each set (except last set, which shows drop set modal)
    if (setNumber < 3) {
      setShowRestTimer(true);
    } else if (setNumber === 3) {
      // For set 3, show drop set modal
      setShowDropSetModal(true);
    }
  };

  const handleTimerComplete = () => {
    setShowRestTimer(false);
    const nextSet = (lastCompletedSetNumber || 0) + 1;
    if (nextSet <= 3) {
      setExpandedSetIndex(nextSet - 1);
    }
  };

  // Calculate sets statistics
  const completedSets = Array.isArray(workoutSets)
    ? workoutSets.filter(s => s?.reps !== null).length
    : 0;
  const totalSets = 3;

  return (
    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-5 border border-slate-700 hover:border-slate-600 transition-all duration-200 shadow-lg">
      {/* Exercise Header with Number Badge */}
      <div className="flex items-start gap-3 mb-4">
        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-blue-500/30 flex items-center justify-center border border-blue-500/50">
          <span className="text-blue-300 font-bold text-lg">{exerciseIndex + 1}</span>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-bold text-white">{exercise.name}</h3>
          <p className="text-slate-400 text-sm mt-0.5 line-clamp-2">
            {exercise.description}
          </p>
        </div>
      </div>

      {/* Current Progression Info */}
      {currentProgression && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-3 mb-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <p className="text-blue-300 text-xs font-semibold uppercase tracking-wide mb-0.5">
                📊 Current Level
              </p>
              <p className="text-white font-semibold">{currentProgression.name}</p>
              {currentProgression.description && (
                <p className="text-slate-300 text-xs mt-1">
                  {currentProgression.description}
                </p>
              )}
            </div>
            <div className="text-2xl">
              {currentProgression.level === 1 ? '🥋' :
               currentProgression.level === 2 ? '🥈' :
               currentProgression.level === 3 ? '🥇' : '⭐'}
            </div>
          </div>
        </div>
      )}

      {/* Sets Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-slate-300 text-sm font-semibold">Sets Progress</p>
          <span className="text-xs font-bold text-blue-300 bg-blue-500/20 px-2 py-1 rounded">
            {completedSets}/{totalSets}
          </span>
        </div>
        <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300"
            style={{ width: `${(completedSets / totalSets) * 100}%` }}
          />
        </div>
      </div>

      {/* Sets Grid */}
      <div className="space-y-2">
        {[1, 2, 3].map((setNumber) => {
          const setsArray = Array.isArray(workoutSets) ? workoutSets : [];
          const existingSet = setsArray.find((s) => s?.set_number === setNumber);
          const isExpanded = expandedSetIndex === setNumber - 1;
          const isCompleted = existingSet && existingSet.reps !== null;

          return (
            <div key={setNumber}>
              {/* Set Button/Header */}
              <button
                onClick={() =>
                  setExpandedSetIndex(isExpanded ? null : setNumber - 1)
                }
                className={`w-full p-4 rounded-xl font-semibold transition-all border-2 ${
                  isExpanded
                    ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white border-blue-400 shadow-lg shadow-blue-500/30'
                    : isCompleted
                      ? 'bg-gradient-to-r from-green-500/30 to-emerald-500/20 text-green-200 border-green-500/50 hover:border-green-400'
                      : 'bg-slate-700/50 text-slate-300 border-slate-600 hover:bg-slate-700 hover:border-slate-500'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 flex-1">
                    <span className="text-lg font-bold">
                      {setNumber === 3 ? '🔥' : '💪'}
                    </span>
                    <span>
                      {setNumber === 3 ? 'Drop Set' : `Set ${setNumber}`}
                    </span>
                  </div>
                  {isCompleted && existingSet && (
                    <span className="text-sm font-bold bg-white/20 px-3 py-1 rounded-full">
                      ✓ {existingSet.reps} reps
                    </span>
                  )}
                  <span className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                    ▼
                  </span>
                </div>
              </button>

              {/* Set Input (Expanded) */}
              {isExpanded && (
                <div className="mt-3 bg-gradient-to-b from-slate-700/80 to-slate-800/50 rounded-xl p-4 border border-slate-600 shadow-lg">
                  <div className="mb-3 pb-3 border-b border-slate-600">
                    <p className="text-slate-400 text-xs font-semibold uppercase tracking-wide">
                      Reps eingeben für Set {setNumber}
                    </p>
                  </div>
                  <SetInput
                    exercise={exercise}
                    setNumber={setNumber}
                    userProgression={userProgression}
                    existingSet={existingSet}
                    onCompleted={handleSetCompleted}
                    isDropSet={setNumber === 3}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Rest Timer Modal */}
      {showRestTimer && lastCompletedSetNumber && lastCompletedSetNumber < 3 && (
        <RestTimer
          onComplete={handleTimerComplete}
          setNumber={lastCompletedSetNumber + 1}
        />
      )}

      {/* Drop Set Modal */}
      {showDropSetModal && (
        <DropSetModal
          exercise={exercise}
          workoutSet={(Array.isArray(workoutSets) ? workoutSets : []).find((s) => s?.set_number === 3)}
          userProgression={userProgression}
          onClose={() => setShowDropSetModal(false)}
        />
      )}
    </div>
  );
}
