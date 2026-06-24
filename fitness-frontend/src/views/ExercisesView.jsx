import { useState } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import { EXERCISE_INFO } from '../data/exerciseInfo';

const PROGRESSION_EXPLANATION =
  'Schaffst du deine Sätze in mehreren Trainings hintereinander sauber, steigst du eine Stufe auf. ' +
  'Schaffst du sie deutlich nicht, passt CORVIS dein Level wieder an — damit du immer auf dem Level ' +
  'trainierst, das zu dir passt.';

function sessionText(at, required) {
  if (at === 0) return 'Stark trainieren, um aufzusteigen';
  if (at >= required - 1) return 'Noch ein starkes Training';
  return 'Auf gutem Weg zum nächsten Level';
}

export default function ExercisesView() {
  const [infoModal, setInfoModal] = useState(null);
  const [openInfo, setOpenInfo] = useState(null); // exercise id with open info panel
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
          const isInfoOpen = openInfo === exercise.id;

          return (
            <div key={exercise.id} className="exercise-block">
              <p className="exercise-block-title">{exercise.name}</p>
              <p className="exercise-block-meta">
                Level {currentProg?.level ?? '—'}
              </p>

              <div className="exercise-session-row">
                <div className="exercise-session-dots">
                  {Array.from({ length: sessionsRequired }).map((_, i) => (
                    <span
                      key={i}
                      className={`exercise-session-dot ${i < sessionsAtTarget ? 'filled' : ''}`}
                    />
                  ))}
                </div>
                <span className="exercise-session-text">
                  {sessionText(sessionsAtTarget, sessionsRequired)}
                </span>
                <button
                  className="exercise-info-toggle"
                  onClick={() => setOpenInfo(isInfoOpen ? null : exercise.id)}
                  aria-label="Wie funktioniert der Aufstieg?"
                >
                  ?
                </button>
              </div>

              {isInfoOpen && (
                <div className="exercise-info-panel">
                  {PROGRESSION_EXPLANATION}
                  <button
                    className="exercise-info-panel-close"
                    onClick={() => setOpenInfo(null)}
                  >
                    ✕
                  </button>
                </div>
              )}

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
