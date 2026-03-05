import { useState } from 'react';

export default function ProgressionModal({ upgrades, downgrades, onClose }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const allItems = [
    ...upgrades.map(u => ({ ...u, type: 'upgrade' })),
    ...downgrades.map(d => ({ ...d, type: 'downgrade' }))
  ];

  if (allItems.length === 0) {
    return (
      <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
        <div className="bg-gradient-to-b from-slate-800 to-slate-900 rounded-2xl p-8 max-w-sm w-full text-center space-y-6 border border-emerald-500/20 shadow-2xl">
          <div className="text-7xl animate-bounce">💯</div>
          <h2 className="text-3xl font-bold text-emerald-400">Workout Complete!</h2>
          <p className="text-slate-300 text-base">
            Great effort! You're on track with your progression.
          </p>
          <button
            onClick={onClose}
            className="w-full py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-bold rounded-lg transition-all"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const currentItem = allItems[currentIndex];
  
  const handleNext = () => {
    if (currentIndex < allItems.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      onClose();
    }
  };

  const isUpgrade = currentItem.type === 'upgrade';
  const isDowngrade = currentItem.type === 'downgrade';
  const isMaxLevel = currentItem.is_max_level;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
      <div className={`rounded-2xl p-8 max-w-sm w-full text-center space-y-6 border shadow-2xl backdrop-blur-sm ${
        isMaxLevel 
          ? 'bg-gradient-to-br from-yellow-950/40 to-yellow-900/20 border-yellow-500/30'
          : isUpgrade
          ? 'bg-gradient-to-br from-emerald-950/40 to-emerald-900/20 border-emerald-500/30'
          : 'bg-gradient-to-br from-blue-950/40 to-blue-900/20 border-blue-500/30'
      }`}>
        {/* Header */}
        {isMaxLevel ? (
          <>
            <div className="text-7xl animate-bounce">👑</div>
            <div>
              <h2 className="text-4xl font-bold text-yellow-400 mb-2">MASTERED!</h2>
              <p className="text-slate-100 text-base">
                You've reached the peak with <span className="font-bold text-yellow-300">{currentItem.exercise}</span>!
              </p>
            </div>
            <p className="text-emerald-300 font-semibold text-sm bg-emerald-500/20 rounded-lg p-3 border border-emerald-500/30">
              {currentItem.message}
            </p>
          </>
        ) : isUpgrade ? (
          <>
            <div className="text-7xl animate-bounce">🎉</div>
            <div>
              <h2 className="text-4xl font-bold text-emerald-400 mb-2">LEVEL UP!</h2>
              <p className="text-slate-100 text-base">
                You've mastered <span className="font-bold text-emerald-300">{currentItem.exercise}</span>!
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="text-7xl animate-pulse">💪</div>
            <div>
              <h2 className="text-4xl font-bold text-blue-400 mb-2">Keep Building</h2>
              <p className="text-slate-100 text-base">
                Let's master <span className="font-bold text-blue-300">{currentItem.exercise}</span> more before advancing.
              </p>
            </div>
          </>
        )}

        {/* Transition Box */}
        {!isMaxLevel && (
          <div className={`rounded-xl p-4 border ${
            isUpgrade
              ? 'bg-emerald-500/10 border-emerald-500/50'
              : 'bg-blue-500/10 border-blue-500/50'
          }`}>
            <p className={`text-xs uppercase tracking-wider mb-2 font-bold ${
              isUpgrade ? 'text-emerald-400' : 'text-blue-400'
            }`}>
              {isUpgrade ? '⬆️ Next Level' : '⬇️ Current Level'}
            </p>
            <p className="text-lg font-bold text-slate-100">
              {currentItem.to_progression}
            </p>
          </div>
        )}

        {/* Button */}
        <button
          onClick={handleNext}
          className={`w-full py-3 font-bold rounded-lg transition-all text-white ${
            isMaxLevel
              ? 'bg-gradient-to-r from-yellow-600 to-yellow-700 hover:from-yellow-700 hover:to-yellow-800'
              : isUpgrade
              ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800'
              : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800'
          }`}
        >
          {currentIndex < allItems.length - 1 ? 'Next' : 'Done'}
        </button>

        {/* Progress Indicator */}
        {allItems.length > 1 && (
          <div className="flex items-center justify-center gap-2 pt-2">
            <div className="flex gap-1">
              {allItems.map((_, idx) => (
                <div
                  key={idx}
                  className={`h-2 rounded-full transition-all ${
                    idx === currentIndex ? 'w-6 bg-emerald-500' : 'w-2 bg-slate-600'
                  }`}
                />
              ))}
            </div>
            <span className="text-xs text-slate-400 ml-2">
              {currentIndex + 1}/{allItems.length}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
