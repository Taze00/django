import { useState, useEffect } from 'react';

export default function TimerInput({ setNumber, exerciseName, progressionName, targetSeconds, lastTime, onComplete }) {
  const [seconds, setSeconds] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setSeconds(s => s + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning]);

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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-blue-900/20 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl animate-pulse-soft"></div>
      </div>

      <div className="w-full max-w-sm relative z-10">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <p className="text-slate-400 text-sm font-semibold uppercase tracking-widest mb-3">Set {setNumber} of 3</p>
          <h2 className="text-4xl font-bold text-slate-100 mb-2">{exerciseName}</h2>
          <p className="text-lg text-emerald-400 font-semibold">{progressionName}</p>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-2 gap-4 mb-8 animate-slide-up">
          {targetSeconds && (
            <div className="bg-gradient-to-br from-emerald-600/20 to-emerald-700/10 border border-emerald-500/30 rounded-2xl p-4 text-center backdrop-blur-sm">
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">Target</p>
              <p className="text-2xl font-bold text-emerald-300">{targetSeconds}s</p>
            </div>
          )}
          {lastTime && (
            <div className="bg-gradient-to-br from-blue-600/20 to-blue-700/10 border border-blue-500/30 rounded-2xl p-4 text-center backdrop-blur-sm">
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">Last time</p>
              <p className="text-2xl font-bold text-blue-300">{formatTime(lastTime)}s</p>
            </div>
          )}
        </div>

        {/* Timer Display */}
        <div className="animate-scale-in bg-gradient-to-br from-slate-800/70 to-slate-900/70 border border-slate-600/30 rounded-3xl p-8 backdrop-blur-sm mb-8">
          <div className="text-center mb-8">
            <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-4">Time held</p>
            <p className="text-7xl font-black text-transparent bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text font-mono">
              {formatTime(seconds)}
            </p>
          </div>

          {/* Control Buttons */}
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`flex-1 py-3 font-bold rounded-xl transition-all duration-200 shadow-lg active:scale-95 ${
                isRunning
                  ? 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white hover:shadow-lg'
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white hover:shadow-glow-blue'
              }`}
            >
              {isRunning ? '⏸ Stop' : '▶ Start'}
            </button>
            <button
              onClick={() => setSeconds(0)}
              className="flex-1 py-3 bg-slate-700/60 hover:bg-slate-600/80 text-slate-100 font-bold rounded-xl transition-all duration-200 shadow-lg active:scale-95"
            >
              ↻ Reset
            </button>
          </div>
        </div>

        {/* Complete Button */}
        <button
          onClick={handleSubmit}
          disabled={isSubmitting || seconds === 0}
          className="w-full py-4 px-6 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold rounded-2xl text-lg shadow-lg hover:shadow-glow transition-all duration-300 transform hover:scale-105 active:scale-95 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
        >
          {isSubmitting ? (
            <>
              <span className="animate-spin">⏳</span>
              Saving...
            </>
          ) : (
            <>
              <span>Complete Set</span>
              <span className="group-hover:translate-x-1 transition-transform duration-200">→</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
