import { useNavigate } from 'react-router-dom';

export default function ExercisesView() {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Calisthenics</h1>
        </div>
      </div>

      <div className="main-content">
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏋️</div>
          <h2 style={{ fontSize: '24px', marginBottom: '8px', color: '#f1f5f9' }}>Exercises</h2>
          <p style={{ color: '#94a3b8' }}>Coming Soon...</p>
        </div>
      </div>
    </div>
  );
}
