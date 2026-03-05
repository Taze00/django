import { useState } from 'react';

export default function ProgressionModal({ upgrades, downgrades, onClose }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const allItems = [
    ...upgrades.map(u => ({ ...u, type: 'upgrade' })),
    ...downgrades.map(d => ({ ...d, type: 'downgrade' }))
  ];

  if (allItems.length === 0) {
    return (
      <div className="progression-complete">
        <div className="progression-complete-card">
          <div className="progression-complete-emoji">💯</div>
          <h1 className="progression-complete-title">Workout Complete!</h1>
          <p className="progression-complete-subtitle">Great effort! You're on track with your progression.</p>
          <button className="progression-complete-btn" onClick={onClose}>Back to Home</button>
        </div>
      </div>
    );
  }

  const currentItem = allItems[currentIndex];
  const isUpgrade = currentItem.type === 'upgrade';
  const isMaxLevel = currentItem.is_max_level;
  
  const handleNext = () => {
    if (currentIndex < allItems.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      onClose();
    }
  };

  return (
    <div className="progression-complete">
      <div className="progression-complete-card">
        {isMaxLevel ? (
          <>
            <div className="progression-complete-emoji">👑</div>
            <h1 className="progression-complete-title">MASTERED!</h1>
            <p className="progression-complete-subtitle">You've reached the peak with {currentItem.exercise}!</p>
          </>
        ) : isUpgrade ? (
          <>
            <div className="progression-complete-emoji">🎉</div>
            <h1 className="progression-complete-title">LEVEL UP!</h1>
            <p className="progression-complete-subtitle">You've mastered {currentItem.exercise}!</p>
            <div className="progression-info">
              <p className="progression-label">Next Level</p>
              <p className="progression-value">{currentItem.to_progression}</p>
            </div>
          </>
        ) : (
          <>
            <div className="progression-complete-emoji">💪</div>
            <h1 className="progression-complete-title">Keep Building</h1>
            <p className="progression-complete-subtitle">Let's master {currentItem.exercise} more!</p>
            <div className="progression-info">
              <p className="progression-label">Current Level</p>
              <p className="progression-value">{currentItem.to_progression}</p>
            </div>
          </>
        )}
        
        <button className="progression-complete-btn" onClick={handleNext}>
          {currentIndex < allItems.length - 1 ? 'Next' : 'Done'}
        </button>

        {allItems.length > 1 && (
          <p className="progression-counter">{currentIndex + 1}/{allItems.length}</p>
        )}
      </div>
    </div>
  );
}
