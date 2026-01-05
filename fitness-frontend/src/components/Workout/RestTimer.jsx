import { useState, useEffect } from 'react';

const REST_DURATION = 90; // 90 seconds

export default function RestTimer({ onComplete, setNumber }) {
  const [timeRemaining, setTimeRemaining] = useState(REST_DURATION);
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    if (!isActive || timeRemaining === 0) {
      if (timeRemaining === 0) {
        onComplete();
      }
      return;
    }

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          setIsActive(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, timeRemaining, onComplete]);

  const progress = ((REST_DURATION - timeRemaining) / REST_DURATION) * 100;
  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-2xl p-8 border border-slate-700 text-center max-w-sm w-full mx-4">
        {/* Header */}
        <h2 className="text-2xl font-bold text-white mb-2">Rest Timer</h2>
        <p className="text-slate-400 mb-8">
          Prepare for <span className="text-white font-bold">Set {setNumber}</span>
        </p>

        {/* Timer Display */}
        <div className="relative w-40 h-40 mx-auto mb-8">
          {/* Progress Circle */}
          <svg className="w-full h-full -rotate-90" viewBox="0 0 200 200">
            <circle
              cx="100"
              cy="100"
              r="90"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
              className="text-slate-700"
            />
            <circle
              cx="100"
              cy="100"
              r="90"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
              strokeDasharray={`${2 * Math.PI * 90}`}
              strokeDashoffset={`${2 * Math.PI * 90 * (1 - progress / 100)}`}
              className="text-blue-500 transition-all"
            />
          </svg>

          {/* Time Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-5xl font-bold text-white font-mono">
              {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          <button
            onClick={() => setIsActive(!isActive)}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors"
          >
            {isActive ? '⏸ Pause' : '▶ Resume'}
          </button>
          <button
            onClick={onComplete}
            className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 px-4 rounded-lg transition-colors"
          >
            Skip
          </button>
        </div>

        {/* Auto-Complete Message */}
        {timeRemaining === 0 && (
          <p className="text-green-400 font-semibold mt-4 text-lg">
            ✓ Ready! Set {setNumber} is next
          </p>
        )}
      </div>
    </div>
  );
}
