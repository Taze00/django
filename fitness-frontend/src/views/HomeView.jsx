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

  // Test data for performance chart showing workout minutes
  const performanceData = {
    Mon: 32,
    Tue: 28,
    Wed: 35,
    Thu: 0,
    Fri: 0,
    Sat: 0,
    Sun: 0
  };

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

            <div className="performance-section">
              <h2 className="section-title">Performance Chart</h2>
              <div className="performance-chart">
                <div className="chart-bars">
                  {WORKOUT_DAYS.concat(REST_DAYS).map((day, idx) => {
                    const minutes = performanceData[day];
                    const maxMinutes = 40;
                    const height = (minutes / maxMinutes) * 100;
                    const isCompleted = weekStatus[day];
                    return (
                      <div key={day} className="chart-bar-wrapper">
                        <div
                          className={`chart-bar ${isCompleted && minutes > 0 ? 'completed' : 'empty'}`}
                          style={{ height: `${Math.max(20, height)}%` }}
                        ></div>
                        <p className="chart-label">{day}</p>
                      </div>
                    );
                  })}
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
