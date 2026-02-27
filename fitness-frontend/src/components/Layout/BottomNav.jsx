import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

export default function BottomNav() {
  const location = useLocation();
  const { user } = useAuthStore();

  const isActive = (path) => location.pathname === path ? '#60a5fa' : '#94a3b8';

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: '70px',
      backgroundColor: '#1e293b',
      borderTop: '1px solid #475569',
      display: 'flex',
      justifyContent: 'space-around',
      alignItems: 'center',
      zIndex: 50,
    }}>
      <Link to="/" style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', color: isActive('/'), textDecoration: 'none' }}>
        <span style={{ fontSize: '22px', lineHeight: '1' }}>🏠</span>
        <span style={{ fontSize: '11px', fontWeight: '500' }}>Home</span>
      </Link>

      <Link to="/exercises" style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', color: isActive('/exercises'), textDecoration: 'none' }}>
        <span style={{ fontSize: '22px', lineHeight: '1' }}>📚</span>
        <span style={{ fontSize: '11px', fontWeight: '500' }}>Exercises</span>
      </Link>

      <Link to="/workout" style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', color: isActive('/workout'), textDecoration: 'none' }}>
        <span style={{ fontSize: '22px', lineHeight: '1' }}>💪</span>
        <span style={{ fontSize: '11px', fontWeight: '500' }}>Workout</span>
      </Link>

      <Link to="/profile" style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', color: isActive('/profile'), textDecoration: 'none' }}>
        {user?.profile?.avatar ? (
          <img
            src={user.profile.avatar}
            alt="Avatar"
            style={{
              width: '22px',
              height: '22px',
              borderRadius: '50%',
              objectFit: 'cover',
              border: isActive('/profile') === '#60a5fa' ? '2px solid #60a5fa' : '2px solid #94a3b8',
              transition: 'border-color 0.2s'
            }}
          />
        ) : (
          <span style={{ fontSize: '22px', lineHeight: '1' }}>👤</span>
        )}
        <span style={{ fontSize: '11px', fontWeight: '500' }}>Profile</span>
      </Link>
    </nav>
  );
}
