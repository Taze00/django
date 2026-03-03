import SetInput from './SetInput';
import TimerInput from './TimerInput';
import DropSetInstructions from './DropSetInstructions';

export default function ExerciseCard({
  exercise,
  setNumber = 1,
  progression,
  onSetCompleted = null,
}) {
  if (!exercise || !progression) {
    return null;
  }

  // Set 3 is always the DROP-SET (no input, just instructions)
  if (setNumber === 3) {
    return (
      <div className="bg-slate-800/40 backdrop-blur-sm rounded-xl p-6 border border-slate-700/30 shadow-md">
        <DropSetInstructions
          exercise={exercise}
          progression={progression}
          onDone={() => onSetCompleted?.()}
        />
      </div>
    );
  }

  // Sets 1 and 2: normal input (reps or time)
  const handleSetCompleted = (setNum, data) => {
    if (onSetCompleted) {
      onSetCompleted(setNum, data);
    }
  };

  return (
    <div className="bg-slate-800/40 backdrop-blur-sm rounded-xl p-6 border border-slate-700/30 shadow-md">
      {/* Header - Exercise Name + Set Number */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div>
            <h3 className="text-lg font-bold text-white">{exercise.name}</h3>
            <p className="text-slate-400 text-xs">
              Level {progression.level}: {progression.name} • Set {setNumber}
            </p>
          </div>
        </div>
      </div>

      {/* Set Input - Reps or Timer */}
      <div className="mb-6">
        {progression.target_type === 'time' ? (
          <TimerInput
            exercise={exercise}
            setNumber={setNumber}
            userProgression={{ current_progression: progression.id }}
            onCompleted={handleSetCompleted}
            isDropSet={false}
          />
        ) : (
          <SetInput
            exercise={exercise}
            setNumber={setNumber}
            progression={progression}
            onCompleted={handleSetCompleted}
            isDropSet={false}
          />
        )}
      </div>
    </div>
  );
}
