import { useState } from 'react';

export default function SetInput({ setNumber, exerciseName, progressionName, onComplete, isSaving = false }) {
  const [reps, setReps] = useState('');

  return (
    <div className="workout-input-wrap">
      <input
        className="workout-number-input"
        type="number"
        inputMode="numeric"
        min="0"
        value={reps}
        onChange={e => setReps(e.target.value)}
        autoFocus
        placeholder="0"
      />
      <button
        className="btn-done"
        onClick={() => onComplete(parseInt(reps, 10) || 0)}
        disabled={isSaving || !reps || parseInt(reps, 10) < 0}
      >
        {isSaving ? 'Speichere …' : 'Satz abschließen →'}
      </button>
    </div>
  );
}
