import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export default function ProfileView() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
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
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center text-3xl">
                💪
              </div>
              <div>
                <p className="text-white font-bold text-lg">{user.username}</p>
                <p className="text-slate-400 text-sm">{user.email || 'Kein Email'}</p>
              </div>
            </div>

            <div className="space-y-3 border-t border-slate-700 pt-4">
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

            <div className="space-y-4">
              {/* iOS Instructions */}
              <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-600">
                <h3 className="font-semibold text-white mb-3">🍎 iPhone / iPad</h3>
                <ol className="text-slate-300 text-sm space-y-2">
                  <li className="flex gap-3">
                    <span className="text-blue-400 font-bold">1.</span>
                    <span>Tippe unten auf <span className="text-2xl">⬆️</span> "Teilen"</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-blue-400 font-bold">2.</span>
                    <span>Wähle "Zum Home-Bildschirm"</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-blue-400 font-bold">3.</span>
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
                    <span>Öffne Chrome und gehe zu <span className="text-blue-300">alex.volkmann.com/fitness</span></span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-green-400 font-bold">2.</span>
                    <span>Oben rechts: Tippe auf ⋮ (3 Punkte)</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-green-400 font-bold">3.</span>
                    <span>Wähle "App installieren" oder "Zum Startbildschirm"</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-green-400 font-bold">4.</span>
                    <span>Bestätige - die App wird installiert! 🎉</span>
                  </li>
                </ol>
              </div>

              {/* Offline Info */}
              <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-500/30">
                <p className="text-blue-200 text-sm">
                  <span className="font-semibold">💡 Offline Modus:</span> Nach der Installation funktioniert die App auch ohne Internet! Trainiere überall. 🚀
                </p>
              </div>
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
