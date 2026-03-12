import { useState, useEffect } from 'react';

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
      // Play sound and show notification
      playNotificationSound();
      showNotification('Rest time is over! Get ready for the next set.');
      
      // Auto-advance immediately
      const timeout = setTimeout(() => {
        onComplete();
      }, 500);
      return () => clearTimeout(timeout);
    }
  }, [timeLeft, isRunning, onComplete]);

  const formatTime = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = ((seconds - timeLeft) / seconds) * 100;

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
