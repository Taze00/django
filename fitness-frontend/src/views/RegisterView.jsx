import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import axios from 'axios';

export default function RegisterView() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [email, setEmail] = useState('');
  const [registrationKey, setRegistrationKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore(state => state.login);

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    if (username.length < 3) { setError('Benutzername mind. 3 Zeichen'); return; }
    if (password.length < 8) { setError('Passwort mind. 8 Zeichen'); return; }
    if (password !== passwordConfirm) { setError('Passwörter stimmen nicht überein'); return; }
    setIsLoading(true);
    try {
      await axios.post('/api/register/', { username, password, email, registration_key: registrationKey });
      await login(username, password);
      navigate('/onboarding');
    } catch (err) {
      setError(err.response?.data?.error || 'Registrierung fehlgeschlagen');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <p className="auth-logo">COR<span>VIS</span></p>
      <p className="auth-tagline">Die Kraft deines Körpers</p>

      <div className="auth-card">
        <p className="auth-title">— Registrieren</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Benutzername</label>
            <input className="form-input" type="text" value={username} onChange={e => setUsername(e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">E-Mail (optional)</label>
            <input className="form-input" type="email" value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Passwort</label>
            <input className="form-input" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">Passwort bestätigen</label>
            <input className="form-input" type="password" value={passwordConfirm} onChange={e => setPasswordConfirm(e.target.value)} required />
          </div>
          <div className="form-group">
            <label className="form-label">Registrierungsschlüssel</label>
            <input className="form-input" type="password" value={registrationKey} onChange={e => setRegistrationKey(e.target.value)} required />
          </div>
          {error && <div className="form-error">{error}</div>}
          <button className="btn-auth" type="submit" disabled={isLoading}>
            {isLoading ? 'Wird erstellt...' : 'Account erstellen →'}
          </button>
        </form>
        <p className="auth-footer">
          Schon ein Account? <Link to="/login">Anmelden</Link>
        </p>
      </div>
    </div>
  );
}
