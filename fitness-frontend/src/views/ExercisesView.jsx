import { useState } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import { EXERCISE_INFO } from '../data/exerciseInfo';

export default function ExercisesView() {
  const [infoModal, setInfoModal] = useState(null);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);

  const renderExercise = (exercise, colorClass) => {
    const userProg = userProgressions[String(exercise.id)];
    const currentProg = userProg?.current_progression;
    const sessionsAtTarget = userProg?.sessions_at_target || 0;
    const sessionsRequired = currentProg?.sessions_required || 3;
    const nextProgLevel = (currentProg?.level || 0) + 1;
    const nextProg = exercise.progressions.find(p => p.level === nextProgLevel);

    return (
      <div key={exercise.id} className="exercise-section">
        <div className="exercise-header">
          <h2 className={`exercise-title ${colorClass}`}>{exercise.name}</h2>
        </div>

        {/* Progress Indicator */}
        <div className="exercise-progress-info">
          <span className="progress-label">Level {currentProg?.level || 0}</span>
          <span className="progress-sessions">{sessionsAtTarget}/{sessionsRequired} sessions</span>
        </div>

        {/* Progression Ladder */}
        <div className="exercise-ladder">
          {exercise.progressions.map(prog => {
            let status = 'future';
            let icon = prog.level;

            if (prog.level < currentProg?.level) {
              status = 'completed';
              icon = '✓';
            } else if (prog.level === currentProg?.level) {
              status = 'current';
              icon = '★';
            }

            return (
              <div
                key={prog.id}
                className={`exercise-ladder-item ${status}`}
              >
                <span className={`exercise-ladder-icon ${colorClass}`}>{icon}</span>
                <span className="exercise-ladder-name">{prog.name}</span>
                {EXERCISE_INFO[prog.name] && (
                  <button
                    className="exercise-info-btn"
                    onClick={() => setInfoModal(prog.name)}
                    title="View exercise details"
                  >
                    ℹ
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const pushExercise = exercises.find(e => e.name === 'Push-ups');
  const pullExercise = exercises.find(e => e.name === 'Pull-ups');
  const plankExercise = exercises.find(e => e.name === 'Planks');

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Calisthenics</h1>
        </div>
      </div>

      <div className="main-content">
        {pushExercise && renderExercise(pushExercise, 'exercise-push')}
        {pullExercise && renderExercise(pullExercise, 'exercise-pull')}
        {plankExercise && renderExercise(plankExercise, 'exercise-core')}
      </div>

      {/* Info Modal */}
      {infoModal && EXERCISE_INFO[infoModal] && (
        <div className="modal-overlay" onClick={() => setInfoModal(null)}>
          <div className="info-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setInfoModal(null)}>✕</button>
            <h2 className="info-modal-title">{infoModal}</h2>
            <p className="info-modal-desc">{EXERCISE_INFO[infoModal].desc}</p>
            <a
              href={EXERCISE_INFO[infoModal].youtube}
              target="_blank"
              rel="noopener noreferrer"
              className="info-modal-link"
            >
              Watch on YouTube →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
