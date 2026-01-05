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

  // Get current progression level
  const currentProgression = Array.isArray(exercise?.progressions)
    ? exercise.progressions.find((p) => p?.id === userProgression?.current_progression)
    : null;

  const handleSetCompleted = (setNumber) => {
    setLastCompletedSetNumber(setNumber);
    setExpandedSetIndex(null);

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

  return (
    <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700 hover:border-slate-600 transition-colors">
      {/* Exercise Header */}
      <div className="mb-4">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="text-lg font-bold text-white">{exercise.name}</h3>
            <p className="text-slate-400 text-sm mt-1">
              {exercise.description}
            </p>
          </div>
          <span className="bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full text-xs font-semibold">
            #{exerciseIndex + 1}
          </span>
        </div>

        {/* Current Progression */}
        {currentProgression && (
          <div className="bg-slate-700/50 rounded-lg p-3 mt-3">
            <p className="text-slate-400 text-xs mb-1">Current Level</p>
            <p className="text-white font-semibold">{currentProgression.name}</p>
            {currentProgression.description && (
              <p className="text-slate-300 text-xs mt-1">
                {currentProgression.description}
              </p>
            )}
          </div>
        )}
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
                className={`w-full p-3 rounded-lg font-semibold transition-all ${
                  isExpanded
                    ? 'bg-blue-600 text-white'
                    : isCompleted
                      ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>
                    {setNumber === 3 ? '🔥 Drop Set' : `Set ${setNumber}`}
                  </span>
                  {isCompleted && existingSet && <span>✓ {existingSet.reps} reps</span>}
                  <span className="text-slate-400">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>
              </button>

              {/* Set Input (Expanded) */}
              {isExpanded && (
                <div className="mt-2 bg-slate-700/50 rounded-lg p-4">
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
