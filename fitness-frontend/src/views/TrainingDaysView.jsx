import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkoutStore } from '../stores/workoutStore';

export default function TrainingDaysView() {
  const navigate = useNavigate();
  const trainingDays = useWorkoutStore(state => state.trainingDays);
  const updateTrainingDays = useWorkoutStore(state => state.updateTrainingDays);
  const [selectedDays, setSelectedDays] = useState(trainingDays);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setSelectedDays(trainingDays);
  }, [trainingDays]);

  const handleToggleDay = (day) => {
    setSelectedDays(prev =>
      prev.includes(day)
        ? prev.filter(d => d !== day)
        : [...prev, day].sort((a, b) => a - b)
    );
  };

  const handleSave = async () => {
    if (selectedDays.length === 0) {
      alert('Please select at least one day to train');
      return;
    }

    setSaving(true);
    try {
      await updateTrainingDays(selectedDays);
      alert('Training days updated successfully');
      navigate('/profile');
    } catch (error) {
      alert('Failed to update training days');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Training Days</h1>
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
        <div className="training-days-card">
          <p className="training-days-desc">Select which days you want to train</p>

          <div className="week-grid-inline">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, idx) => {
              const dayNum = idx + 1;
              const isActive = selectedDays.includes(dayNum);
              return (
                <button
                  key={dayNum}
                  className={`week-day ${isActive ? 'active' : 'inactive'}`}
                  onClick={() => handleToggleDay(dayNum)}
                  title={`${isActive ? 'Remove' : 'Add'} ${day}`}
                >
                  <p className="week-day-name">{day}</p>
                  <p className="week-day-status">{isActive ? '✓' : '○'}</p>
                </button>
              );
            })}
          </div>

          <div className="training-days-info">
            <p className="training-days-count">
              {selectedDays.length} day{selectedDays.length !== 1 ? 's' : ''} selected
            </p>
            <p className="training-days-recommendation">
              💡 Recommended: 4-5 days per week for optimal recovery and progress
            </p>
          </div>
        </div>

        <button
          className="training-days-save-btn"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}
