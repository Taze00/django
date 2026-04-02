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
  const [selectedDays, setSelectedDays] = useState([1, 2, 3, 4, 5]); // Mon-Fri by default
  const [pushLevel, setPushLevel] = useState(3);
  const [pullLevel, setPullLevel] = useState(1);
  const [plankLevel, setPlankLevel] = useState(1);

  const weekDays = [
    { num: 1, name: 'Mon' },
    { num: 2, name: 'Tue' },
    { num: 3, name: 'Wed' },
    { num: 4, name: 'Thu' },
    { num: 5, name: 'Fri' },
    { num: 6, name: 'Sat' },
    { num: 7, name: 'Sun' },
  ];

  const pushOptions = [
    { level: 1, name: 'Wall Push-ups', desc: 'Level 1: Hands on wall, body straight. Easiest.' },
    { level: 2, name: 'Incline Push-ups', desc: 'Level 2: Hands on bench/table.' },
    { level: 3, name: 'Knee Push-ups', desc: 'Level 3: On your knees. Medium difficulty. Min 4-5 reps' },
    { level: 4, name: 'Standard Push-ups', desc: 'Level 4: Full body weight. Classic. Min 4-5 reps' },
    { level: 5, name: 'Diamond Push-ups', desc: 'Level 5: Hands close together. Hard on triceps. Min 4-5 reps' },
    { level: 6, name: 'Decline Push-ups', desc: 'Level 6: Feet elevated. Very hard. Min 4-5 reps' },
    { level: 7, name: 'Pseudo Planche', desc: 'Level 7: Advanced strength. Super hard. Min 4-5 reps' },
  ];

  const pullOptions = [
    { level: 1, name: 'Dead Hang', desc: 'Level 1: Just hang from the bar. Hold 10-15 seconds minimum' },
    { level: 2, name: 'Scapular Shrugs', desc: 'Level 2: Hang with shoulder engagement. 10+ reps' },
    { level: 3, name: 'Active Hang', desc: 'Level 3: Engaged hang. Hold 10-15 seconds' },
    { level: 4, name: 'Pull-up Negatives', desc: 'Level 4: Jump up, lower yourself. Min 1-2 controlled reps' },
    { level: 5, name: 'Band-Assisted Pull-ups', desc: 'Level 5: Use a resistance band. Min 1-2 reps' },
    { level: 6, name: 'Standard Pull-ups', desc: 'Level 6: Full pull-up. Min 1-2 reps' },
    { level: 7, name: 'Chest-to-Bar', desc: 'Level 7: Advanced pull-up. Min 1 rep' },
  ];

  const plankOptions = [
    { level: 1, name: 'Knee Plank', desc: 'Level 1: On your knees. Easier version. Hold 20-30 seconds' },
    { level: 2, name: 'Incline Plank', desc: 'Level 2: Hands on elevated surface. Hold 30-45 seconds' },
    { level: 3, name: 'Standard Plank', desc: 'Level 3: Full body weight, straight line. Hold 45-60 seconds' },
    { level: 4, name: 'Feet-Elevated Plank', desc: 'Level 4: Feet on bench. Hold 45-60 seconds' },
    { level: 5, name: 'Extended Plank', desc: 'Level 5: Arms extended forward. Hold 30-45 seconds' },
    { level: 6, name: 'RKC Plank', desc: 'Level 6: Maximum tension, shorter hold. Hold 20-30 seconds' },
    { level: 7, name: 'One-Arm Plank', desc: 'Level 7: Advanced strength. Hold 15-20 seconds' },
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
      setError('');
    }
  };

  const toggleDay = (dayNum) => {
    setSelectedDays(prev =>
      prev.includes(dayNum)
        ? prev.filter(d => d !== dayNum)
        : [...prev, dayNum].sort()
    );
  };

  const handleComplete = async () => {
    setIsLoading(true);
    setError('');

    try {
      console.log('=== Starting onboarding save ===');
      console.log('Push Level:', pushLevel);
      console.log('Pull Level:', pullLevel);
      console.log('Plank Level:', plankLevel);
      console.log('Selected Days:', selectedDays);

      // Step 1: Get all user progressions
      console.log('Step 1: Fetching user progressions...');
      const progressionsRes = await api.get('/user-progressions/');
      const progressions = progressionsRes.data.results || progressionsRes.data;
      
      console.log('Found progressions:', progressions);

      // Step 2: Find progression IDs by exercise
      const pushProg = progressions.find(p => p.exercise === 1); // Push-ups
      const pullProg = progressions.find(p => p.exercise === 2); // Pull-ups
      const plankProg = progressions.find(p => p.exercise === 3); // Planks

      console.log('Progression IDs:', { pushProg: pushProg?.id, pullProg: pullProg?.id, plankProg: plankProg?.id });

      if (!pushProg || !pullProg || !plankProg) {
        throw new Error('Could not find user progressions. Please refresh and try again.');
      }

      // Step 3: Update progressions
      console.log('Step 2: Updating progressions...');
      const updatePush = api.patch(`/user-progressions/${pushProg.id}/`, {
        current_progression: pushLevel,
        training_days: selectedDays,
      });
      
      const updatePull = api.patch(`/user-progressions/${pullProg.id}/`, {
        current_progression: pullLevel,
        training_days: selectedDays,
      });
      
      const updatePlank = api.patch(`/user-progressions/${plankProg.id}/`, {
        current_progression: plankLevel,
        training_days: selectedDays,
      });

      const results = await Promise.all([updatePush, updatePull, updatePlank]);
      console.log('Progressions updated:', results);

      // Step 4: Mark onboarding as complete
      console.log('Step 3: Marking onboarding as complete...');
      const completeResult = await api.post('/onboarding/complete/', {});
      console.log('Onboarding marked complete:', completeResult);

      // Step 5: Update auth store to reflect onboarding completion
      const currentUser = useAuthStore.getState().user;
      useAuthStore.setState(state => ({
        user: { ...state.user, onboarding_completed: true }
      }));

      console.log('=== Onboarding save successful! Navigating home... ===');
      
      // Step 6: Navigate to home
      setTimeout(() => navigate('/'), 500);
    } catch (err) {
      console.error('=== Onboarding error ===');
      console.error('Error:', err);
      console.error('Error response:', err.response?.data);
      console.error('Error status:', err.response?.status);
      
      const errorMsg = err.response?.data?.detail || 
                      err.response?.data?.error || 
                      err.message || 
                      'Failed to save onboarding. Please try again.';
      setError(errorMsg);
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
              Which days do you want to train?
            </p>
            <div className="onboarding-hint">
              💡 Click the days you want to train. Rest days are the ones you don't select. You can change this later in the app!
            </div>

            <div className="onboarding-days-grid">
              {weekDays.map((day) => (
                <button
                  key={day.num}
                  className={`onboarding-day-btn ${selectedDays.includes(day.num) ? 'active' : ''}`}
                  onClick={() => toggleDay(day.num)}
                >
                  {day.name}
                </button>
              ))}
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
              <button onClick={handlePrev} className="btn-onboarding-prev" disabled={isLoading}>← Back</button>
              <button 
                onClick={handleComplete} 
                className="btn-onboarding-complete"
                disabled={isLoading}
              >
                {isLoading ? 'Setting up...' : 'Complete Setup'}
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
