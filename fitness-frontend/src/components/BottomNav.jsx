import { useNavigate, useLocation } from 'react-router-dom';

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();

  const tabs = [
    { label: 'Home', icon: '🏠', path: '/' },
    { label: 'Exercises', icon: '🏋️', path: '/exercises' },
    { label: 'Statistics', icon: '📊', path: '/statistics' },
    { label: 'Profile', icon: '👤', path: '/profile' }
  ];

  return (
    <nav className="bottom-nav">
      {tabs.map(tab => (
        <button
          key={tab.path}
          className={`bottom-nav-item ${location.pathname === tab.path ? 'active' : ''}`}
          onClick={() => navigate(tab.path)}
        >
          <span className="bottom-nav-icon">{tab.icon}</span>
          <span>{tab.label}</span>
        </button>
      ))}
    </nav>
  );
}
