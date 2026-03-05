import { useState } from 'react';

export default function DropSetInstructions({ exercise, progressions, onComplete }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleComplete = async () => {
    setIsSubmitting(true);
    try {
      await onComplete();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="workout-container">
      <div className="workout-bg-orb workout-bg-orb-1"></div>
      <div className="workout-bg-orb workout-bg-orb-2"></div>

      <div className="workout-card">
        {/* Header */}
        <div className="drop-set-header" style={{ animation: 'fadeIn 0.5s ease-out' }}>
          <h2 className="workout-title" style={{ fontSize: '1.8rem' }}>🔥 DROP-SET 🔥</h2>
        </div>

        {/* Progression Sequence */}
        <div className="drop-set-sequence">
          {progressions.map((prog, idx) => (
            <div
              key={prog.id}
              className="drop-set-progression"
              style={{ animation: `slideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) ${idx * 0.1}s both` }}
            >
              <div className="drop-set-number">{idx + 1}</div>
              <div className="drop-set-info">
                <p className="drop-set-name">{prog.name}</p>
                {idx === 0 ? (
                  <p className="drop-set-start">▶ Start here</p>
                ) : (
                  <p className="drop-set-next">↓ Drop & continue to failure</p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Complete Button */}
        <button
          className="btn-submit-workout"
          onClick={handleComplete}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : 'Drop-Set Complete'}
        </button>
      </div>
    </div>
  );
}
