import { useState } from 'react';

export default function ProgressionModal({ upgrades, downgrades, onClose }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const allItems = [
    ...upgrades.map(u => ({ ...u, type: 'upgrade' })),
    ...downgrades.map(d => ({ ...d, type: 'downgrade' }))
  ];

  // If no items, show completion message and close
  if (allItems.length === 0) {
    return (
      <div className="fixed inset-0 bg-black/80 flex items-center justify-center">
        <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full mx-4 text-center space-y-6 border border-slate-700">
          <div className="text-6xl">💯</div>
          <h2 className="text-2xl font-bold text-emerald-400">Workout Complete!</h2>
          <p className="text-slate-100 text-lg">
            Great effort! You're on track with your progression.
          </p>
          <button
            onClick={onClose}
            className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-lg"
          >
            Done
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

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center">
      <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full mx-4 text-center space-y-6 border border-slate-700">
        {currentItem.type === 'upgrade' ? (
          <>
            <div className="text-6xl">🎉</div>
            <h2 className="text-2xl font-bold text-emerald-400">LEVEL UP!</h2>
            <p className="text-slate-100 text-lg">
              You've mastered <span className="font-bold">{currentItem.exercise}</span>!
            </p>
          </>
        ) : (
          <>
            <div className="text-6xl">💪</div>
            <h2 className="text-2xl font-bold text-blue-400">Keep Building Strength</h2>
            <p className="text-slate-100 text-lg">
              Let's master <span className="font-bold">{currentItem.exercise}</span> more before advancing.
            </p>
          </>
        )}

        <div className="bg-slate-700/50 rounded-lg p-4">
          <p className="text-slate-300">
            <span className="text-slate-400">Next:</span>
            <br />
            <span className="text-lg font-bold text-slate-100">
              {currentItem.to_progression}
            </span>
          </p>
        </div>

        <button
          onClick={handleNext}
          className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-lg"
        >
          {currentIndex < allItems.length - 1 ? 'Next' : 'Done'}
        </button>

        {allItems.length > 1 && (
          <p className="text-slate-400 text-sm">
            {currentIndex + 1} of {allItems.length}
          </p>
        )}
      </div>
    </div>
  );
}
