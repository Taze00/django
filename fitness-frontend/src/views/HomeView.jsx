import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

const WORKOUT_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const REST_DAYS = ['Sat', 'Sun'];

export default function HomeView() {
  const navigate = useNavigate();
  const logout = useAuthStore(state => state.logout);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const isLoading = useWorkoutStore(state => state.isLoading);

  const handleStartWorkout = () => navigate('/workout');
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

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

  const weekStatus = { Mon: true, Tue: true, Wed: true, Thu: false, Fri: false };

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Calisthenics</h1>
          <button className="btn-logout" onClick={handleLogout}>Logout</button>
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
            <div className="week-plan">
              <h2 className="section-title">This Week</h2>
              <div className="week-grid">
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
              <h2 className="section-title">Current Progression</h2>
              <div className="progression-grid">
                <div className="progression-card progression-push">
                  <div className="progression-icon">💪</div>
                  <h3 className="progression-title">Push-ups</h3>
                  {pushProg ? (
                    <>
                      <p className="progression-name">{pushProg.name}</p>
                      <p className="progression-target">Target: {pushProg.target_value}{pushProg.target_type === 'reps' ? ' reps' : 's'}</p>
                    </>
                  ) : (
                    <p className="progression-target">Loading...</p>
                  )}
                </div>

                <div className="progression-card progression-pull">
                  <div className="progression-icon">🔥</div>
                  <h3 className="progression-title">Pull-ups</h3>
                  {pullProg ? (
                    <>
                      <p className="progression-name">{pullProg.name}</p>
                      <p className="progression-target">Target: {pullProg.target_value}{pullProg.target_type === 'reps' ? ' reps' : 's'}</p>
                    </>
                  ) : (
                    <p className="progression-target">Loading...</p>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="floating-button">
        <button className="btn-start" onClick={handleStartWorkout}>
          <span className="btn-start-emoji">💪</span>
          Start Workout
        </button>
      </div>
    </div>
  );
}
