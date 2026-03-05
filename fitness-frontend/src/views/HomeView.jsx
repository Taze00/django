import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

const WORKOUT_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const REST_DAYS = ['Sat', 'Sun'];

export default function HomeView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const workouts = useWorkoutStore(state => state.workouts);
  const isLoading = useWorkoutStore(state => state.isLoading);

  const handleStartWorkout = () => navigate('/workout');

  const getPushProgress = () => {
    const pushExercise = exercises.find(e => e.name === 'Push-ups');
    if (!pushExercise) return null;
    const prog = userProgressions[String(pushExercise.id)];
    return prog ? prog.current_progression : null;
  };

  const getPullProgress = () => {
    const pullExercise = exercises.find(e => e.name === 'Pull-ups');
    if (!pullExercise) return null;
    const prog = userProgressions[String(pullExercise.id)];
    return prog ? prog.current_progression : null;
  };

  const pushProg = getPushProgress();
  const pullProg = getPullProgress();

  // Calculate week status based on actual workouts
  const getWeekStatus = () => {
    const now = new Date();
    const dayIndex = now.getDay(); // 0 = Sunday, 1 = Monday, etc.

    // Get Monday of current week
    const monday = new Date(now);
    monday.setDate(now.getDate() - (dayIndex === 0 ? 6 : dayIndex - 1));
    monday.setHours(0, 0, 0, 0);

    const status = { Mon: false, Tue: false, Wed: false, Thu: false, Fri: false };

    workouts.forEach(workout => {
      const workoutDate = new Date(workout.date);
      workoutDate.setHours(0, 0, 0, 0);

      // Check if workout is in current week
      if (workoutDate >= monday) {
        const dayOfWeek = workoutDate.getDay();
        if (dayOfWeek === 1) status.Mon = true;
        else if (dayOfWeek === 2) status.Tue = true;
        else if (dayOfWeek === 3) status.Wed = true;
        else if (dayOfWeek === 4) status.Thu = true;
        else if (dayOfWeek === 5) status.Fri = true;
      }
    });

    return status;
  };

  const weekStatus = getWeekStatus();

  // Calculate total reps and workout count
  const stats = {
    pushReps: 0,
    pullReps: 0,
    totalWorkouts: workouts.length
  };

  workouts.forEach(workout => {
    workout.sets?.forEach(set => {
      if (set.exercise_name === 'Push-ups' && set.reps) {
        stats.pushReps += set.reps;
      } else if (set.exercise_name === 'Pull-ups' && set.reps) {
        stats.pullReps += set.reps;
      }
    });
  });

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Calisthenics</h1>
        </div>
      </div>

      <div className="main-content">
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
            <p style={{ color: '#94a3b8' }}>Loading your workouts...</p>
          </div>
        ) : (
          <>
            <p className="welcome-text">Welcome, {user?.username || 'Athlete'}</p>
            <div className="week-plan">
              <div className="week-grid-inline">
                {WORKOUT_DAYS.map(day => (
                  <div key={day} className={weekStatus[day] ? 'week-day completed' : 'week-day pending'}>
                    <p className="week-day-name">{day}</p>
                    <p className="week-day-status">{weekStatus[day] ? '✓' : '○'}</p>
                  </div>
                ))}
                {REST_DAYS.map(day => (
                  <div key={day} className="week-day rest-day">
                    <p className="week-day-name">{day}</p>
                    <p className="week-day-status">🌙</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="progression-section">
              <div className="progression-grid-compact">
                <div className="progression-card-compact progression-push">
                  <div className="progression-icon-compact">🚀</div>
                  <p className="progression-title-compact">Push</p>
                  {pushProg ? (
                    <>
                      <p className="progression-name-compact">{pushProg.name}</p>
                      <p className="progression-level-number">Level {pushProg.level}</p>
                    </>
                  ) : (
                    <p className="progression-name-compact">Loading...</p>
                  )}
                </div>

                <div className="progression-card-compact progression-pull">
                  <div className="progression-icon-compact">🔥</div>
                  <p className="progression-title-compact">Pull</p>
                  {pullProg ? (
                    <>
                      <p className="progression-name-compact">{pullProg.name}</p>
                      <p className="progression-level-number">Level {pullProg.level}</p>
                    </>
                  ) : (
                    <p className="progression-name-compact">Loading...</p>
                  )}
                </div>
              </div>
            </div>

            <div className="stats-summary">
              <div className="stat-item">
                <p className="stat-label">Push-ups</p>
                <p className="stat-value">{stats.pushReps}</p>
              </div>
              <div className="stat-item">
                <p className="stat-label">Pull-ups</p>
                <p className="stat-value">{stats.pullReps}</p>
              </div>
              <div className="stat-item">
                <p className="stat-label">Workouts</p>
                <p className="stat-value">{stats.totalWorkouts}</p>
              </div>
            </div>

            <button className="btn-start-inline" onClick={handleStartWorkout}>
              <span className="btn-start-emoji">💪</span>
              Start Workout
            </button>
          </>
        )}
      </div>
    </div>
  );
}
