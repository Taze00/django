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

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-blue-900/20 flex flex-col items-center justify-center p-4 relative">
      {/* Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-10 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl animate-pulse-soft"></div>
      </div>

      <div className="w-full max-w-sm relative z-10">
        {/* Set Counter Badge */}
        <div className="mb-8 inline-block mx-auto">
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-2 rounded-full font-bold text-sm">
            Set {setNumber} of 3
          </div>
        </div>

        {/* Exercise Info */}
        <div className="text-center mb-10 animate-fade-in">
          <h2 className="text-5xl font-black text-slate-100 mb-3">{exerciseName}</h2>
          <p className="text-lg text-emerald-400 font-bold">{progressionName}</p>
        </div>

        {/* Last Time Card */}
        {lastTime && (
          <div className="mb-8 animate-slide-up p-6 bg-blue-600/20 border border-blue-500/30 rounded-2xl text-center backdrop-blur-sm">
            <p className="text-slate-400 text-sm font-medium mb-2">Last Time</p>
            <p className="text-3xl font-black text-blue-300">{lastTime}</p>
            <p className="text-slate-400 text-xs font-medium mt-1">reps</p>
          </div>
        )}

        {/* Counter */}
        <div className="animate-scale-in mb-8 bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 rounded-3xl p-10 backdrop-blur-sm">
          <div className="text-center mb-10">
            <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4">Reps Completed</p>
            <p className="text-8xl font-black text-transparent bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text">
              {reps}
            </p>
          </div>

          {/* Buttons */}
          <div className="flex gap-4 justify-center mb-8">
            <button
              onClick={() => setReps(Math.max(0, reps - 1))}
              disabled={reps === 0}
              className="w-24 h-24 bg-slate-700/50 hover:bg-slate-600/70 disabled:bg-slate-800/30 disabled:text-slate-500 text-slate-100 text-4xl font-bold rounded-2xl transition-all duration-200 active:scale-95 disabled:cursor-not-allowed"
            >
              −
            </button>
            <button
              onClick={() => setReps(reps + 1)}
              className="w-24 h-24 bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-4xl font-bold rounded-2xl transition-all duration-200 shadow-lg hover:shadow-glow-blue active:scale-95"
            >
              +
            </button>
          </div>

          <p className="text-center text-slate-400 text-xs font-medium uppercase tracking-wider">
            Stop at RIR 1-2 (1-2 reps left in reserve)
          </p>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="w-full py-4 px-6 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold rounded-2xl text-lg shadow-lg hover:shadow-glow transition-all duration-300 transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <span className="animate-spin">⏳</span>
              Saving...
            </>
          ) : (
            <>
              <span>Complete Set</span>
              <span>→</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
