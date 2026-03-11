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

      <div className="workout-card">

        <h2 className="workout-title">{exerciseName}</h2>
        <p className="workout-subtitle">{progressionName}</p>

        {/* Info Cards */}
        <div className="info-grid" style={{ animation: 'slideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s both' }}>
          {targetSeconds && !isPullups && (
            <div className="info-card info-card-emerald">
              <p className="info-label">Target</p>
              <p className="info-value">{targetSeconds}s</p>
            </div>
          )}
          {lastTime && (
            <div className="info-card info-card-blue">
              <p className="info-label">Last time</p>
              <p className="info-value">{formatTime(lastTime)}</p>
            </div>
          )}
        </div>

        {/* Timer Display */}
        <div className="timer-display" style={{ animation: 'scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)' }}>
          <p className="counter-label">{countdownActive ? 'Get ready...' : 'Time held'}</p>
          <p className="timer-value" style={{
            fontSize: countdownActive ? '96px' : undefined,
            color: countdownActive ? '#3b82f6' : undefined,
            animation: countdownActive ? 'pulse 1s infinite' : undefined
          }}>
            {countdownActive ? countdown : formatTime(seconds)}
          </p>

          {/* Control Buttons */}
          <div className="button-group" style={{ marginTop: '24px' }}>
            <button
              onClick={() => !isRunning ? handleStartCountdown() : setIsRunning(!isRunning)}
              className={isRunning ? 'btn-large btn-stop' : 'btn-large btn-play'}
              disabled={countdownActive}
            >
              {isRunning ? '⏸ Pause' : '▶ Start'}
            </button>
            <button
              onClick={() => {
                setSeconds(0);
                setCountdownActive(false);
                setCountdown(3);
                setIsRunning(false);
              }}
              className="btn-large btn-reset"
            >
              ↻ Reset
            </button>
          </div>
        </div>

        <button
          className="btn-submit-workout"
          onClick={handleSubmit}
          disabled={isSubmitting || seconds === 0}
        >
          {isSubmitting ? 'Saving...' : 'Complete Set'}
        </button>
      </div>
    </div>
  );
}
