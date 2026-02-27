import { useState } from 'react';
import SetInput from './SetInput';
import TimerInput from './TimerInput';
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
  const [showFormTips, setShowFormTips] = useState(false);

  if (!userProgression) {
    console.warn(`[ExerciseCard] No userProgression for exercise ${exercise?.id} (${exercise?.name})`);
  }

  const currentProgression = Array.isArray(exercise?.progressions)
    ? exercise.progressions.find((p) => p?.id === userProgression?.current_progression)
    : null;

  const handleSetCompleted = (setNumber, info = {}) => {
    setLastCompletedSetNumber(setNumber);
    setExpandedSetIndex(null);

    if (info.isUpdate) {
      console.log(`[ExerciseCard] Set ${setNumber} updated`);
      return;
    }

    if (setNumber < 3) {
      setShowRestTimer(true);
    } else if (setNumber === 3) {
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

  const completedSets = Array.isArray(workoutSets)
    ? workoutSets.filter(s => currentProgression?.target_type === 'time' ? s?.seconds !== null : s?.reps !== null).length
    : 0;

  if (!currentProgression) {
    return null;
  }

  const targetValue = currentProgression.target_value;
  const targetUnit = currentProgression.target_type === 'time' ? 's' : 'reps';

  // Get first 3 form cues only
  const formCuesShort = Array.isArray(currentProgression.form_cues)
    ? currentProgression.form_cues.slice(0, 3)
    : [];

  return (
    <div className="bg-slate-800/40 backdrop-blur-sm rounded-xl p-6 border border-slate-700/30 shadow-md">
      {/* Header - Exercise Name + Number */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500/40 flex items-center justify-center border border-blue-500/30 font-bold text-blue-300 text-sm">
            {exerciseIndex + 1}
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{currentProgression.name}</h3>
            <p className="text-slate-400 text-xs">Level {currentProgression.level}</p>
          </div>
        </div>
      </div>

      {/* Target Info - Minimal */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mb-6">
        <p className="text-slate-300 text-xs font-semibold tracking-wide mb-1">TARGET</p>
        <p className="text-white text-2xl font-bold">{targetValue} {targetUnit}</p>
        <p className="text-slate-400 text-xs mt-1">Set 1 & 2</p>
      </div>

      {/* Sets - Expandable */}
      <div className="space-y-3 mb-6">
        {[1, 2, 3].map((setNum) => {
          const set = workoutSets?.find(s => s.set_number === setNum && !s.is_drop_set);
          const isExpanded = expandedSetIndex === setNum - 1;
          const isCompleted = set && (set.reps || set.seconds);

          return (
            <div key={setNum}>
              {isExpanded ? (
                currentProgression.target_type === 'time' ? (
                  <TimerInput
                    exercise={exercise}
                    setNumber={setNum}
                    userProgression={userProgression}
                    existingSet={set}
                    onCompleted={handleSetCompleted}
                  />
                ) : (
                  <SetInput
                    exercise={exercise}
                    setNumber={setNum}
                    userProgression={userProgression}
                    existingSet={set}
                    onCompleted={handleSetCompleted}
                  />
                )
              ) : (
                <button
                  onClick={() => setExpandedSetIndex(setNum - 1)}
                  className={`w-full p-3 rounded-lg border transition-all text-left font-medium ${
                    isCompleted
                      ? 'bg-green-500/10 border-green-500/30 text-green-300 hover:bg-green-500/20'
                      : 'bg-slate-700/30 border-slate-600/30 text-slate-300 hover:bg-slate-700/50'
                  }`}
                >
                  {isCompleted ? `✓ Set ${setNum}` : `Set ${setNum}`}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Form Tips - Collapsed by default */}
      {formCuesShort.length > 0 && (
        <div>
          <button
            onClick={() => setShowFormTips(!showFormTips)}
            className="w-full flex items-center justify-between p-3 rounded-lg border border-slate-600/30 text-slate-300 hover:bg-slate-700/30 transition-all"
          >
            <span className="text-sm font-medium">💡 Form Tips</span>
            <span className="text-xs">{showFormTips ? '−' : '+'}</span>
          </button>

          {showFormTips && (
            <div className="mt-2 p-3 bg-slate-700/20 border border-slate-600/20 rounded-lg">
              <ul className="space-y-1.5">
                {formCuesShort.map((cue, i) => (
                  <li key={i} className="text-slate-300 text-xs flex gap-2">
                    <span className="text-green-400 flex-shrink-0">✓</span>
                    <span>{cue}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Rest Timer */}
      {showRestTimer && (
        <RestTimer onComplete={handleTimerComplete} restSeconds={180} />
      )}

      {/* Drop Set Modal */}
      {showDropSetModal && (
        <DropSetModal
          exercise={exercise}
          currentProgression={currentProgression}
          userProgression={userProgression}
          onClose={() => setShowDropSetModal(false)}
        />
      )}
    </div>
  );
}
