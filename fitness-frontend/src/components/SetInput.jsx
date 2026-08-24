import { useState } from 'react';
import { MAX_REPS, nurZiffern } from '../utils/eingabe';

export default function SetInput({ setNumber, exerciseName, progressionName, onComplete, isSaving = false }) {
  const [reps, setReps] = useState('');
  const zuGross = reps !== '' && parseInt(reps, 10) > MAX_REPS;

  return (
    <div className="workout-input-wrap">
      <input
        className="workout-number-input"
        type="text"
        inputMode="numeric"
        pattern="[0-9]*"
        value={reps}
        onChange={e => setReps(nurZiffern(e.target.value))}
        autoFocus
        placeholder="0"
      />
      {zuGross && (
        <p className="eingabe-hinweis">Höchstens {MAX_REPS} Wiederholungen.</p>
      )}
      <button
        className="btn-done"
        onClick={() => onComplete(parseInt(reps, 10) || 0)}
        disabled={isSaving || !reps || zuGross}
      >
        {isSaving ? 'Speichere …' : 'Satz abschließen →'}
      </button>
    </div>
  );
}
