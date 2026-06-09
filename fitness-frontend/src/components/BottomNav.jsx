import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

const tabs = [
  { label: 'Home',       path: '/',          icon: '⌂' },
  { label: 'Übungen',    path: '/exercises',  icon: '↑' },
  { label: 'Statistik',  path: '/statistics', icon: '≡' },
  { label: 'Profil',     path: '/profile',    isProfile: true },
];

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore(state => state.user);

  return (
    <nav className="bottom-nav">
      {tabs.map(tab => (
        <button
          key={tab.path}
          className={`bottom-nav-item ${location.pathname === tab.path ? 'active' : ''}`}
          onClick={() => navigate(tab.path)}
        >
          {tab.isProfile ? (
            <>
              {user?.profile_picture
                ? <img src={user.profile_picture} alt="Profil" className="bottom-nav-profile-pic" />
                : <span className="bottom-nav-icon">👤</span>}
              <span>{tab.label}</span>
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
