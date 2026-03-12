import { useState, useEffect, useRef } from 'react';

export default function RestTimer({ seconds, nextExercise, setNumber, onComplete }) {
  const [timeLeft, setTimeLeft] = useState(seconds);
  const [isRunning, setIsRunning] = useState(true);
  const startTimeRef = useRef(Date.now());
  const totalSecondsRef = useRef(seconds);

  // Update timeLeft when seconds prop changes
  useEffect(() => {
    setTimeLeft(seconds);
    totalSecondsRef.current = seconds;
    startTimeRef.current = Date.now();
  }, [seconds]);

  useEffect(() => {
    if (!isRunning) return;

    // Use timestamp-based timing - works even if app pauses
    const checkTimer = () => {
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      const remaining = Math.max(0, totalSecondsRef.current - elapsed);
      
      setTimeLeft(remaining);

      if (remaining === 0) {
        setIsRunning(false);
        setTimeout(() => {
          onComplete();
        }, 500);
      } else if (remaining > 0) {
        // Check every 100ms for smooth updates
        setTimeout(checkTimer, 100);
      }
    };

    checkTimer();
  }, [isRunning, onComplete]);

  // When app comes back to focus, recalculate timer based on actual elapsed time
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden || !isRunning) return;
      
      // App is now visible - recalculate based on real elapsed time
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      const remaining = Math.max(0, totalSecondsRef.current - elapsed);
      
      setTimeLeft(remaining);
      
      // Auto-advance if time is up
      if (remaining === 0) {
        setIsRunning(false);
        setTimeout(() => {
          onComplete();
        }, 500);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isRunning, onComplete]);

  const formatTime = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = ((totalSecondsRef.current - timeLeft) / totalSecondsRef.current) * 100;

  return (
    <div className="rest-timer-overlay">
      <div className="rest-timer-modal">
        <h2 className="rest-timer-title">Rest</h2>

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
