import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkoutStore } from '../stores/workoutStore';

export default function SetProgressionView() {
  const navigate = useNavigate();
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const [saving, setSaving] = useState(false);
  const [progressions, setProgressions] = useState({});

  useEffect(() => {
    // Initialize progressions state from store
    const initialProgressions = {};
    exercises.forEach(exercise => {
      const key = String(exercise.id);
      const prog = userProgressions[key];
      if (prog) {
        initialProgressions[key] = prog.current_progression;
      }
    });
    setProgressions(initialProgressions);
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
        await fetch(`/api/user-progressions/${update.exerciseId}/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({ current_progression: update.progression })
        });
      }

      // Refresh data
      const state = useWorkoutStore.getState();
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
            const prog = userProgressions[String(exercise.id)];
            if (!prog) return null;

            return (
              <div key={exercise.id} className="progression-setting-item">
                <div className="progression-setting-header">
                  <span className="progression-setting-icon">
                    {exercise.name === 'Push-ups' ? '🚀' : '🔥'}
                  </span>
                  <h3 className="progression-setting-name">{exercise.name}</h3>
                </div>

                <div className="progression-levels-grid">
                  {prog.progressions.map((progressionLevel, idx) => (
                    <button
                      key={idx}
                      className={`progression-level-btn ${progressions[String(exercise.id)] === progressionLevel.id ? 'active' : ''}`}
                      onClick={() => handleProgressionChange(exercise.id, progressionLevel.id)}
                      title={progressionLevel.name}
                    >
                      <p className="progression-level-number">Lvl {idx + 1}</p>
                      <p className="progression-level-name">{progressionLevel.name}</p>
                    </button>
                  ))}
                </div>

                <p className="progression-setting-current">
                  Current: {prog.progressions.find(p => p.id === progressions[String(exercise.id)])?.name || 'Not set'}
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
