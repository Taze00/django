import { useState } from 'react';
import SetInput from './SetInput';
import TimerInput from './TimerInput';

export default function ExerciseCard({
  exercise,
  workoutSets,
  userProgression,
  exerciseIndex,
  onSetCompleted = null,
  setNumber = 1, // ← Which set number are we on (1, 2, or 3)
}) {
  const [expandedSetInput, setExpandedSetInput] = useState(true); // Always expanded in Phase 8
  const [showFormTips, setShowFormTips] = useState(false);

  if (!userProgression) {
    console.warn(`[ExerciseCard] No userProgression for exercise ${exercise?.id} (${exercise?.name})`);
    return null;
  }

  const currentProgression = Array.isArray(exercise?.progressions)
    ? exercise.progressions.find((p) => p?.id === userProgression?.current_progression)
    : null;

  if (!currentProgression) {
    return null;
  }

  // Find the set for this specific set number
  const existingSet = workoutSets?.find(
    (s) => s.set_number === setNumber && !s.is_drop_set
  );

  const handleSetCompleted = (completedSetNumber, info = {}) => {
    if (onSetCompleted) {
      onSetCompleted(completedSetNumber, info);
    }
  };

  const targetValue = currentProgression.target_value;
  const targetUnit = currentProgression.target_type === 'time' ? 's' : 'reps';

  // Get first 3 form cues only
  const formCuesShort = Array.isArray(currentProgression.form_cues)
    ? currentProgression.form_cues.slice(0, 3)
    : [];

  return (
    <div className="bg-slate-800/40 backdrop-blur-sm rounded-xl p-6 border border-slate-700/30 shadow-md">
      {/* Header - Exercise Name + Set Number */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500/40 flex items-center justify-center border border-blue-500/30 font-bold text-blue-300 text-sm">
            {exerciseIndex + 1}
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{currentProgression.name}</h3>
            <p className="text-slate-400 text-xs">
              Level {currentProgression.level} • Set {setNumber} of 3
            </p>
          </div>
        </div>
      </div>

      {/* Set Input - Always Expanded in Phase 8 */}
      <div className="mb-6">
        {currentProgression.target_type === 'time' ? (
          <TimerInput
            exercise={exercise}
            setNumber={setNumber}
            userProgression={userProgression}
            existingSet={existingSet}
            onCompleted={handleSetCompleted}
            isDropSet={false}
          />
        ) : (
          <SetInput
            exercise={exercise}
            setNumber={setNumber}
            userProgression={userProgression}
            existingSet={existingSet}
            onCompleted={handleSetCompleted}
            isDropSet={false}
          />
        )}
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
    </div>
  );
}
