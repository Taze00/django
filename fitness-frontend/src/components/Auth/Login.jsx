import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export const Login = () => {
  const navigate = useNavigate();
  const { login, isLoading, error } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');

    if (!username || !password) {
      setLocalError('Benutzername und Passwort erforderlich');
      return;
    }

    const success = await login(username, password);
    if (success) {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-slate-800 rounded-2xl border-2 border-slate-700 p-8 backdrop-blur-sm bg-opacity-80">
          <h1 className="text-3xl font-bold text-white mb-2 text-center">
            Fitness Tracker
          </h1>
          <p className="text-slate-400 text-center mb-8">
            Melde dich an, um zu starten
          </p>

          {(error || localError) && (
            <div className="bg-red-500/10 border-l-4 border-red-500 p-4 mb-6 rounded">
              <p className="text-red-400 text-sm">{error || localError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-slate-300 text-sm font-semibold mb-2">
                Benutzername
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-900 border-2 border-slate-700 text-white px-4 py-3 rounded-xl focus:border-blue-500 focus:outline-none transition"
                placeholder="Dein Benutzername"
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-slate-300 text-sm font-semibold mb-2">
                Passwort
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900 border-2 border-slate-700 text-white px-4 py-3 rounded-xl focus:border-blue-500 focus:outline-none transition"
                placeholder="Dein Passwort"
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-slate-600 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-300 active:scale-95 shadow-lg shadow-blue-500/30"
            >
              {isLoading ? 'Lädt...' : 'Anmelden'}
            </button>
          </form>

          <p className="text-slate-400 text-center text-sm mt-6">
            Noch kein Konto?{' '}
            <button
              onClick={() => navigate('/register')}
              className="text-blue-400 hover:text-blue-300 font-semibold"
            >
              Jetzt registrieren
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};
