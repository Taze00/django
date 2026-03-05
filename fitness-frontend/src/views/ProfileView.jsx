import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function ProfileView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Calisthenics</h1>
        </div>
      </div>

      <div className="main-content">
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>👤</div>
          <h2 style={{ fontSize: '24px', marginBottom: '16px', color: '#f1f5f9' }}>Profile</h2>
          <p style={{ color: '#94a3b8', marginBottom: '24px' }}>{user?.username || 'Athlete'}</p>
          <button
            onClick={handleLogout}
            style={{
              padding: '12px 24px',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
