import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

export default function ProfileView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);
  const workouts = useWorkoutStore(state => state.workouts);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleLogoutConfirm = () => {
    logout();
    navigate('/login');
  };

  // Calculate stats
  const totalWorkouts = workouts.length;
  const totalPushReps = workouts.reduce((sum, w) => {
    return sum + (w.sets?.reduce((setSum, s) => {
      return setSum + (s.exercise_name === 'Push-ups' && s.reps ? s.reps : 0);
    }, 0) || 0);
  }, 0);
  const totalPullReps = workouts.reduce((sum, w) => {
    return sum + (w.sets?.reduce((setSum, s) => {
      return setSum + (s.exercise_name === 'Pull-ups' && s.reps ? s.reps : 0);
    }, 0) || 0);
  }, 0);

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Calisthenics</h1>
        </div>
      </div>

      <div className="main-content">
        {/* User Card */}
        <div className="profile-card">
          <div className="profile-avatar">👤</div>
          <p className="profile-username">{user?.username || 'Athlete'}</p>
          <p className="profile-email">{user?.email || 'No email'}</p>
        </div>

        {/* Stats Section */}
        <div className="profile-section">
          <h3 className="profile-section-title">Stats</h3>
          <div className="profile-stats-grid">
            <div className="profile-stat-item">
              <p className="profile-stat-label">Total Workouts</p>
              <p className="profile-stat-value">{totalWorkouts}</p>
            </div>
            <div className="profile-stat-item">
              <p className="profile-stat-label">Push-ups</p>
              <p className="profile-stat-value">{totalPushReps}</p>
            </div>
            <div className="profile-stat-item">
              <p className="profile-stat-label">Pull-ups</p>
              <p className="profile-stat-value">{totalPullReps}</p>
            </div>
          </div>
        </div>

        {/* Settings Section */}
        <div className="profile-section">
          <h3 className="profile-section-title">Settings</h3>
          <div className="profile-settings">
            <div className="profile-setting-item">
              <div>
                <p className="profile-setting-label">Notifications</p>
                <p className="profile-setting-desc">Get reminders for workouts</p>
              </div>
              <input type="checkbox" className="profile-toggle" defaultChecked />
            </div>
            <div className="profile-setting-item">
              <div>
                <p className="profile-setting-label">Dark Mode</p>
                <p className="profile-setting-desc">Always enabled (app default)</p>
              </div>
              <input type="checkbox" className="profile-toggle" checked disabled />
            </div>
          </div>
        </div>

        {/* Logout Button */}
        <div className="profile-section">
          {!showLogoutConfirm ? (
            <button
              className="profile-logout-btn"
              onClick={() => setShowLogoutConfirm(true)}
            >
              Logout
            </button>
          ) : (
            <div className="profile-logout-confirm">
              <p className="profile-logout-text">Are you sure you want to logout?</p>
              <div className="profile-logout-buttons">
                <button
                  className="profile-logout-cancel"
                  onClick={() => setShowLogoutConfirm(false)}
                >
                  Cancel
                </button>
                <button
                  className="profile-logout-confirm-btn"
                  onClick={handleLogoutConfirm}
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
