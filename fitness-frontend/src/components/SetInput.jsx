import { useState } from 'react';

export default function SetInput({ setNumber, exerciseName, progressionName, lastTime, onComplete }) {
  const [reps, setReps] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onComplete(reps);
    } finally {
      setIsSubmitting(false);
    }
  };

  const incrementReps = () => setReps(reps + 1);
  const decrementReps = () => setReps(Math.max(0, reps - 1));

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-blue-900/20 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse-soft"></div>
      </div>

      <div className="w-full max-w-sm relative z-10">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <p className="text-slate-400 text-sm font-semibold uppercase tracking-widest mb-3">Set {setNumber} of 3</p>
          <h2 className="text-4xl font-bold text-slate-100 mb-2">{exerciseName}</h2>
          <p className="text-lg text-emerald-400 font-semibold">{progressionName}</p>
        </div>

        {/* Last Time Card */}
        {lastTime && (
          <div className="mb-8 animate-slide-up bg-gradient-to-br from-blue-600/20 to-blue-700/10 border border-blue-500/30 rounded-2xl p-6 text-center backdrop-blur-sm">
            <p className="text-slate-400 text-sm mb-2">Last time</p>
            <p className="text-3xl font-bold text-blue-300">{lastTime} reps</p>
          </div>
        )}

        {/* Reps Counter */}
        <div className="animate-scale-in bg-gradient-to-br from-slate-800/70 to-slate-900/70 border border-slate-600/30 rounded-3xl p-8 backdrop-blur-sm mb-8">
          <div className="text-center mb-8">
            <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-4">Reps completed</p>
            <p className="text-7xl font-black text-transparent bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text">
              {reps}
            </p>
          </div>

          {/* Counter Buttons */}
          <div className="flex gap-4 justify-center mb-8">
            <button
              onClick={decrementReps}
              disabled={reps === 0}
              className="w-20 h-20 bg-slate-700/60 hover:bg-slate-600/80 disabled:bg-slate-800/40 disabled:text-slate-500 text-slate-100 text-3xl font-bold rounded-2xl transition-all duration-200 active:scale-95 disabled:cursor-not-allowed shadow-lg"
            >
              −
            </button>
            <button
              onClick={incrementReps}
              className="w-20 h-20 bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-3xl font-bold rounded-2xl transition-all duration-200 shadow-lg hover:shadow-glow-blue active:scale-95 transform"
            >
              +
            </button>
          </div>

          {/* Instructions */}
          <p className="text-center text-slate-400 text-xs font-medium uppercase tracking-wider">
            Stop when form breaks or 1-2 more reps possible
          </p>
        </div>

        {/* Complete Button */}
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="w-full py-4 px-6 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold rounded-2xl text-lg shadow-lg hover:shadow-glow transition-all duration-300 transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2 group"
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
