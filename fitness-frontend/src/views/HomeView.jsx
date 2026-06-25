import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

const ALL_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAY_SHORT = { Mon: 'Mo', Tue: 'Di', Wed: 'Mi', Thu: 'Do', Fri: 'Fr', Sat: 'Sa', Sun: 'So' };
const MAX_LEVEL = 7;

// ── Radar triangle SVG — translated from the design's DC script ──
function StrengthTriangle({ push, pull, core }) {
  const clamp = v => Math.max(0, Math.min(MAX_LEVEL, v || 0));
  const p = clamp(push), u = clamp(pull), c = clamp(core);

  const C = 150, R = 112;
  const ang = { push: -90, pull: 30, core: 150 };
  const pt = (key, frac) => {
    const a = ang[key] * Math.PI / 180;
    return [C + Math.cos(a) * R * frac, C + Math.sin(a) * R * frac];
  };
  const triStr = frac => ['push', 'pull', 'core'].map(k => pt(k, frac).join(',')).join(' ');
  const dataPts = [pt('push', p / MAX_LEVEL), pt('pull', u / MAX_LEVEL), pt('core', c / MAX_LEVEL)];
  const dataStr = dataPts.map(d => d.join(',')).join(' ');

  return (
    <svg viewBox="0 0 300 300" width="240" height="240" style={{ display: 'block', overflow: 'visible' }}>
      {[1, 0.715, 0.43, 0.145].map((f, i) => (
        <polygon key={i} points={triStr(f)} fill="none" stroke="#1d1d1d" strokeWidth="1" />
      ))}
      {['push', 'pull', 'core'].map((k, i) => {
        const [x, y] = pt(k, 1);
        return <line key={i} x1={C} y1={C} x2={x} y2={y} stroke="#181818" strokeWidth="1" />;
      })}
      <polygon points={dataStr} fill="rgba(255,77,0,0.16)" stroke="#FF4D00" strokeWidth="2.5" strokeLinejoin="round" />
      {dataPts.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="4.5" fill="#FF4D00" stroke="#080808" strokeWidth="2" />
      ))}
    </svg>
  );
}

export default function HomeView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const initialize = useWorkoutStore(state => state.initialize);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const workouts = useWorkoutStore(state => state.workouts);
  const streak = useWorkoutStore(state => state.streak);
  const markRestDay = useWorkoutStore(state => state.markRestDay);
  const isLoading = useWorkoutStore(state => state.isLoading);
  const [restConfirm, setRestConfirm] = useState(false);
  const [resting, setResting] = useState(false);

  useEffect(() => {
    if (user && user.onboarding_completed === false) navigate('/onboarding');
  }, [user, navigate]);

  useEffect(() => {
    if (user && user.onboarding_completed === true) {
      useWorkoutStore.setState({ isInitialized: false });
      initialize();
    }
  }, [user?.onboarding_completed, initialize]);

  // Derive per-category levels
  const levels = useMemo(() => {
    const get = cat => {
      const ex = exercises.find(e => e.category === cat);
      if (!ex) return 0;
      return userProgressions[String(ex.id)]?.current_progression?.level ?? 0;
    };
    const push = get('PUSH'), pull = get('PULL'), core = get('CORE');
    const total = push + pull + core;
    const avg = exercises.length > 0 ? (total / 3) : 0;
    return { push, pull, core, total, avg };
  }, [exercises, userProgressions]);

  const weekStatus = useMemo(() => {
    const now = new Date();
    const dayIndex = now.getDay();
    const monday = new Date(now);
    monday.setDate(now.getDate() - (dayIndex === 0 ? 6 : dayIndex - 1));
    monday.setHours(0, 0, 0, 0);
    const status = {};
    ALL_DAYS.forEach(d => { status[d] = false; });
    workouts.forEach(workout => {
      const d = new Date(workout.date);
      d.setHours(0, 0, 0, 0);
      if (d >= monday) {
        const dow = d.getDay();
        const num = dow === 0 ? 7 : dow;
        status[ALL_DAYS[num - 1]] = true;
      }
    });
    return status;
  }, [workouts]);

  const todayName = useMemo(() => {
    const i = new Date().getDay();
    return ALL_DAYS[i === 0 ? 6 : i - 1];
  }, []);

  const handleRest = async () => {
    setResting(true);
    try {
      await markRestDay();
      setRestConfirm(false);
    } catch { /* ignore */ } finally {
      setResting(false);
    }
  };

  const showRestOption =
    streak.is_training_day_today && !streak.trained_today && !streak.rested_today;

  const completedWorkouts = workouts.filter(w => w.completed).length;

  if (isLoading) {
    return (
      <div className="loading-shell">
        <div className="loading-logo">COR<span>VIS</span></div>
        <div className="loading-spinner" />
        <p className="loading-text">Loading</p>
      </div>
    );
  }

  return (
    <>
      <div className="header">
        <div className="header-content">
          <div className="header-logo">COR<span>VIS</span></div>
        </div>
      </div>

      {/* orange radial glow — starts below header */}
      <div className="home-glow" aria-hidden="true" />

      {/* ── WOCHENTAGE-LEISTE — direkt unter Header ── */}
      <div className="week-bar">
        {ALL_DAYS.map(day => {
          const isDone = weekStatus[day];
          const isToday = day === todayName;
          return (
            <div key={day} className={`week-bar-day${isToday ? ' today' : ''}${isDone ? ' completed' : ''}`}>
              <span className="week-bar-label">{DAY_SHORT[day]}</span>
              <div className="week-bar-line" />
            </div>
          );
        })}
      </div>

      <div className="main-content home-main">

        {/* ── HERO: Gesamtstärke ── */}
        <section className="home-hero">
          <p className="home-hero-eyebrow">— Gesamtstärke</p>
          <span className="home-hero-total">{levels.total}</span>
        </section>

        {/* ── STÄRKE-DREIECK ── */}
        <section className="home-triangle-section">
          <div className="home-triangle-wrap">
            <div className="home-vertex home-vertex-top">
              <span className="home-vertex-cat">Push</span>
              <span className="home-vertex-level">L{levels.push}</span>
            </div>
            <div className="home-vertex home-vertex-br">
              <span className="home-vertex-cat">Pull</span>
              <span className="home-vertex-level">L{levels.pull}</span>
            </div>
            <div className="home-vertex home-vertex-bl">
              <span className="home-vertex-cat">Core</span>
              <span className="home-vertex-level">L{levels.core}</span>
            </div>
            <div className="home-triangle-svg">
              <StrengthTriangle push={levels.push} pull={levels.pull} core={levels.core} />
            </div>
          </div>
        </section>

        {/* ── STATS ROW ── */}
        <section className="home-stats">
          <div className="home-stat">
            <span className="home-stat-val home-stat-orange">{streak.current}</span>
            <span className="home-stat-label">🔥 Serie</span>
          </div>
          <div className="home-stat">
            <span className="home-stat-val">{completedWorkouts}</span>
            <span className="home-stat-label">Workouts</span>
          </div>
          <div className="home-stat">
            <span className="home-stat-val">{levels.avg.toFixed(1)}</span>
            <span className="home-stat-label">Ø Level</span>
          </div>
        </section>

        {/* ── ACTION ── */}
        <div className="home-bottom">
          <button className="btn-start" onClick={() => navigate('/workout')}>
            Training starten →
          </button>

          {streak.rested_today && (
            <p className="rest-note">Heute pausiert — deine Serie bleibt. Erhol dich gut. 💪</p>
          )}

          {showRestOption && !restConfirm && (
            <button className="btn-rest-text" onClick={() => setRestConfirm(true)}>
              Ruhetag einlegen — deine Serie bleibt erhalten
            </button>
          )}

          {showRestOption && restConfirm && (
            <div className="rest-confirm">
              <p className="rest-confirm-text">
                Heute pausieren? Deine Serie bleibt erhalten — kein Verlust.
              </p>
              <div className="rest-confirm-btns">
                <button className="btn-rest-cancel" onClick={() => setRestConfirm(false)} disabled={resting}>
                  Doch trainieren
                </button>
                <button className="btn-rest-confirm" onClick={handleRest} disabled={resting}>
                  {resting ? '...' : 'Ja, pausieren'}
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </>
  );
}
