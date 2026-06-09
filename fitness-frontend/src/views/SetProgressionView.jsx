import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkoutStore } from '../stores/workoutStore';
import api from '../api';

export default function SetProgressionView() {
  const navigate = useNavigate();
  const exercises = useWorkoutStore(state => state.exercises) || [];
  const userProgressions = useWorkoutStore(state => state.userProgressions) || {};
  const [selected, setSelected] = useState({});
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    if (exercises.length > 0) {
      const init = {};
      exercises.forEach(ex => {
        const prog = userProgressions[String(ex.id)];
        if (prog) init[String(ex.id)] = prog.current_progression?.id;
      });
      setSelected(init);
    }
  }, [exercises, userProgressions]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updates = exercises.filter(ex => {
        const key = String(ex.id);
        return selected[key] && selected[key] !== userProgressions[key]?.current_progression?.id;
      });

      if (updates.length === 0) {
        setFeedback({ type: 'info', msg: 'Keine Änderungen.' });
        setSaving(false);
        return;
      }

      for (const ex of updates) {
        await api.patch(`/user-progressions/${ex.id}/`, {
          current_progression: selected[String(ex.id)]
        });
      }

      useWorkoutStore.setState({ isInitialized: false });
      await useWorkoutStore.getState().initialize();
      setFeedback({ type: 'success', msg: 'Level gespeichert!' });
      setTimeout(() => navigate('/profile'), 1200);
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
        {feedback && (
          <div className={`feedback-bar ${feedback.type}`}>{feedback.msg}</div>
        )}

        <p className="progression-desc">
          Wähle dein aktuelles Level für jede Übung. Dieses Level wird im Dashboard und im Training verwendet.
        </p>

        {exercises.map(exercise => {
          const key = String(exercise.id);
          const progressions = exercise.progressions || [];
          const currentId = selected[key];
          const currentName = progressions.find(p => p.id === currentId)?.name || '—';

          return (
            <div key={exercise.id} className="progression-exercise-block">
              <p className="progression-exercise-title">{exercise.name}</p>
              <p className="progression-exercise-current">
                Aktuell: <span>{currentName}</span>
              </p>
              <div className="progression-levels">
                {progressions.map((prog, idx) => (
                  <button
                    key={prog.id}
                    className={`progression-level-btn ${currentId === prog.id ? 'active' : ''}`}
                    onClick={() => setSelected(prev => ({ ...prev, [key]: prog.id }))}
                  >
                    <span className="plvl-num">{idx + 1}</span>
                    <span className="plvl-name">{prog.name}</span>
                    {currentId === prog.id && <span className="plvl-check">●</span>}
                  </button>
                ))}
              </div>
            </div>
          );
        })}

        <button className="btn-save" onClick={handleSave} disabled={saving}>
          {saving ? 'Wird gespeichert...' : 'Level speichern'}
        </button>
      </div>
    </>
  );
}
