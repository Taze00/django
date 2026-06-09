import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';
import api from '../api';

export default function ProfileView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);
  const getCurrentWorkout = useWorkoutStore(state => state.getCurrentWorkout);
  const resetWorkout = useWorkoutStore(state => state.resetWorkout);
  const [uploading, setUploading] = useState(false);
  const [previewImage, setPreviewImage] = useState(user?.profile_picture || null);
  const [resetting, setResetting] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [confirmText, setConfirmText] = useState('');

  const handleFileChange = async e => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { alert('Max 2MB'); return; }
    const reader = new FileReader();
    reader.onload = ev => setPreviewImage(ev.target.result);
    reader.readAsDataURL(file);
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('profile_picture', file);
      const res = await api.put('/profile/picture/upload/', fd);
      const pic = res.data.profile_picture ? `${res.data.profile_picture}?t=${Date.now()}` : null;
      useAuthStore.setState(s => ({ user: { ...s.user, profile_picture: pic } }));
    } catch { alert('Upload fehlgeschlagen'); setPreviewImage(user?.profile_picture || null); }
    finally { setUploading(false); }
  };

  const handleDeletePicture = async () => {
    if (!window.confirm('Profilbild löschen?')) return;
    setUploading(true);
    try {
      await api.delete('/profile/picture/delete/');
      setPreviewImage(null);
      useAuthStore.setState(s => ({ user: { ...s.user, profile_picture: null } }));
    } catch { alert('Löschen fehlgeschlagen'); }
    finally { setUploading(false); }
  };

  const handleResetWorkout = async () => {
    if (!window.confirm('Heutiges Workout zurücksetzen?')) return;
    setResetting(true);
    try {
      const w = await getCurrentWorkout();
      await resetWorkout(w.id);
    } catch { alert('Fehler beim Zurücksetzen'); }
    finally { setResetting(false); }
  };

  const handleResetOnboarding = async () => {
    setResetting(true);
    try {
      await api.post('/onboarding/reset/', {});
      useAuthStore.setState(s => ({ user: { ...s.user, onboarding_completed: false } }));
      setShowResetModal(false);
      setConfirmText('');
      navigate('/onboarding');
    } catch { alert('Fehler beim Zurücksetzen'); }
    finally { setResetting(false); }
  };

  return (
    <>
      <div className="header">
        <div className="header-content">
          <div className="header-logo">COR<span>VIS</span></div>
        </div>
      </div>

      <div className="main-content">
        {/* Avatar */}
        <div className="profile-avatar-wrap">
          <label style={{ cursor: 'pointer' }}>
            <div className="profile-avatar">
              {previewImage
                ? <img src={previewImage} alt="Profil" />
                : <span>👤</span>}
              <div className="profile-avatar-overlay">📷</div>
            </div>
            <input type="file" accept="image/*" onChange={handleFileChange} disabled={uploading} style={{ display: 'none' }} />
          </label>
          {previewImage && (
            <button onClick={handleDeletePicture} disabled={uploading} style={{ background: 'none', border: 'none', color: 'var(--muted)', fontSize: '0.6rem', letterSpacing: '1px', cursor: 'pointer', marginTop: '0.5rem' }}>
              Bild entfernen
            </button>
          )}
          <p className="profile-username" style={{ marginTop: '0.75rem' }}>{user?.username || 'Athlete'}</p>
          <p className="profile-email">{user?.email || ''}</p>
        </div>

        {/* Settings */}
        <span className="profile-section-label">Einstellungen</span>
        <button className="profile-nav-btn" onClick={() => navigate('/set-progression')}>
          <div>
            <p className="profile-nav-label">Level anpassen</p>
            <p className="profile-nav-desc">Deine Progressionsstufen</p>
          </div>
          <span className="profile-nav-arrow">›</span>
        </button>
        <button className="profile-nav-btn" onClick={() => navigate('/training-days')}>
          <div>
            <p className="profile-nav-label">Trainingstage</p>
            <p className="profile-nav-desc">Wochentage auswählen</p>
          </div>
          <span className="profile-nav-arrow">›</span>
        </button>

        {/* Danger */}
        <span className="profile-section-label" style={{ marginTop: '1rem' }}>Danger Zone</span>
        <button className="profile-danger-btn" onClick={handleResetWorkout} disabled={resetting}>
          Heutiges Workout zurücksetzen
        </button>
        <button className="profile-danger-btn" onClick={() => setShowResetModal(true)} disabled={resetting}>
          Onboarding zurücksetzen
        </button>
        <button className="profile-logout-btn" onClick={() => { logout(); navigate('/login'); }}>
          Abmelden
        </button>
      </div>

      {showResetModal && (
        <div className="modal-overlay" onClick={() => !resetting && setShowResetModal(false)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <p className="modal-danger-title">Account zurücksetzen</p>
            <p className="modal-warning-text">
              Das löscht <strong>alle Workouts</strong> und setzt deine Progressionen auf Level 1 zurück.
            </p>
            <ul className="modal-warning-list">
              <li>✗ Alle Workouts werden gelöscht</li>
              <li>✗ Alle Level werden zurückgesetzt</li>
              <li>✗ Onboarding startet neu</li>
            </ul>
            <p style={{ fontSize: '0.6rem', color: 'var(--muted)', marginBottom: '0.75rem', letterSpacing: '0.3px' }}>
              Tippe <strong style={{ color: 'var(--white)' }}>RESET</strong> zur Bestätigung:
            </p>
            <input
              className="modal-input"
              placeholder="RESET"
              value={confirmText}
              onChange={e => setConfirmText(e.target.value)}
              disabled={resetting}
            />
            <div className="modal-btn-row">
              <button className="btn-cancel" onClick={() => { setShowResetModal(false); setConfirmText(''); }} disabled={resetting}>
                Abbrechen
              </button>
              <button className="btn-danger" onClick={handleResetOnboarding} disabled={resetting || confirmText !== 'RESET'}>
                {resetting ? 'Wird zurückgesetzt...' : 'Bestätigen'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
