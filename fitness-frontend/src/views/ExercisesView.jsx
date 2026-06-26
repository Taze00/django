import { useState } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import { EXERCISE_INFO } from '../data/exerciseInfo';

export default function ExercisesView() {
  const [openAll, setOpenAll] = useState({});
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

          const progressions = exercise.progressions || [];
          const currentLevel = currentProg?.level ?? 1;
          const currentIdx = progressions.findIndex(p => p.level === currentLevel);
          const prevProg = currentIdx > 0 ? progressions[currentIdx - 1] : null;
          const currProg = currentIdx >= 0 ? progressions[currentIdx] : null;
          const nextProg = currentIdx >= 0 && currentIdx < progressions.length - 1
            ? progressions[currentIdx + 1] : null;
          const isExpanded = !!openAll[exercise.id];

          return (
            <div key={exercise.id} className="lib-block">
              <p className="lib-title">{exercise.name}</p>

              {prevProg && (
                <div className="lib-level-row lib-level-prev">
                  <span className="lib-num">{prevProg.level}</span>
                  <span className="lib-name">{prevProg.name}</span>
                  <span className="lib-badge">✓</span>
                </div>
              )}

              {currProg && (
                <div className="lib-level-row lib-level-current">
                  <span className="lib-num">{currProg.level}</span>
                  <span className="lib-name">{currProg.name}</span>
                  <div className="lib-dots">
                    {Array.from({ length: sessionsRequired }).map((_, i) => (
                      <span key={i} className={`lib-dot${i < sessionsAtTarget ? ' filled' : ''}`} />
                    ))}
                  </div>
                  {EXERCISE_INFO[currProg.name] && (
                    <button className="lib-info-btn" onClick={() => setInfoModal(currProg.name)}>
                      INFO
                    </button>
                  )}
                </div>
              )}

              {nextProg && (
                <div className="lib-level-row lib-level-next">
                  <span className="lib-num">{nextProg.level}</span>
                  <span className="lib-name">{nextProg.name}</span>
                  <span className="lib-badge">↑</span>
                </div>
              )}

              <button
                className="lib-expand-btn"
                onClick={() => setOpenAll(prev => ({ ...prev, [exercise.id]: !prev[exercise.id] }))}
              >
                {isExpanded ? '▲ Weniger anzeigen' : `Alle ${progressions.length} Stufen ›`}
              </button>

              {isExpanded && (
                <div className="lib-full-ladder">
                  {progressions.map(prog => {
                    let status = 'future';
                    if (prog.level < currentLevel) status = 'completed';
                    else if (prog.level === currentLevel) status = 'current';
                    return (
                      <div key={prog.id} className={`lib-ladder-item ${status}`}>
                        <span className="lib-ladder-num">{prog.level}</span>
                        <span className="lib-ladder-name">{prog.name}</span>
                        <span className="lib-ladder-status">
                          {status === 'completed' ? '✓' : status === 'current' ? '●' : ''}
                        </span>
                        {EXERCISE_INFO[prog.name] && (
                          <button className="lib-info-btn" onClick={() => setInfoModal(prog.name)}>
                            INFO
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
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
