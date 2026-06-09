import { useState } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import { EXERCISE_INFO } from '../data/exerciseInfo';

export default function ExercisesView() {
  const [infoModal, setInfoModal] = useState(null);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);

  return (
    <>
      <div className="header">
        <div className="header-content">
          <div className="header-logo">COR<span>VIS</span></div>
        </div>
      </div>

      <div className="main-content">
        <p className="exercises-header-label">— Deine Progressionen</p>

        {exercises.map(exercise => {
          const userProg = userProgressions[String(exercise.id)];
          const currentProg = userProg?.current_progression;
          const sessionsAtTarget = userProg?.sessions_at_target || 0;
          const sessionsRequired = currentProg?.sessions_required || 3;
          const totalLevels = exercise.progressions?.length || 1;
          const progressPct = currentProg ? ((currentProg.level - 1) / (totalLevels - 1)) * 100 : 0;

          return (
            <div key={exercise.id} className="exercise-block">
              <p className="exercise-block-title">{exercise.name}</p>
              <p className="exercise-block-meta">
                Level {currentProg?.level ?? '—'} · {sessionsAtTarget}/{sessionsRequired} Sessions
              </p>
              <div className="exercise-progress-bar-wrap">
                <div className="exercise-progress-bar-fill" style={{ width: `${progressPct}%` }} />
              </div>

              <div className="exercise-ladder">
                {exercise.progressions?.map(prog => {
                  let status = 'future';
                  if (prog.level < (currentProg?.level || 0)) status = 'completed';
                  else if (prog.level === currentProg?.level) status = 'current';

                  return (
                    <div key={prog.id} className={`exercise-ladder-item ${status}`}>
                      <span className="ladder-level">{prog.level}</span>
                      <span className="ladder-name">{prog.name}</span>
                      <span className="ladder-status">
                        {status === 'completed' ? '✓' : status === 'current' ? '●' : ''}
                      </span>
                      {EXERCISE_INFO[prog.name] && (
                        <button
                          className="exercise-info-btn"
                          onClick={() => setInfoModal(prog.name)}
                        >
                          INFO
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {infoModal && EXERCISE_INFO[infoModal] && (
        <div className="modal-overlay" onClick={() => setInfoModal(null)}>
          <div className="info-modal-box" onClick={e => e.stopPropagation()}>
            <p className="info-modal-title">{infoModal}</p>
            <p className="info-modal-desc">{EXERCISE_INFO[infoModal].desc}</p>
            <a
              href={EXERCISE_INFO[infoModal].youtube}
              target="_blank"
              rel="noopener noreferrer"
              className="info-modal-link"
            >
              YouTube ansehen →
            </a>
            <button className="info-modal-close" onClick={() => setInfoModal(null)}>
              Schließen
            </button>
          </div>
        </div>
      )}
    </>
  );
}
