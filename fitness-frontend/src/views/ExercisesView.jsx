import { useWorkoutStore } from '../stores/workoutStore';

export default function ExercisesView() {
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
        <h2 className={`exercise-section-title ${colorClass}`}>{exercise.name.toUpperCase()}</h2>

        {/* Current Level Card */}
        <div className={`exercise-current-card ${colorClass}`}>
          <p className="exercise-current-name">{currentProg?.name || 'Loading...'}</p>
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
                className={`exercise-ladder-item ${status} ${colorClass}`}
              >
                <span className="exercise-ladder-icon">{icon}</span>
                <span className="exercise-ladder-name">{prog.name}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const pushExercise = exercises.find(e => e.name === 'Push-ups');
  const pullExercise = exercises.find(e => e.name === 'Pull-ups');

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
      </div>
    </div>
  );
}
