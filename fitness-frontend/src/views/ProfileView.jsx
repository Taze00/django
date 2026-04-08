import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';
import api from '../api';

export default function ProfileView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);
  const workouts = useWorkoutStore(state => state.workouts);
  const getCurrentWorkout = useWorkoutStore(state => state.getCurrentWorkout);
  const resetWorkout = useWorkoutStore(state => state.resetWorkout);
  const [uploading, setUploading] = useState(false);
  const [previewImage, setPreviewImage] = useState(user?.profile_picture || null);
  const [resetting, setResetting] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [confirmText, setConfirmText] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check file size
    if (file.size > 2 * 1024 * 1024) {
      alert('File size exceeds 2MB limit');
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (event) => {
      setPreviewImage(event.target.result);
    };
    reader.readAsDataURL(file);

    // Upload file
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('profile_picture', file);

      const res = await api.put('/profile/picture/upload/', formData);

      // Update user in auth store with cache-buster timestamp
      const pictureWithCache = res.data.profile_picture ? `${res.data.profile_picture}?t=${Date.now()}` : null;
      useAuthStore.setState(state => ({
        user: { ...state.user, profile_picture: pictureWithCache }
      }));
    } catch (error) {
      alert('Failed to upload image');
      setPreviewImage(user?.profile_picture || null);
    } finally {
      setUploading(false);
    }
  };

  const handleDeletePicture = async () => {
    if (!window.confirm('Delete profile picture?')) return;

    setUploading(true);
    try {
      await api.delete('/profile/picture/delete/');
      setPreviewImage(null);
      useAuthStore.setState(state => ({
        user: { ...state.user, profile_picture: null }
      }));
    } catch (error) {
      alert('Failed to delete image');
    } finally {
      setUploading(false);
    }
  };

  const handleResetOnboarding = async () => {
    setResetting(true);
    try {
      await api.post('/onboarding/reset/', {});
      // Update user profile and redirect
      useAuthStore.setState(state => ({
        user: { ...state.user, onboarding_completed: false }
      }));
      setShowResetModal(false);
      setConfirmText('');
      navigate('/onboarding');
    } catch (error) {
      alert('Failed to reset onboarding');
      console.error(error);
    } finally {
      setResetting(false);
    }
  };

  const handleResetWorkout = async () => {
    if (!window.confirm('Reset today\'s workout? All sets will be deleted.')) return;

    setResetting(true);
    try {
      const workout = await getCurrentWorkout();
      await resetWorkout(workout.id);
      alert('Workout reset successfully');
    } catch (error) {
      alert('Failed to reset workout');
    } finally {
      setResetting(false);
    }
  };

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
          <div className="profile-avatar-container">
            {previewImage ? (
              <img src={previewImage} alt="Profile" className="profile-avatar-image" />
            ) : (
              <div className="profile-avatar">👤</div>
            )}
            <label className="profile-upload-overlay" style={{ opacity: uploading ? 0.5 : 1 }}>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                disabled={uploading}
                style={{ display: 'none' }}
              />
              <span className="profile-upload-icon">📷</span>
            </label>
            {previewImage && (
              <button
                className="profile-delete-picture"
                onClick={handleDeletePicture}
                disabled={uploading}
                title="Delete picture"
              >
                ✕
              </button>
            )}
          </div>
          <p className="profile-username">{user?.username || 'Athlete'}</p>
          <p className="profile-email">{user?.email || 'No email'}</p>
          <p className="profile-upload-hint">Tap the image to upload a photo (max 2MB)</p>
        </div>


        {/* Settings Section */}
        <div className="profile-section">
          <h3 className="profile-section-title">Settings</h3>

          <button
            className="profile-setting-nav-btn"
            onClick={() => navigate('/set-progression')}
          >
            <div>
              <p className="profile-setting-label">Set Your Levels</p>
              <p className="profile-setting-desc">Choose your starting progression</p>
            </div>
            <span className="profile-setting-arrow">›</span>
          </button>

          <button
            className="profile-setting-nav-btn"
            onClick={() => navigate('/training-days')}
          >
            <div>
              <p className="profile-setting-label">Training Days</p>
              <p className="profile-setting-desc">Choose which days to train</p>
            </div>
            <span className="profile-setting-arrow">›</span>
          </button>

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

        {/* Danger Zone */}
        <div className="profile-section danger-zone">
          <h3 className="profile-section-title">Danger Zone</h3>
          <button
            className="profile-reset-btn"
            onClick={handleResetWorkout}
            disabled={resetting}
          >
            {resetting ? 'Resetting...' : 'Reset Today\'s Workout'}
          </button>

          <button
            className="profile-reset-btn"
            onClick={() => setShowResetModal(true)}
            disabled={resetting}
          >
            Reset Onboarding
          </button>

          <button
            className="profile-logout-btn"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Reset Onboarding Modal */}
      {showResetModal && (
        <div className="modal-overlay" onClick={() => !resetting && setShowResetModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">⚠️ Reset Onboarding?</h2>
            
            <div className="modal-warning">
              <p className="modal-warning-text">
                This will <strong>delete all your progress</strong> and reset your account to the beginning:
              </p>
              <ul className="modal-warning-list">
                <li>✗ All workouts will be deleted</li>
                <li>✗ All exercise progressions reset to Level 1</li>
                <li>✗ You'll need to complete onboarding again</li>
              </ul>
            </div>

            <p className="modal-instruction">
              Type <strong>"RESET"</strong> below to confirm:
            </p>
            
            <input
              type="text"
              className="modal-input"
              placeholder='Type "RESET" to confirm'
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              disabled={resetting}
            />

            <div className="modal-buttons">
              <button
                className="modal-btn modal-btn-cancel"
                onClick={() => {
                  setShowResetModal(false);
                  setConfirmText('');
                }}
                disabled={resetting}
              >
                Cancel
              </button>
              <button
                className="modal-btn modal-btn-danger"
                onClick={handleResetOnboarding}
                disabled={resetting || confirmText !== 'RESET'}
              >
                {resetting ? 'Resetting...' : 'Confirm Reset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
