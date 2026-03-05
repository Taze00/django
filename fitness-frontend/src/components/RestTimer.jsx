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
    <div className="fixed inset-0 bg-gradient-to-br from-black/80 to-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur-xl rounded-3xl p-8 max-w-md w-full mx-4 text-center space-y-6 border border-slate-700/50 shadow-2xl">
        <h2 className="text-3xl font-bold text-slate-100 uppercase tracking-wider">Rest time</h2>

        {/* Circular Progress Timer */}
        <div className="flex justify-center mb-4">
          <div className="relative w-48 h-48">
            {/* Progress Circle */}
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-slate-700"
              />
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeDasharray={`${(progress / 100) * 440} 440`}
                className="text-blue-400 transition-all duration-1000"
              />
            </svg>
            {/* Timer Text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-6xl font-black text-slate-100 font-mono">{formatTime(timeLeft)}</p>
              <p className="text-xs text-slate-400 uppercase tracking-widest mt-1">seconds</p>
            </div>
          </div>
        </div>

        {/* Next Exercise */}
        <div className="bg-gradient-to-r from-emerald-600/20 to-emerald-700/10 border border-emerald-500/30 rounded-2xl p-4 backdrop-blur-sm">
          <p className="text-slate-400 text-sm mb-1 uppercase tracking-wider">Next exercise</p>
          <p className="text-slate-100 font-bold text-xl">{nextExercise}</p>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-3 pt-2">
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`flex-1 py-3 font-bold rounded-xl transition-all duration-200 shadow-lg active:scale-95 ${
              isRunning
                ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
                : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white hover:shadow-glow-blue'
            }`}
          >
            {isRunning ? '⏸ Pause' : '▶ Resume'}
          </button>
          <button
            onClick={onComplete}
            className="flex-1 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 text-white font-bold rounded-xl transition-all duration-200 shadow-lg hover:shadow-glow active:scale-95"
          >
            ⏭ Skip
          </button>
        </div>
      </div>
    </div>
  );
}
