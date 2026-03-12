import { useState, useEffect } from 'react';

export default function TimerInput({ setNumber, exerciseName, progressionName, targetSeconds, lastTime, onComplete }) {
  const [seconds, setSeconds] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [countdownActive, setCountdownActive] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const isPullups = exerciseName === 'Pull-ups';

  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setSeconds(s => s + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning]);

  // Handle countdown before timer start
  const handleStartCountdown = () => {
    setCountdownActive(true);
    setCountdown(3);
  };

  useEffect(() => {
    if (!countdownActive || countdown <= 0) return;

    const interval = setInterval(() => {
      setCountdown(c => {
        if (c - 1 === 0) {
          setCountdownActive(false);
          setIsRunning(true);
        }
        return c - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [countdownActive, countdown]);

  const handleSubmit = async () => {
    setIsRunning(false);
    setIsSubmitting(true);
    try {
      await onComplete(seconds);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="workout-container">
      <div className="workout-bg-orb workout-bg-orb-1"></div>
      <div className="workout-bg-orb workout-bg-orb-2"></div>

      <div className="workout-card timer-card">
        <h2 className="workout-title">{exerciseName}</h2>
        <p className="workout-subtitle">{progressionName}</p>

        {/* Last Time Info */}
        {lastTime && (
          <div className="timer-info">
            <p className="timer-info-label">Last time</p>
            <p className="timer-info-value">{formatTime(lastTime)}</p>
          </div>
        )}

        {/* Timer Display */}
        <div className="timer-display-centered">
          <p className="timer-label">{countdownActive ? 'Get ready...' : 'Time'}</p>
          <p className="timer-main-value" style={{animation: countdownActive ? 'pulse 1s infinite' : undefined}}>
            {countdownActive ? countdown : formatTime(seconds)}
          </p>
        </div>

        {/* Control Buttons */}
        <div className="timer-button-group">
          <button
            onClick={() => !isRunning ? handleStartCountdown() : setIsRunning(!isRunning)}
            className={`timer-btn ${isRunning ? 'timer-btn-stop' : 'timer-btn-start'}`}
            disabled={countdownActive}
          >
            {isRunning ? '⏸' : '▶'}
          </button>
          <button
            onClick={() => {
              setSeconds(0);
              setCountdownActive(false);
              setCountdown(3);
              setIsRunning(false);
            }}
            className="timer-btn timer-btn-reset"
          >
            ↻
          </button>
        </div>

        <button className="btn-submit-workout" onClick={handleSubmit} disabled={isSubmitting || seconds === 0}>
          {isSubmitting ? 'Saving...' : 'Complete Set'}
        </button>
      </div>
    </div>
  );
}
