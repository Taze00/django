import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkoutStore } from '../stores/workoutStore';

const DAY_FULL = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];

export default function TrainingDaysView() {
  const navigate = useNavigate();
  const trainingDays = useWorkoutStore(state => state.trainingDays);
  const updateTrainingDays = useWorkoutStore(state => state.updateTrainingDays);
  const [selectedDays, setSelectedDays] = useState(trainingDays);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => { setSelectedDays(trainingDays); }, [trainingDays]);

  const toggle = day => setSelectedDays(prev =>
    prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day].sort((a, b) => a - b)
  );

  const handleSave = async () => {
    if (selectedDays.length === 0) { setFeedback({ type: 'error', msg: 'Mindestens einen Tag auswählen.' }); return; }
    setSaving(true);
    try {
      await updateTrainingDays(selectedDays);
      setFeedback({ type: 'success', msg: 'Gespeichert!' });
      setTimeout(() => navigate('/profile'), 900);
    } catch {
      setFeedback({ type: 'error', msg: 'Speichern fehlgeschlagen.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <div className="header">
        <div className="header-content">
          <div className="header-logo">COR<span>VIS</span></div>
          <button className="header-close-btn" onClick={() => navigate('/profile')}>✕</button>
        </div>
      </div>

      <div className="main-content">
        {feedback && <div className={`feedback-bar ${feedback.type}`}>{feedback.msg}</div>}

        <p className="progression-desc">
          Wähle deine Trainingstage. An diesen Tagen wird der Kalender markiert.
        </p>

        <div className="days-grid">
          {DAY_FULL.map((name, idx) => {
            const dayNum = idx + 1;
            const isSelected = selectedDays.includes(dayNum);
            return (
              <button
                key={dayNum}
                className={`day-btn ${isSelected ? 'selected' : ''}`}
                onClick={() => toggle(dayNum)}
              >
                <span className="day-btn-name">{name}</span>
                <span className="day-btn-indicator" />
              </button>
            );
          })}
        </div>

        <p style={{ fontSize: '0.58rem', color: 'var(--muted)', letterSpacing: '0.3px', marginBottom: '1.5rem' }}>
          {selectedDays.length} von 7 Tagen · Empfehlung: 4–5 Tage
        </p>

        <button className="btn-save" onClick={handleSave} disabled={saving}>
          {saving ? 'Wird gespeichert...' : 'Speichern'}
        </button>
      </div>
    </>
  );
}
