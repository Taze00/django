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
  const totalSets = 3;

  return (
    <div className="bg-slate-900/40 backdrop-blur-lg rounded-2xl p-5 border border-slate-700/50 hover:border-slate-600/70 transition-all duration-200 shadow-lg shadow-blue-500/5">
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

      {currentProgression && (
        <div className="bg-gradient-to-r from-blue-500/15 to-purple-500/15 backdrop-blur-sm border border-blue-500/30 rounded-xl p-4 mb-4">
          <div>
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-blue-300 text-xs font-semibold uppercase tracking-wide mb-1">
                  📊 Level {currentProgression.level}
                </p>
                <p className="text-white font-semibold text-lg">{currentProgression.name}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-green-300">
                  {userProgression?.sessions_at_target || 0}<span className="text-sm text-slate-400">/3</span>
                </p>
                <p className="text-xs text-slate-300">sessions</p>
              </div>
            </div>

            {currentProgression.description && (
              <p className="text-slate-300 text-sm mt-2">
                {currentProgression.description}
              </p>
            )}

            <div className="mt-3 pt-3 border-t border-blue-500/20 space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-semibold text-amber-300">🎯 Target:</span>
                <span className="font-bold text-white">
                  Set 1+2 each: {currentProgression.target_type === 'time'
                    ? `${currentProgression.target_value}s`
                    : `${currentProgression.target_value} reps`}
                </span>
              </div>

              {currentProgression.form_cues && currentProgression.form_cues.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-semibold text-amber-300 mb-1">✓ Form Cues:</p>
                  <div className="space-y-0.5">
                    {currentProgression.form_cues.slice(0, 3).map((cue, idx) => (
                      <p key={idx} className="text-xs text-slate-200">
                        {cue}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-slate-300 text-sm font-semibold">Sets Progress</p>
          <p className="text-slate-400 text-xs mt-1">{completedSets} of {totalSets} sets</p>
        </div>
      </div>

      <div className="space-y-2">
        {[1, 2, 3].map((setNumber) => {
          const setsArray = Array.isArray(workoutSets) ? workoutSets : [];
          const existingSet = setsArray.find((s) => s?.set_number === setNumber);
          const isExpanded = expandedSetIndex === setNumber - 1;
          const isCompleted = existingSet && (currentProgression?.target_type === 'time' ? existingSet.seconds !== null : existingSet.reps !== null);

          return (
            <div key={setNumber}>
              <button
                onClick={() =>
                  setExpandedSetIndex(isExpanded ? null : setNumber - 1)
                }
                className={`w-full p-4 rounded-xl font-semibold transition-all border-2 backdrop-blur-sm ${
                  isExpanded
                    ? 'bg-gradient-to-r from-blue-600/80 to-blue-500/80 text-white border-blue-300 shadow-lg shadow-blue-500/40'
                    : isCompleted
                      ? 'bg-gradient-to-r from-green-500/40 to-emerald-500/30 text-green-100 border-green-500/60 hover:from-green-500/50 hover:to-emerald-500/40 hover:border-green-400'
                      : 'bg-slate-700/30 text-slate-300 border-slate-600/50 hover:bg-slate-700/50 hover:border-slate-500/70'
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
                      ✓ {currentProgression?.target_type === 'time'
                        ? `${Math.floor(existingSet.seconds / 60)}:${(existingSet.seconds % 60).toString().padStart(2, '0')}`
                        : `${existingSet.reps}/${currentProgression?.target_value}`}
                    </span>
                  )}
                  <span className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                    ▼
                  </span>
                </div>
              </button>

              {isExpanded && (
                <div className="mt-3 bg-gradient-to-b from-slate-700/80 to-slate-800/50 rounded-xl p-4 border border-slate-600 shadow-lg">
                  <div className="mb-3 pb-3 border-b border-slate-600">
                    <p className="text-slate-400 text-xs font-semibold uppercase tracking-wide">
                      {setNumber < 3
                        ? `Set ${setNumber}${currentProgression?.target_type === 'time' ? ' - Hold Time' : ' - Enter Reps'}`
                        : 'Drop Set - Choose Drop Progression'}
                    </p>
                  </div>
                  {currentProgression?.target_type === 'time' ? (
                    <TimerInput
                      exercise={exercise}
                      setNumber={setNumber}
                      userProgression={userProgression}
                      existingSet={existingSet}
                      onCompleted={handleSetCompleted}
                      isDropSet={setNumber === 3}
                      currentProgression={currentProgression}
                    />
                  ) : (
                    <SetInput
                      exercise={exercise}
                      setNumber={setNumber}
                      userProgression={userProgression}
                      existingSet={existingSet}
                      onCompleted={handleSetCompleted}
                      isDropSet={setNumber === 3}
                      currentProgression={currentProgression}
                    />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {showRestTimer && lastCompletedSetNumber && lastCompletedSetNumber < 3 && (
        <RestTimer
          onComplete={handleTimerComplete}
          setNumber={lastCompletedSetNumber + 1}
        />
      )}

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
