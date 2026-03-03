import { useState } from 'react';

export default function ProgressionUpgradeModal({ upgrades, downgrades, onClose }) {
  const [phase, setPhase] = useState('upgrades');  // 'upgrades' | 'downgrades'
  const [currentIndex, setCurrentIndex] = useState(0);

  const activeItems = phase === 'upgrades' ? (upgrades || []) : (downgrades || []);
  const currentItem = activeItems[currentIndex];
  const isLastItem = currentIndex === activeItems.length - 1;

  if (!currentItem) {
    // No upgrades or downgrades to show
    return null;
  }

  const handleNext = () => {
    if (!isLastItem) {
      // Next item in current phase
      setCurrentIndex((prev) => prev + 1);
    } else if (phase === 'upgrades' && (downgrades?.length || 0) > 0) {
      // Switch to downgrades phase
      setPhase('downgrades');
      setCurrentIndex(0);
    } else {
      // All done
      onClose?.();
    }
  };

  const isUpgrade = phase === 'upgrades';

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-sm w-full overflow-hidden">
        {/* Header */}
        <div className={`px-6 py-4 text-center ${isUpgrade ? 'bg-green-600' : 'bg-blue-600'}`}>
          <div className="text-4xl mb-2">{isUpgrade ? '🎉' : '💪'}</div>
          <h2 className="text-2xl font-bold text-white">
            {isUpgrade ? 'Level Up!' : 'Keep Building Strength!'}
          </h2>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-4">
          {/* Exercise Name */}
          <div className="text-center">
            <p className="text-slate-400 text-xs mb-1">EXERCISE</p>
            <h3 className="text-lg font-bold text-white">
              {currentItem.exercise_name}
            </h3>
          </div>

          {isUpgrade ? (
            /* Upgrade view: old → new */
            <div className="space-y-3">
              <div>
                <p className="text-slate-400 text-xs mb-1">FROM</p>
                <div className="bg-slate-700/50 rounded-lg p-2">
                  <p className="text-slate-300 text-sm font-semibold">
                    {currentItem.old_progression.name}
                  </p>
                </div>
              </div>

              <div className="flex justify-center">
                <div className="text-2xl">⬇️</div>
              </div>

              <div>
                <p className="text-green-400 text-xs font-bold mb-1">NEW LEVEL</p>
                <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-2">
                  <p className="text-green-300 font-bold text-sm">
                    {currentItem.new_progression.name}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            /* Downgrade view: positive message */
            <div className="text-center space-y-2">
              <p className="text-slate-300 text-sm">
                Let's build more strength at the current level first!
              </p>
              <p className="text-blue-300 text-xs">
                You've got this! 💪
              </p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex gap-2 text-xs pt-2">
            <span className="text-slate-400">
              {currentIndex + 1} / {activeItems.length}
            </span>
          </div>
        </div>

        {/* Button */}
        <div className={`px-6 py-3 border-t ${isUpgrade ? 'bg-slate-700 border-slate-600' : 'bg-slate-700 border-slate-600'}`}>
          <button
            onClick={handleNext}
            className={`w-full px-4 py-2 text-white font-bold rounded-lg transition-all text-sm ${
              isUpgrade
                ? 'bg-green-600 hover:bg-green-500'
                : 'bg-blue-600 hover:bg-blue-500'
            }`}
          >
            {isLastItem && (phase === 'downgrades' || !downgrades?.length)
              ? 'Done!'
              : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}
