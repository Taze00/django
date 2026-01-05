import { useEffect } from 'react';
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

      {/* User Info */}
      {user && (
        <div className="p-4">
          <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center text-3xl">
                👤
              </div>
              <div>
                <p className="text-white font-bold text-lg">{user.username}</p>
                <p className="text-slate-400 text-sm">{user.email}</p>
              </div>
            </div>

            <div className="space-y-3 border-t border-slate-700 pt-4">
              <div className="flex justify-between items-center">
                <p className="text-slate-400">Member since</p>
                <p className="text-white font-semibold">
                  {new Date(user.date_joined).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full mt-6 bg-red-500/20 text-red-300 border border-red-500/30 rounded-lg py-3 font-semibold hover:bg-red-500/30 transition-colors"
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
