import { Link, useLocation } from 'react-router-dom';

export default function BottomNav() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? '#60a5fa' : '#94a3b8';

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: '80px',
      backgroundColor: '#1e293b',
      borderTop: '1px solid #475569',
      display: 'flex',
      justifyContent: 'space-around',
      alignItems: 'center',
      zIndex: 50,
    }}>
      <Link to="/" style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: isActive('/'), textDecoration: 'none' }}>
        <span style={{ fontSize: '24px', marginBottom: '4px' }}>🏠</span>
        <span style={{ fontSize: '12px' }}>Home</span>
      </Link>

      <Link to="/workout" style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: isActive('/workout'), textDecoration: 'none' }}>
        <span style={{ fontSize: '24px', marginBottom: '4px' }}>💪</span>
        <span style={{ fontSize: '12px' }}>Workout</span>
      </Link>

      <Link to="/profile" style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: isActive('/profile'), textDecoration: 'none' }}>
        <span style={{ fontSize: '24px', marginBottom: '4px' }}>👤</span>
        <span style={{ fontSize: '12px' }}>Profile</span>
      </Link>
    </nav>
  );
}
