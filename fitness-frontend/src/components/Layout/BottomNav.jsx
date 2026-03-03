import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useWorkoutStore } from '../../store/workoutStore';

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { isWorkoutActive } = useWorkoutStore();

  const isActive = (path) => location.pathname === path ? '#60a5fa' : '#94a3b8';

  const handleNavClick = (e, path) => {
    if (isWorkoutActive && location.pathname === '/workout' && path !== '/workout') {
      e.preventDefault();
      const confirmed = window.confirm(
        'Workout abbrechen? Der aktuelle Fortschritt geht verloren.'
      );
      if (confirmed) {
        useWorkoutStore.setState({ isWorkoutActive: false });
        navigate(path);
      }
    }
  };

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
      <Link 
        to="/" 
        onClick={(e) => handleNavClick(e, '/')}
        style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', color: isActive('/'), textDecoration: 'none' }}
      >
        <span style={{ fontSize: '28px', lineHeight: '1' }}>🏠</span>
        <span style={{ fontSize: '12px', fontWeight: '500' }}>Home</span>
      </Link>

      <Link 
        to="/exercises" 
        onClick={(e) => handleNavClick(e, '/exercises')}
        style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', color: isActive('/exercises'), textDecoration: 'none' }}
      >
        <span style={{ fontSize: '28px', lineHeight: '1' }}>📚</span>
        <span style={{ fontSize: '12px', fontWeight: '500' }}>Exercises</span>
      </Link>

      <Link 
        to="/workout" 
        onClick={(e) => handleNavClick(e, '/workout')}
        style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', color: isActive('/workout'), textDecoration: 'none' }}
      >
        <span style={{ fontSize: '28px', lineHeight: '1' }}>💪</span>
        <span style={{ fontSize: '12px', fontWeight: '500' }}>Workout</span>
      </Link>

      <Link 
        to="/profile" 
        onClick={(e) => handleNavClick(e, '/profile')}
        style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', color: isActive('/profile'), textDecoration: 'none' }}
      >
        {user?.profile?.avatar ? (
          <img
            src={user.profile.avatar}
            alt="Avatar"
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              objectFit: 'cover',
              border: 'none',
              transition: 'border-color 0.2s'
            }}
          />
        ) : (
          <span style={{ fontSize: '28px', lineHeight: '1' }}>👤</span>
        )}
        <span style={{ fontSize: '12px', fontWeight: '500' }}>Profile</span>
      </Link>
    </nav>
  );
}
