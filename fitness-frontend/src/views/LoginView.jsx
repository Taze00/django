import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function LoginView() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore(state => state.login);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-slate-900 to-emerald-900/20"></div>
      <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse-soft"></div>
      <div className="absolute bottom-20 right-10 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl animate-pulse-soft" style={{ animationDelay: '1.5s' }}></div>

      <div className="w-full max-w-md px-6 relative z-10">
        {/* Card */}
        <div className="bg-slate-800/50 backdrop-blur-2xl border border-slate-700/50 rounded-3xl p-8 shadow-2xl animate-scale-in">
          {/* Logo Area */}
          <div className="text-center mb-8">
            <div className="inline-block p-4 bg-gradient-to-br from-emerald-500 to-blue-500 rounded-2xl mb-4 animate-bounce-sm">
              <span className="text-4xl">💪</span>
            </div>
            <h1 className="text-3xl font-black bg-gradient-to-r from-blue-300 via-emerald-300 to-blue-300 bg-clip-text text-transparent mb-1">
              Calisthenics
            </h1>
            <p className="text-slate-400 text-sm font-medium">Master your bodyweight</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                autoComplete="username"
                className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/50 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-400/50 focus:bg-slate-700/50 transition-all duration-200"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/50 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-400/50 focus:bg-slate-700/50 transition-all duration-200"
                required
              />
            </div>

            {/* Error */}
            {error && (
              <div className="animate-slide-up p-3 bg-red-500/20 border border-red-400/50 text-red-200 rounded-xl text-xs font-medium">
                ⚠️ {error}
              </div>
            )}

            {/* Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 mt-6 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold rounded-xl transition-all duration-300 shadow-lg hover:shadow-glow disabled:shadow-none transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Logging in...
                </>
              ) : (
                <>
                  <span>Enter</span>
                  <span>→</span>
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-slate-500 text-xs mt-6 font-medium">
            Push your limits every day
          </p>
        </div>
      </div>
    </div>
  );
}
