import { useState } from 'react';

export default function DropSetInstructions({ exercise, progressions, onComplete }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleComplete = async () => {
    setIsSubmitting(true);
    try {
      await onComplete();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-blue-900/20 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-0 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl animate-pulse-soft"></div>
      </div>

      <div className="w-full max-w-sm relative z-10">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <p className="text-4xl mb-3 animate-bounce">🔥</p>
          <h2 className="text-4xl font-bold text-slate-100 mb-2">
            DROP-SET
          </h2>
          <p className="text-slate-400 text-lg">Maximum effort until failure</p>
        </div>

        {/* Warning Card */}
        <div className="animate-slide-up mb-8 bg-gradient-to-br from-orange-600/30 to-orange-700/20 border-2 border-orange-500/50 rounded-2xl p-6 backdrop-blur-sm">
          <p className="text-orange-100 text-sm font-bold mb-2 flex items-center gap-2">
            <span className="text-xl">⚠️</span>
            NO REST between drops!
          </p>
          <p className="text-orange-200/80 text-xs leading-relaxed">
            Go immediately from one to the next until complete exhaustion. Don't hold back!
          </p>
        </div>

        {/* Progression Sequence */}
        <div className="space-y-3 mb-8">
          {progressions.map((prog, idx) => (
            <div
              key={prog.id}
              className="animate-slide-up bg-gradient-to-r from-slate-800/70 to-slate-900/70 border border-slate-600/30 rounded-2xl p-4 backdrop-blur-sm transform hover:scale-105 transition-transform duration-200"
              style={{ animationDelay: `${idx * 0.1}s` }}
            >
              <div className="flex items-start gap-4">
                <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0 text-white font-bold shadow-lg">
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <p className="text-slate-100 font-bold text-lg">{prog.name}</p>
                  {idx === 0 ? (
                    <p className="text-emerald-400 text-sm mt-1 font-semibold">▶ Start here</p>
                  ) : (
                    <p className="text-slate-400 text-sm mt-1">
                      ↓ Drop & continue to failure
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Complete Button */}
        <button
          onClick={handleComplete}
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
              <span>✓ Drop-Set Complete</span>
              <span className="group-hover:translate-x-1 transition-transform duration-200">→</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
