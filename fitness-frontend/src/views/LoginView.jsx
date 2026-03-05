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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900/10 to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse-soft"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl animate-pulse-soft" style={{ animationDelay: '1s' }}></div>

      <div className="w-full max-w-md px-6 relative z-10">
        <div className="bg-slate-800/70 backdrop-blur-xl rounded-2xl p-8 border border-slate-700/50 shadow-2xl animate-scale-in">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="text-5xl mb-4 animate-bounce-sm">💪</div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent mb-2">
              Calisthenics
            </h1>
            <p className="text-slate-400 text-sm">Master your bodyweight</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username Input */}
            <div className="group">
              <label className="block text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wider">
                Username
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="your username"
                  autoComplete="username"
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-400/50 focus:bg-slate-700/70 transition-all duration-200 group-focus-within:shadow-glow-blue"
                  required
                />
                <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none text-blue-400/50">
                  👤
                </div>
              </div>
            </div>

            {/* Password Input */}
            <div className="group">
              <label className="block text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="your password"
                  autoComplete="current-password"
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-400/50 focus:bg-slate-700/70 transition-all duration-200 group-focus-within:shadow-glow-blue"
                  required
                />
                <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none text-blue-400/50">
                  🔒
                </div>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="animate-slide-up p-4 bg-red-500/15 border border-red-500/50 text-red-200 rounded-xl text-sm font-medium flex items-start gap-3">
                <span className="text-lg">⚠️</span>
                <span>{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 mt-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold rounded-xl transition-all duration-200 shadow-lg hover:shadow-glow-blue disabled:shadow-none flex items-center justify-center gap-2 group"
            >
              {isLoading ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Logging in...
                </>
              ) : (
                <>
                  Enter
                  <span className="group-hover:translate-x-1 transition-transform duration-200">→</span>
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-slate-400 text-xs mt-8">
            Welcome to your fitness journey
          </p>
        </div>
      </div>
    </div>
  );
}
