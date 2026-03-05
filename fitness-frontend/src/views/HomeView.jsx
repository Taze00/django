import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

export default function HomeView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const isLoading = useWorkoutStore(state => state.isLoading);

  const handleStartWorkout = () => navigate('/workout');
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Calisthenics</h1>
          <div className="header-user">
            <span className="header-username">{user?.username}</span>
            <button className="btn-logout" onClick={handleLogout} title="Logout">🚪</button>
          </div>
        </div>
      </div>

      <div className="main-content">
        <h2 className="section-title">Today's Workout</h2>
        <p className="section-subtitle">Check your current progression levels</p>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
            <p style={{ color: '#94a3b8' }}>Loading your workouts...</p>
          </div>
        ) : (
          <>
            <div className="exercise-grid">
              {exercises.map((exercise) => {
                const prog = userProgressions[String(exercise.id)];
                return (
                  <div key={exercise.id} className="exercise-card">
                    <div className="exercise-icon">
                      {exercise.name.includes('Push') ? '💪' : '🔥'}
                    </div>
                    <div className="exercise-info">
                      <h3 className="exercise-name">{exercise.name}</h3>
                      <p className="exercise-label">Current Level</p>
                      {prog ? (
                        <>
                          <p className="exercise-level">{prog.current_progression.name}</p>
                          <p className="exercise-target">
                            Target: {prog.current_progression.target_value}
                            {prog.current_progression.target_type === 'reps' ? ' reps' : 's'}
                          </p>
                        </>
                      ) : (
                        <p className="exercise-target">Loading...</p>
                      )}
                    </div>
                    <div className="exercise-arrow">→</div>
                  </div>
                );
              })}
            </div>

            <div className="motivation-card">
              <h3 className="motivation-title">Ready to push?</h3>
              <p className="motivation-text">Every rep brings you closer to your goals</p>
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
