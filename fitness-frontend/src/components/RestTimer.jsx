import { useState, useEffect } from 'react';

export default function RestTimer({ seconds, nextExercise, setNumber, onComplete }) {
  const [timeLeft, setTimeLeft] = useState(seconds);
  const [isRunning, setIsRunning] = useState(true);

  useEffect(() => {
    if (!isRunning || timeLeft <= 0) return;

    const interval = setInterval(() => {
      setTimeLeft(t => t - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning, timeLeft]);

  useEffect(() => {
    if (timeLeft === 0 && isRunning) {
      setIsRunning(false);
    }
  }, [timeLeft, isRunning]);

  const formatTime = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = ((seconds - timeLeft) / seconds) * 100;

  return (
    <div className="rest-timer-overlay">
      <div className="rest-timer-modal">
        <h2 className="rest-timer-title">Rest time</h2>

        {/* Circular Progress Timer */}
        <div className="rest-timer-circle-container">
          <svg className="rest-timer-circle" viewBox="0 0 160 160">
            <circle
              cx="80"
              cy="80"
              r="70"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              style={{ color: '#1e293b' }}
            />
            <circle
              cx="80"
              cy="80"
              r="70"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              strokeDasharray={`${(progress / 100) * 440} 440`}
              style={{
                color: '#3b82f6',
                transition: 'stroke-dasharray 1s linear',
                transform: 'rotate(-90deg)',
                transformOrigin: 'center'
              }}
            />
          </svg>
          {/* Timer Text */}
          <div className="rest-timer-text">
            <p className="rest-timer-time">{formatTime(timeLeft)}</p>
            <p className="rest-timer-label">seconds</p>
          </div>
        </div>

        {/* Next Exercise */}
        <div className="info-card info-card-emerald" style={{ marginTop: '24px', marginBottom: '24px' }}>
          <p className="info-label">Next exercise</p>
          <p className="info-value">{nextExercise}</p>
        </div>

        {/* Control Buttons */}
        <div className="button-group">
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={isRunning ? 'btn-large btn-stop' : 'btn-large btn-play'}
          >
            {isRunning ? 'Pause' : 'Resume'}
          </button>
          <button
            onClick={onComplete}
            className="btn-large btn-plus"
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  );
}
