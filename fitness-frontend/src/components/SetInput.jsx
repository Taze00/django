import { useState } from 'react';

export default function SetInput({ setNumber, exerciseName, progressionName, lastTime, onComplete }) {
  const [reps, setReps] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onComplete(reps);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="workout-container">
      <div className="workout-bg-orb workout-bg-orb-1"></div>
      <div className="workout-bg-orb workout-bg-orb-2"></div>

      <div className="workout-card">
        <div className="badge" style={{ animation: 'slideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)' }}>
          Set {setNumber} of 3
        </div>

        <h2 className="workout-title">{exerciseName}</h2>
        <p className="workout-subtitle">{progressionName}</p>

        {lastTime && (
          <div className="info-card">
            <p className="info-label">Last Time</p>
            <p className="info-value">{lastTime}</p>
          </div>
        )}

        <div className="counter-display">
          <p className="counter-label">Reps Completed</p>
          <p className="counter-value">{reps}</p>
        </div>

        <div className="button-group">
          <button
            className="btn-large btn-minus"
            onClick={() => setReps(Math.max(0, reps - 1))}
            disabled={reps === 0}
          >
            −
          </button>
          <button
            className="btn-large btn-plus"
            onClick={() => setReps(reps + 1)}
          >
            +
          </button>
        </div>

        <p className="hint-text" style={{ marginBottom: '20px' }}>
          Stop at RIR 1-2 (1-2 reps in reserve)
        </p>

        <button
          className="btn-submit-workout"
          onClick={handleSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : 'Complete Set →'}
        </button>
      </div>
    </div>
  );
}
