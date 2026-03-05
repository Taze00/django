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

  const getModalStyle = () => {
    if (currentItem.is_max_level) {
      return {
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%)',
        border: 'rgba(59, 130, 246, 0.3)'
      };
    }
    if (currentItem.type === 'upgrade') {
      return {
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)',
        border: 'rgba(16, 185, 129, 0.3)'
      };
    }
    return {
      background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%)',
      border: 'rgba(59, 130, 246, 0.3)'
    };
  };

  const modalStyle = getModalStyle();

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
      <div
        className="rounded-2xl p-8 max-w-sm w-full text-center space-y-6 border shadow-2xl"
        style={{ background: modalStyle.background, borderColor: modalStyle.border }}
      >
        {/* Header */}
        {currentItem.is_max_level ? (
          <>
            <div className="text-7xl animate-bounce">👑</div>
            <div>
              <h2 className="text-3xl font-bold text-yellow-400 mb-2">MASTERED!</h2>
              <p className="text-slate-100 text-base">
                You've reached the peak with <span className="font-bold text-yellow-300">{currentItem.exercise}</span>!
              </p>
            </div>
            <p className="text-emerald-400 font-semibold text-sm bg-emerald-500/10 rounded-lg p-3">
              {currentItem.message}
            </p>
          </>
        ) : currentItem.type === 'upgrade' ? (
          <>
            <div className="text-7xl animate-bounce">🎉</div>
            <div>
              <h2 className="text-3xl font-bold text-emerald-400 mb-2">LEVEL UP!</h2>
              <p className="text-slate-100 text-base">
                You've mastered <span className="font-bold text-emerald-300">{currentItem.exercise}</span>!
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="text-7xl animate-pulse">💪</div>
            <div>
              <h2 className="text-3xl font-bold text-blue-400 mb-2">Keep Building</h2>
              <p className="text-slate-100 text-base">
                Let's master <span className="font-bold text-blue-300">{currentItem.exercise}</span> more before advancing.
              </p>
            </div>
          </>
        )}

        {/* Transition Box */}
        {!currentItem.is_max_level && (
          <div className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/50">
            <p className="text-slate-400 text-xs uppercase tracking-wider mb-2">
              {currentItem.type === 'upgrade' ? '⬆️ Next Level' : '⬇️ Current Level'}
            </p>
            <p className="text-lg font-bold text-slate-100">
              {currentItem.to_progression}
            </p>
            {currentItem.type === 'upgrade' && (
              <p className="text-xs text-emerald-400 mt-2">
                New Target: {currentItem.to_target || 'Standard'}
              </p>
            )}
          </div>
        )}

        {/* Button */}
        <button
          onClick={handleNext}
          className={`w-full py-3 font-bold rounded-lg transition-all ${
            currentItem.type === 'upgrade'
              ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white'
              : currentItem.type === 'downgrade'
              ? 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white'
              : 'bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-white'
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
