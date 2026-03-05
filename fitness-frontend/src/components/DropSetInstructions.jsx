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
          <p className="drop-set-emoji">🔥</p>
          <h2 className="workout-title" style={{ fontSize: '2.5rem' }}>DROP-SET</h2>
          <p className="workout-subtitle">Maximum effort until failure</p>
        </div>

        {/* Warning Card */}
        <div className="drop-set-warning" style={{ animation: 'slideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)' }}>
          <p className="drop-set-warning-title">
            <span>⚠️</span> NO REST between drops!
          </p>
          <p className="drop-set-warning-text">
            Go immediately from one to the next until complete exhaustion. Don't hold back!
          </p>
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
          {isSubmitting ? 'Saving...' : '✓ Drop-Set Complete →'}
        </button>
      </div>
    </div>
  );
}
