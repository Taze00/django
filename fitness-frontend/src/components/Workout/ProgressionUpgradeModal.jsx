import { useState } from 'react';

export default function ProgressionUpgradeModal({ upgrades, onClose }) {
  const [currentUpgradeIndex, setCurrentUpgradeIndex] = useState(0);

  if (!upgrades || upgrades.length === 0) {
    return null;
  }

  const currentUpgrade = upgrades[currentUpgradeIndex];
  const isLastUpgrade = currentUpgradeIndex === upgrades.length - 1;

  const handleNext = () => {
    if (!isLastUpgrade) {
      setCurrentUpgradeIndex((prev) => prev + 1);
    } else {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-b from-slate-800 to-slate-900 border border-slate-700 rounded-2xl max-w-sm w-full overflow-hidden">
        {/* Header - Compact */}
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 px-6 py-4 text-center">
          <div className="text-4xl mb-2">🎉</div>
          <h2 className="text-2xl font-bold text-white">
            Upgrade!
          </h2>
        </div>

        {/* Content - Compact */}
        <div className="px-6 py-5 space-y-4">
          {/* Exercise Name */}
          <div className="text-center">
            <p className="text-slate-400 text-xs mb-1">EXERCISE</p>
            <h3 className="text-lg font-bold text-white">
              {currentUpgrade.exercise_name}
            </h3>
          </div>

          {/* Old vs New Progression */}
          <div className="space-y-3">
            {/* From */}
            <div>
              <p className="text-slate-400 text-xs mb-1">FROM</p>
              <div className="bg-slate-700/50 rounded-lg p-2">
                <p className="text-slate-300 text-sm font-semibold">
                  {currentUpgrade.old_progression.name}
                </p>
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center">
              <div className="text-2xl">⬇️</div>
            </div>

            {/* To */}
            <div>
              <p className="text-green-400 text-xs font-bold mb-1">TO (NEW!)</p>
              <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-2">
                <p className="text-green-300 font-bold text-sm">
                  {currentUpgrade.new_progression.name}
                </p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex gap-2 text-xs pt-2">
            <span className="text-slate-400">
              {currentUpgradeIndex + 1} / {upgrades.length}
            </span>
          </div>
        </div>

        {/* Button */}
        <div className="bg-slate-700 px-6 py-3 border-t border-slate-600">
          <button
            onClick={handleNext}
            className="w-full px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-bold rounded-lg transition-all text-sm"
          >
            {isLastUpgrade ? 'Done!' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}
