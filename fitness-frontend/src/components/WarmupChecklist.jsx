import { useState } from 'react';

export default function WarmupChecklist({ onComplete }) {
  const [checks, setChecks] = useState({
    wrists: false,
    shoulders: false,
    elbows: false,
    back: false,
    legs: false,
  });

  const handleToggle = (key) => {
    setChecks(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const allChecked = Object.values(checks).every(v => v === true);

  return (
    <div className="workout-container">
      <div className="workout-bg-orb workout-bg-orb-1"></div>
      <div className="workout-bg-orb workout-bg-orb-2"></div>

      <div className="workout-card">
        <h2 className="workout-title">Warm-up Checklist</h2>
        <p className="workout-subtitle">Make sure to warm up these areas</p>

        <div className="warmup-checklist">
          {[
            { key: 'wrists', label: 'Wrists', emoji: '🦗' },
            { key: 'shoulders', label: 'Shoulders', emoji: '💪' },
            { key: 'elbows', label: 'Elbows', emoji: '📐' },
            { key: 'back', label: 'Back', emoji: '🔙' },
            { key: 'legs', label: 'Legs', emoji: '🦵' },
          ].map(item => (
            <button
              key={item.key}
              className={`warmup-item ${checks[item.key] ? 'checked' : ''}`}
              onClick={() => handleToggle(item.key)}
            >
              <span className="warmup-emoji">{item.emoji}</span>
              <span className="warmup-label">{item.label}</span>
              <span className="warmup-checkbox">{checks[item.key] ? '✓' : ''}</span>
            </button>
          ))}
        </div>

        <button
          className="btn-submit-workout"
          onClick={() => onComplete(checks)}
          disabled={!allChecked}
        >
          {allChecked ? 'Start Workout' : 'Complete warm-up first'}
        </button>
      </div>
    </div>
  );
}
