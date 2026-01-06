import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useAuthStore } from '../../store/authStore';
import { useWorkoutStore } from '../../store/workoutStore';
import shareIcon from '../../assets/share-icon.png';
import mehrIcon from '../../assets/mehr-icon.png';

export default function ProfileView() {
  const { user, logout, fetchUser } = useAuth();
  const navigate = useNavigate();
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);
  const [avatarCacheBuster, setAvatarCacheBuster] = useState(Date.now());

  // Refresh profile data when user changes (from auth store updates)
  // This ensures avatar updates immediately after upload
  useEffect(() => {
    if (user?.profile?.avatar) {
      console.log('[ProfileView] Profile avatar detected:', user.profile.avatar);
      setAvatarCacheBuster(Date.now());
    }
  }, [user?.profile?.avatar]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file size (3MB limit)
    const MAX_SIZE = 3 * 1024 * 1024; // 3MB in bytes
    if (file.size > MAX_SIZE) {
      setUploadMessage({ type: 'error', text: 'Datei ist zu groß (max. 3MB)' });
      return;
    }

    // Check file type
    if (!file.type.startsWith('image/')) {
      setUploadMessage({ type: 'error', text: 'Bitte wähle ein Bild aus' });
      return;
    }

    setAvatarFile(file);
    setUploadMessage(null);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setAvatarPreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleUploadAvatar = async () => {
    if (!avatarFile) return;

    setIsUploading(true);
    setUploadMessage(null);

    try {
      const formData = new FormData();
      formData.append('avatar', avatarFile);

      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/fitness/user/profile/', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[ProfileView] Avatar uploaded successfully:', data);

        setUploadMessage({ type: 'success', text: '✓ Profilbild aktualisiert!' });
        setAvatarFile(null);
        setAvatarPreview(null);

        // Refresh user data to show new avatar
        await fetchUser();

        // Give service worker a moment to update the cache, then fetch fresh profile data
        // with cache busting to ensure we get the latest from network
        await new Promise(resolve => setTimeout(resolve, 500));

        // Refetch profile to get updated avatar URL - use cache busting to skip SW cache
        const profileResponse = await fetch(`/api/fitness/user/profile/?t=${Date.now()}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Cache-Control': 'no-cache',
          },
        });
        if (profileResponse.ok) {
          const profileData = await profileResponse.json();
          console.log('[ProfileView] Profile refreshed with avatar:', profileData.avatar);
          // Update user object with the new avatar from profile
          const updatedUser = {
            ...user,
            profile: profileData,
          };
          // This updates the auth store user object directly
          useAuthStore.setState({ user: updatedUser });
          // Update cache buster to force browser to fetch new image
          setAvatarCacheBuster(Date.now());
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('[ProfileView] Upload failed:', response.status, errorData);
        setUploadMessage({ type: 'error', text: 'Fehler beim Hochladen' });
      }
    } catch (error) {
      console.error('[ProfileView] Upload error:', error);
      setUploadMessage({ type: 'error', text: 'Fehler beim Hochladen' });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-slate-800/95 backdrop-blur border-b border-slate-700 z-10">
        <h1 className="text-2xl font-bold text-white p-4">👤 Profile</h1>
      </div>

      {user && (
        <div className="p-4 space-y-6">
          {/* User Card */}
          <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
            {/* Avatar Section */}
            <div className="flex flex-col items-center mb-6">
              <div className="relative mb-4">
                {avatarPreview ? (
                  <img
                    src={avatarPreview}
                    alt="Avatar Preview"
                    className="w-24 h-24 rounded-full object-cover border-4 border-blue-500"
                  />
                ) : user.profile?.avatar ? (
                  <img
                    src={`${user.profile.avatar}?t=${avatarCacheBuster}`}
                    alt="Avatar"
                    className="w-24 h-24 rounded-full object-cover border-4 border-blue-500"
                  />
                ) : (
                  <div className="w-24 h-24 rounded-full bg-blue-500/20 flex items-center justify-center text-5xl border-4 border-blue-500">
                    💪
                  </div>
                )}
                <label className="absolute bottom-0 right-0 bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full cursor-pointer transition-colors">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    className="hidden"
                  />
                  📷
                </label>
              </div>

              {avatarFile && (
                <div className="w-full space-y-2">
                  <button
                    onClick={handleUploadAvatar}
                    disabled={isUploading}
                    className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-2 px-4 rounded-lg transition-all duration-200 active:scale-95"
                  >
                    {isUploading ? (
                      <span className="flex items-center justify-center">
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>
                        Wird hochgeladen...
                      </span>
                    ) : (
                      '✓ Bestätigen'
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setAvatarFile(null);
                      setAvatarPreview(null);
                      setUploadMessage(null);
                    }}
                    disabled={isUploading}
                    className="w-full bg-slate-700 hover:bg-slate-600 disabled:bg-slate-600 text-white font-bold py-2 px-4 rounded-lg transition-all duration-200 active:scale-95"
                  >
                    Abbrechen
                  </button>
                  <p className="text-xs text-slate-400 text-center">
                    Max 3MB • JPG, PNG, WebP
                  </p>
                </div>
              )}

              {uploadMessage && (
                <div
                  className={`mt-3 text-sm font-semibold text-center w-full px-3 py-2 rounded-lg ${
                    uploadMessage.type === 'success'
                      ? 'bg-green-500/20 border border-green-500/30 text-green-300'
                      : 'bg-red-500/20 border border-red-500/30 text-red-300'
                  }`}
                >
                  {uploadMessage.text}
                </div>
              )}
            </div>

            {/* User Info */}
            <div className="text-center border-t border-slate-700 pt-4">
              <p className="text-white font-bold text-lg">{user.username}</p>
              <p className="text-slate-400 text-sm">{user.email || 'Kein Email'}</p>
            </div>

            <div className="space-y-3 border-t border-slate-700 pt-4 mt-4">
              <div className="flex justify-between items-center">
                <p className="text-slate-400">Mitglied seit</p>
                <p className="text-white font-semibold">
                  {new Date(user.date_joined).toLocaleDateString('de-DE')}
                </p>
              </div>
            </div>
          </div>

          {/* Installation Guide */}
          <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">📱 App installieren</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* iOS Instructions */}
              <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-600">
                <h3 className="font-semibold text-white mb-3">🍎 iPhone / iPad</h3>
                <ol className="text-slate-300 text-sm space-y-2">
                  <li className="flex gap-3 items-center">
                    <span className="text-blue-400 font-bold">1.</span>
                    <span>Tippe unten auf das Share-Icon:</span>
                    <img src={shareIcon} alt="Share Icon" className="w-5 h-5 object-contain" />
                  </li>
                  <li className="flex gap-3 items-center">
                    <span className="text-blue-400 font-bold">2.</span>
                    <span>Klicke auf "Mehr":</span>
                    <img src={mehrIcon} alt="Mehr Icon" style={{ height: '1.6rem' }} className="object-contain" />
                  </li>
                  <li className="flex gap-3">
                    <span className="text-blue-400 font-bold">3.</span>
                    <span>Wähle "Zum Home-Bildschirm"</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-blue-400 font-bold">4.</span>
                    <span>Tippe "Hinzufügen" - fertig! 🎉</span>
                  </li>
                </ol>
              </div>

              {/* Android Instructions */}
              <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-600">
                <h3 className="font-semibold text-white mb-3">🤖 Android / Chrome</h3>
                <ol className="text-slate-300 text-sm space-y-2">
                  <li className="flex gap-3">
                    <span className="text-green-400 font-bold">1.</span>
                    <span>Oben rechts: Tippe auf ⋮ (3 Punkte)</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-green-400 font-bold">2.</span>
                    <span>Wähle "App installieren" oder "Zum Startbildschirm"</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-green-400 font-bold">3.</span>
                    <span>Bestätige - die App wird installiert! 🎉</span>
                  </li>
                </ol>
              </div>
            </div>

            {/* Offline Info */}
            <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-500/30 mt-4">
              <p className="text-blue-200 text-sm">
                <span className="font-semibold">💡 Offline Modus:</span> Nach der Installation funktioniert die App auch ohne Internet! Trainiere überall. 🚀
              </p>
            </div>
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full bg-red-500/20 text-red-300 border border-red-500/30 rounded-lg py-3 font-semibold hover:bg-red-500/30 transition-colors"
          >
            Abmelden
          </button>
        </div>
      )}
    </div>
  );
}
