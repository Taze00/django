import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function LoginView() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore(state => state.login);

  const handleSubmit = async e => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login fehlgeschlagen');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <p className="auth-logo">COR<span>VIS</span></p>
      <p className="auth-tagline">Die Kraft deines Körpers</p>

      <div className="auth-card">
        <p className="auth-title">— Anmelden</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Benutzername</label>
            <input
              className="form-input"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Passwort</label>
            <input
              className="form-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error && <div className="form-error">{error}</div>}
          <button className="btn-auth" type="submit" disabled={isLoading}>
            {isLoading ? 'Einloggen...' : 'Einloggen →'}
          </button>
        </form>
        <p className="auth-footer">
          Noch kein Account? <Link to="/register">Registrieren</Link>
        </p>
      </div>
    </div>
  );
}
