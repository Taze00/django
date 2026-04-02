import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import api from '../api';

export default function OnboardingView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Form state
  const [trainingDays, setTrainingDays] = useState(4);
  const [pushLevel, setPushLevel] = useState(3);
  const [pullLevel, setPullLevel] = useState(1);
  const [plankLevel, setPlankLevel] = useState(1);

  const pushOptions = [
    { level: 1, name: 'Wall Push-ups', desc: 'Hands on wall, body straight. Easiest.' },
    { level: 2, name: 'Incline Push-ups', desc: 'Hands on bench/table.' },
    { level: 3, name: 'Knee Push-ups', desc: 'On your knees. Medium difficulty. Min 4-5 reps' },
    { level: 4, name: 'Standard Push-ups', desc: 'Full body weight. Classic. Min 4-5 reps' },
    { level: 5, name: 'Diamond Push-ups', desc: 'Hands close together. Hard on triceps. Min 4-5 reps' },
    { level: 6, name: 'Decline Push-ups', desc: 'Feet elevated. Very hard. Min 4-5 reps' },
    { level: 7, name: 'Pseudo Planche', desc: 'Advanced strength. Super hard. Min 4-5 reps' },
  ];

  const pullOptions = [
    { level: 1, name: 'Dead Hang', desc: 'Just hang from the bar. Hold 10-15 seconds minimum' },
    { level: 2, name: 'Scapular Shrugs', desc: 'Hang with shoulder engagement. 10+ reps' },
    { level: 3, name: 'Active Hang', desc: 'Engaged hang. Hold 10-15 seconds' },
    { level: 4, name: 'Pull-up Negatives', desc: 'Jump up, lower yourself. Min 1-2 controlled reps' },
    { level: 5, name: 'Band-Assisted Pull-ups', desc: 'Use a resistance band. Min 1-2 reps' },
    { level: 6, name: 'Standard Pull-ups', desc: 'Full pull-up. Min 1-2 reps' },
    { level: 7, name: 'Chest-to-Bar', desc: 'Advanced pull-up. Min 1 rep' },
  ];

  const plankOptions = [
    { level: 1, name: 'Knee Plank', desc: 'On your knees. Easier version. Hold 20-30 seconds' },
    { level: 2, name: 'Incline Plank', desc: 'Hands on elevated surface. Hold 30-45 seconds' },
    { level: 3, name: 'Standard Plank', desc: 'Full body weight, straight line. Hold 45-60 seconds' },
    { level: 4, name: 'Feet-Elevated Plank', desc: 'Feet on bench. Hold 45-60 seconds' },
    { level: 5, name: 'Extended Plank', desc: 'Arms extended forward. Hold 30-45 seconds' },
    { level: 6, name: 'RKC Plank', desc: 'Maximum tension, shorter hold. Hold 20-30 seconds' },
    { level: 7, name: 'One-Arm Plank', desc: 'Advanced strength. Hold 15-20 seconds' },
  ];

  const handleNext = () => {
    if (currentStep < 6) {
      setCurrentStep(currentStep + 1);
      setError('');
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    setIsLoading(true);
    setError('');

    try {
      // Update user progressions
      await api.patch('/user-progressions/1/', {
        current_progression: pushLevel,
      });
      await api.patch('/user-progressions/2/', {
        current_progression: pullLevel,
      });
      await api.patch('/user-progressions/3/', {
        current_progression: plankLevel,
      });

      // Mark onboarding as complete
      await api.post('/onboarding/complete/', {});

      // Navigate to home
      navigate('/');
    } catch (err) {
      setError('Failed to save onboarding. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="onboarding-container">
      <div className="onboarding-bg-orb onboarding-bg-orb-1"></div>
      <div className="onboarding-bg-orb onboarding-bg-orb-2"></div>

      <div className="onboarding-card">
        {/* Step 1: Welcome */}
        {currentStep === 1 && (
          <>
            <h1 className="onboarding-title">Hey {user?.username}! 🎉</h1>
            <p className="onboarding-subtitle">Let's set up your training</p>
            <p className="onboarding-text">
              We'll ask about your current level so we can start you at the right difficulty.
            </p>
            <button onClick={handleNext} className="btn-onboarding-next">
              Let's Go →
            </button>
          </>
        )}

        {/* Step 2: Training Days */}
        {currentStep === 2 && (
          <>
            <h2 className="onboarding-step-title">Training Days 📅</h2>
            <p className="onboarding-question">
              How many days per week do you want to train?
            </p>
            <div className="onboarding-hint">
              💡 Most people train 4-5 days with rest days in between for better recovery.
              Pick what works for you!
            </div>

            <div className="onboarding-options">
              <label className="onboarding-radio">
                <input
                  type="radio"
                  value={3}
                  checked={trainingDays === 3}
                  onChange={(e) => setTrainingDays(Number(e.target.value))}
                />
                <span className="onboarding-label">3 days (minimum effective)</span>
              </label>
              <label className="onboarding-radio">
                <input
                  type="radio"
                  value={4}
                  checked={trainingDays === 4}
                  onChange={(e) => setTrainingDays(Number(e.target.value))}
                />
                <span className="onboarding-label">4 days <strong>(recommended)</strong></span>
              </label>
              <label className="onboarding-radio">
                <input
                  type="radio"
                  value={5}
                  checked={trainingDays === 5}
                  onChange={(e) => setTrainingDays(Number(e.target.value))}
                />
                <span className="onboarding-label">5 days (advanced)</span>
              </label>
            </div>

            <div className="onboarding-buttons">
              <button onClick={handlePrev} className="btn-onboarding-prev">← Back</button>
              <button onClick={handleNext} className="btn-onboarding-next">Next →</button>
            </div>
          </>
        )}

        {/* Step 3: Push-ups */}
        {currentStep === 3 && (
          <>
            <h2 className="onboarding-step-title">Push-ups Level 💪</h2>
            <p className="onboarding-question">
              Which push-up variation can you do?
            </p>
            <div className="onboarding-hint">
              💡 You should be able to do at least 4-5 reps to start at that level
            </div>

            <div className="onboarding-options">
              {pushOptions.map((opt) => (
                <label key={opt.level} className="onboarding-radio-card">
                  <input
                    type="radio"
                    value={opt.level}
                    checked={pushLevel === opt.level}
                    onChange={(e) => setPushLevel(Number(e.target.value))}
                  />
                  <div className="onboarding-option-content">
                    <span className="onboarding-option-name">{opt.name}</span>
                    <span className="onboarding-option-desc">{opt.desc}</span>
                  </div>
                </label>
              ))}
            </div>

            <div className="onboarding-buttons">
              <button onClick={handlePrev} className="btn-onboarding-prev">← Back</button>
              <button onClick={handleNext} className="btn-onboarding-next">Next →</button>
            </div>
          </>
        )}

        {/* Step 4: Pull-ups */}
        {currentStep === 4 && (
          <>
            <h2 className="onboarding-step-title">Pull-ups Level 🔥</h2>
            <p className="onboarding-question">
              What's your pull-up level?
            </p>
            <div className="onboarding-hint">
              💡 Pull-ups are harder than push-ups! Pick what you can do for at least 10-15 seconds or 1-2 good reps
            </div>

            <div className="onboarding-options">
              {pullOptions.map((opt) => (
                <label key={opt.level} className="onboarding-radio-card">
                  <input
                    type="radio"
                    value={opt.level}
                    checked={pullLevel === opt.level}
                    onChange={(e) => setPullLevel(Number(e.target.value))}
                  />
                  <div className="onboarding-option-content">
                    <span className="onboarding-option-name">{opt.name}</span>
                    <span className="onboarding-option-desc">{opt.desc}</span>
                  </div>
                </label>
              ))}
            </div>

            <div className="onboarding-buttons">
              <button onClick={handlePrev} className="btn-onboarding-prev">← Back</button>
              <button onClick={handleNext} className="btn-onboarding-next">Next →</button>
            </div>
          </>
        )}

        {/* Step 5: Planks */}
        {currentStep === 5 && (
          <>
            <h2 className="onboarding-step-title">Planks Level 💪</h2>
            <p className="onboarding-question">
              What's your plank level?
            </p>
            <div className="onboarding-hint">
              💡 For planks, we measure by TIME, not reps. Pick a level where you can hold 20-30 seconds
            </div>

            <div className="onboarding-options">
              {plankOptions.map((opt) => (
                <label key={opt.level} className="onboarding-radio-card">
                  <input
                    type="radio"
                    value={opt.level}
                    checked={plankLevel === opt.level}
                    onChange={(e) => setPlankLevel(Number(e.target.value))}
                  />
                  <div className="onboarding-option-content">
                    <span className="onboarding-option-name">{opt.name}</span>
                    <span className="onboarding-option-desc">{opt.desc}</span>
                  </div>
                </label>
              ))}
            </div>

            <div className="onboarding-buttons">
              <button onClick={handlePrev} className="btn-onboarding-prev">← Back</button>
              <button onClick={handleNext} className="btn-onboarding-next">Next →</button>
            </div>
          </>
        )}

        {/* Step 6: How It Works */}
        {currentStep === 6 && (
          <>
            <h2 className="onboarding-step-title">How It Works 📖</h2>
            <p className="onboarding-subtitle">Here's the system:</p>

            <div className="onboarding-how-it-works">
              <div className="onboarding-point">
                <span className="onboarding-check">✓</span>
                <span>3 exercises: Push • Pull • Core</span>
              </div>
              <div className="onboarding-point">
                <span className="onboarding-check">✓</span>
                <span>Your current level is your starting point</span>
              </div>
              <div className="onboarding-point">
                <span className="onboarding-check">✓</span>
                <span>After 3 perfect workouts, you level up automatically</span>
              </div>
              <div className="onboarding-point">
                <span className="onboarding-check">✓</span>
                <span>If a level is too hard, we'll adjust</span>
              </div>
              <div className="onboarding-point">
                <span className="onboarding-check">✓</span>
                <span>Rest 3 min between sets, 5 min after drop-sets</span>
              </div>
            </div>

            <p className="onboarding-final-text">
              "You don't track numbers—just do your best!"
            </p>

            {error && <div className="error-message">⚠️ {error}</div>}

            <div className="onboarding-buttons">
              <button onClick={handlePrev} className="btn-onboarding-prev">← Back</button>
              <button 
                onClick={handleComplete} 
                className="btn-onboarding-start"
                disabled={isLoading}
              >
                {isLoading ? 'Setting up...' : 'Start Your First Workout 🚀'}
              </button>
            </div>
          </>
        )}

        {/* Progress indicator */}
        <div className="onboarding-progress">
          <div className="onboarding-progress-bar">
            <div 
              className="onboarding-progress-fill" 
              style={{ width: `${(currentStep / 6) * 100}%` }}
            ></div>
          </div>
          <p className="onboarding-progress-text">Step {currentStep} of 6</p>
        </div>
      </div>
    </div>
  );
}
