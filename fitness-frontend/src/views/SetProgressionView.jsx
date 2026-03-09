import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkoutStore } from '../stores/workoutStore';
import api from '../api';

export default function SetProgressionView() {
  const navigate = useNavigate();
  const exercises = useWorkoutStore(state => state.exercises) || [];
  const userProgressions = useWorkoutStore(state => state.userProgressions) || {};
  const [saving, setSaving] = useState(false);
  const [progressions, setProgressions] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [exerciseDetails, setExerciseDetails] = useState({});

  useEffect(() => {
    // Initialize progressions state from store
    if (exercises && exercises.length > 0) {
      const initialProgressions = {};
      const details = {};

      exercises.forEach(exercise => {
        const key = String(exercise.id);
        const prog = userProgressions[key];
        details[key] = exercise.progressions || [];
        
        if (prog) {
          initialProgressions[key] = prog.current_progression;
        }
      });
      
      setProgressions(initialProgressions);
      setExerciseDetails(details);
      setIsLoading(false);
    } else {
      setIsLoading(false);
    }
  }, [exercises, userProgressions]);

  const handleProgressionChange = (exerciseId, newProgression) => {
    setProgressions(prev => ({
      ...prev,
      [String(exerciseId)]: newProgression
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Save each progression
      const updates = [];
      exercises.forEach(exercise => {
        const key = String(exercise.id);
        const newProg = progressions[key];
        if (newProg && userProgressions[key]) {
          updates.push({
            exerciseId: exercise.id,
            progression: newProg
          });
        }
      });

      // Call API to update progressions
      for (const update of updates) {
        await api.patch(`/user-progressions/${update.exerciseId}/`, {
          current_progression: update.progression
        });
      }

      // Refresh data
      const state = useWorkoutStore.getState();
      useWorkoutStore.setState({ isInitialized: false });
      await state.initialize();
      
      alert('Progression levels updated successfully');
      navigate('/profile');
    } catch (error) {
      console.error('Error saving progressions:', error);
      alert('Failed to update progression levels');
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="home-container">
        <div className="header">
          <div className="header-content">
            <h1 className="header-title">Set Levels</h1>
          </div>
        </div>
        <div className="main-content" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <p style={{ color: '#94a3b8' }}>Loading exercises...</p>
        </div>
      </div>
    );
  }

  if (!exercises || exercises.length === 0) {
    return (
      <div className="home-container">
        <div className="header">
          <div className="header-content">
            <h1 className="header-title">Set Levels</h1>
            <button
              className="header-close-btn"
              onClick={() => navigate('/profile')}
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>
        <div className="main-content" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <p style={{ color: '#94a3b8' }}>No exercises found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Set Levels</h1>
          <button
            className="header-close-btn"
            onClick={() => navigate('/profile')}
            title="Close"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="main-content">
        <div className="progression-settings-card">
          <p className="progression-settings-desc">Choose your current level for each exercise</p>

          {exercises.map(exercise => {
            const key = String(exercise.id);
            const prog = userProgressions[key];
            const progressionsList = exerciseDetails[key] || exercise.progressions || [];
            
            if (!prog || !progressionsList || progressionsList.length === 0) {
              return null;
            }

            const currentProgId = progressions[key];
            const currentProgName = progressionsList.find(p => p.id === currentProgId)?.name || 'Not set';

            return (
              <div key={exercise.id} className="progression-setting-item">
                <div className="progression-setting-header">
                  <span className="progression-setting-icon">
                    {exercise.name === 'Push-ups' ? '🚀' : '🔥'}
                  </span>
                  <h3 className="progression-setting-name">{exercise.name}</h3>
                </div>

                <div className="progression-levels-grid">
                  {progressionsList.map((progressionLevel, idx) => (
                    <button
                      key={progressionLevel.id}
                      className={`progression-level-btn ${currentProgId === progressionLevel.id ? 'active' : ''}`}
                      onClick={() => handleProgressionChange(exercise.id, progressionLevel.id)}
                      title={progressionLevel.name}
                    >
                      <p className="progression-level-number">Lvl {idx + 1}</p>
                      <p className="progression-level-name">{progressionLevel.name}</p>
                    </button>
                  ))}
                </div>

                <p className="progression-setting-current">
                  Current: {currentProgName}
                </p>
              </div>
            );
          })}
        </div>

        <button
          className="progression-save-btn"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Levels'}
        </button>

        <p className="progression-setting-info">
          💡 You can always adjust your level later as your strength improves
        </p>
      </div>
    </div>
  );
}
