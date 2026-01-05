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
      <div className="bg-gradient-to-b from-slate-800 to-slate-900 border border-slate-700 rounded-2xl max-w-md w-full overflow-hidden">
        {/* Animated Header */}
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 px-6 py-8 text-center animate-pulse">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-3xl font-bold text-white">
            Progression Upgrade!
          </h2>
        </div>

        {/* Content */}
        <div className="px-6 py-8 space-y-6">
          {/* Exercise Name */}
          <div className="text-center">
            <p className="text-slate-400 text-sm mb-2">EXERCISE</p>
            <h3 className="text-2xl font-bold text-white">
              {currentUpgrade.exercise_name}
            </h3>
          </div>

          {/* Old vs New Progression */}
          <div className="space-y-4">
            {/* From */}
            <div>
              <p className="text-slate-400 text-xs mb-2">FROM</p>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-slate-300 font-semibold">
                  Level {currentUpgrade.old_progression.level}:{' '}
                  {currentUpgrade.old_progression.name}
                </p>
                {currentUpgrade.old_progression.description && (
                  <p className="text-slate-400 text-sm mt-1">
                    {currentUpgrade.old_progression.description}
                  </p>
                )}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center">
              <div className="text-3xl">⬇️</div>
            </div>

            {/* To */}
            <div>
              <p className="text-green-400 text-xs font-bold mb-2">TO (NEW!)</p>
              <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-3">
                <p className="text-green-300 font-bold text-lg">
                  Level {currentUpgrade.new_progression.level}:{' '}
                  {currentUpgrade.new_progression.name}
                </p>
                {currentUpgrade.new_progression.description && (
                  <p className="text-green-200 text-sm mt-1">
                    {currentUpgrade.new_progression.description}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-blue-400 text-xs font-semibold">LAST WORKOUTS</p>
                <p className="text-white text-2xl font-bold mt-1">
                  {currentUpgrade.qualifying_workouts}
                </p>
              </div>
              <div className="text-center">
                <p className="text-blue-400 text-xs font-semibold">AVG REPS</p>
                <p className="text-white text-2xl font-bold mt-1">
                  {currentUpgrade.average_reps.toFixed(1)}
                </p>
              </div>
            </div>
          </div>

          {/* Upgrade Count Indicator */}
          {upgrades.length > 1 && (
            <div className="text-center">
              <p className="text-slate-400 text-sm">
                {currentUpgradeIndex + 1} of {upgrades.length} upgrades
              </p>
              <div className="mt-2 flex gap-1 justify-center">
                {upgrades.map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-2 rounded-full transition-all ${
                      idx <= currentUpgradeIndex ? 'bg-green-500 w-4' : 'bg-slate-600 w-2'
                    }`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="border-t border-slate-700 px-6 py-4 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition-colors"
          >
            Skip
          </button>
          <button
            onClick={handleNext}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg font-bold transition-all active:scale-95"
          >
            {isLastUpgrade ? '🎉 Done!' : 'Next →'}
          </button>
        </div>
      </div>
    </div>
  );
}
