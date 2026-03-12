import { useState, useEffect, useRef } from 'react';

// Create audio context for notification sound
const playNotificationSound = () => {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const now = audioContext.currentTime;
    
    // Create a simple beep: 2 beeps
    const oscillator1 = audioContext.createOscillator();
    const gain1 = audioContext.createGain();
    
    oscillator1.connect(gain1);
    gain1.connect(audioContext.destination);
    
    oscillator1.frequency.value = 800;
    oscillator1.type = 'sine';
    
    gain1.gain.setValueAtTime(0.3, now);
    gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
    
    oscillator1.start(now);
    oscillator1.stop(now + 0.2);
    
    // Second beep
    const oscillator2 = audioContext.createOscillator();
    const gain2 = audioContext.createGain();
    
    oscillator2.connect(gain2);
    gain2.connect(audioContext.destination);
    
    oscillator2.frequency.value = 1000;
    oscillator2.type = 'sine';
    
    gain2.gain.setValueAtTime(0.3, now + 0.25);
    gain2.gain.exponentialRampToValueAtTime(0.01, now + 0.45);
    
    oscillator2.start(now + 0.25);
    oscillator2.stop(now + 0.45);
  } catch (e) {
    console.log('Audio notification not available');
  }
};

// Show browser notification
const showNotification = (message) => {
  if ('Notification' in window) {
    if (Notification.permission === 'granted') {
      new Notification('Rest Timer Complete', {
        body: message,
        icon: '🏋️'
      });
    }
  }
};

export default function RestTimer({ seconds, nextExercise, setNumber, onComplete }) {
  const [timeLeft, setTimeLeft] = useState(seconds);
  const [isRunning, setIsRunning] = useState(true);
  const startTimeRef = useRef(Date.now());
  const totalSecondsRef = useRef(seconds);
  const hasNotifiedRef = useRef(false);

  // Update timeLeft when seconds prop changes
  useEffect(() => {
    setTimeLeft(seconds);
    totalSecondsRef.current = seconds;
    startTimeRef.current = Date.now();
    hasNotifiedRef.current = false;
  }, [seconds]);

  useEffect(() => {
    if (!isRunning) return;

    // Use timestamp-based timing instead of intervals
    // This works even if tab is in background
    const checkTimer = () => {
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      const remaining = Math.max(0, totalSecondsRef.current - elapsed);
      
      setTimeLeft(remaining);

      if (remaining === 0 && !hasNotifiedRef.current) {
        hasNotifiedRef.current = true;
        setIsRunning(false);
        playNotificationSound();
        showNotification('Rest time is over! Get ready for the next set.');
        
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

  // Handle tab visibility change - when user comes back, check if time is up
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Tab is hidden - nothing to do
        return;
      }
      
      // Tab is now visible - check if timer finished while we were away
      if (!isRunning) return;
      
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      const remaining = Math.max(0, totalSecondsRef.current - elapsed);
      
      setTimeLeft(remaining);
      
      if (remaining === 0 && !hasNotifiedRef.current) {
        hasNotifiedRef.current = true;
        setIsRunning(false);
        playNotificationSound();
        showNotification('Rest time is over! Get ready for the next set.');
        
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

  useEffect(() => {
    // Request notification permission if not already granted
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

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
