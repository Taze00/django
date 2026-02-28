import { useState } from 'react';
import SetInput from './SetInput';
import TimerInput from './TimerInput';
import DropSetModal from './DropSetModal';

export default function ExerciseCard({
  exercise,
  setNumber = 1,
  progression,
  onSetCompleted = null,
}) {
  const [showDropSetModal, setShowDropSetModal] = useState(false);

  if (!exercise || !progression) {
    return null;
  }

  const handleSetCompleted = (completedSetNumber, info = {}) => {
    // If this is Set 3 and we have drop-set options, show drop-set modal
    if (completedSetNumber === 3 && progression?.level > 1 && !info.isUpdate) {
      setShowDropSetModal(true);
    } else if (onSetCompleted) {
      // Otherwise proceed to next step
      onSetCompleted();
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
              Level {progression.level}: {progression.name} • Set {setNumber} of 3
            </p>
          </div>
        </div>
      </div>

      {/* Set Input - Always Expanded */}
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

      {/* Drop Set Modal - Show after Set 3 if available */}
      {showDropSetModal && (
        <DropSetModal
          exercise={exercise}
          userProgression={{ current_progression: progression.id }}
          onClose={() => {
            setShowDropSetModal(false);
            if (onSetCompleted) {
              onSetCompleted();
            }
          }}
        />
      )}
    </div>
  );
}
