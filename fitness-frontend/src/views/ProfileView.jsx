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
  const [uploading, setUploading] = useState(false);
  const [previewImage, setPreviewImage] = useState(user?.profile_picture || null);

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
          <button
            className="profile-logout-btn"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
