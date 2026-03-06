import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore(state => state.user);

  const tabs = [
    { label: 'Home', icon: '🏠', path: '/' },
    { label: 'Exercises', icon: '🏋️', path: '/exercises' },
    { label: 'Statistics', icon: '📊', path: '/statistics' },
    { label: 'Profile', icon: null, path: '/profile', isProfile: true }
  ];

  return (
    <nav className="bottom-nav">
      {tabs.map(tab => (
        <button
          key={tab.path}
          className={`bottom-nav-item ${location.pathname === tab.path ? 'active' : ''}`}
          onClick={() => navigate(tab.path)}
          title={tab.label}
        >
          {tab.isProfile && user?.profile_picture ? (
            <>
              <img
                src={user.profile_picture}
                alt="Profile"
                className="bottom-nav-profile-pic"
              />
              <span>Profile</span>
            </>
          ) : (
            <>
              <span className="bottom-nav-icon">{tab.icon}</span>
              <span>{tab.label}</span>
            </>
          )}
        </button>
      ))}
    </nav>
  );
}
