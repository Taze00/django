import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

const ALL_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAY_SHORT = { Mon: 'Mo', Tue: 'Di', Wed: 'Mi', Thu: 'Do', Fri: 'Fr', Sat: 'Sa', Sun: 'So' };
const MAX_LEVEL = 7;

// ── Radar triangle SVG — labels inside, scales with screen width ──
function StrengthTriangle({ push, pull, core }) {
  const clamp = v => Math.max(0, Math.min(MAX_LEVEL, v || 0));
  const p = clamp(push), u = clamp(pull), c = clamp(core);

  const C = 150, R = 125;
  const ang = { push: -90, pull: 30, core: 150 };
  const pt = (key, frac) => {
    const a = ang[key] * Math.PI / 180;
    return [C + Math.cos(a) * R * frac, C + Math.sin(a) * R * frac];
  };
  const triStr = frac => ['push', 'pull', 'core'].map(k => pt(k, frac).join(',')).join(' ');
  const dataPts = [pt('push', p / MAX_LEVEL), pt('pull', u / MAX_LEVEL), pt('core', c / MAX_LEVEL)];
  const dataStr = dataPts.map(d => d.join(',')).join(' ');

  // Full-size vertex positions for label placement
  const [px, py] = pt('push', 1);  // ≈ [150, 25]
  const [rx, ry] = pt('pull', 1);  // ≈ [258, 212]
  const [lx, ly] = pt('core', 1);  // ≈ [42, 212]

  return (
    <svg viewBox="-42 -46 384 350" className="home-triangle-svg">
      {[1, 0.715, 0.43, 0.145].map((f, i) => (
        <polygon key={i} points={triStr(f)} fill="none" stroke="#1d1d1d" strokeWidth="1.2" />
      ))}
      {['push', 'pull', 'core'].map((k, i) => {
        const [x, y] = pt(k, 1);
        return <line key={i} x1={C} y1={C} x2={x} y2={y} stroke="#181818" strokeWidth="1" />;
      })}
      <polygon points={dataStr} fill="rgba(255,77,0,0.16)" stroke="#FF4D00" strokeWidth="2.5" strokeLinejoin="round" />
      {dataPts.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="5.5" fill="#FF4D00" stroke="#080808" strokeWidth="2" />
      ))}

      {/* Push — above top vertex */}
      <text x={px} y={py - 25} textAnchor="middle" fontSize="9"
            fontFamily="DM Mono, monospace" letterSpacing="2" fill="#999">PUSH</text>
      <text x={px} y={py - 2} textAnchor="middle" fontSize="26"
            fontFamily="Bebas Neue, sans-serif" letterSpacing="1" fill="#f0ede8">L{p}</text>

      {/* Pull — right of right vertex */}
      <text x={rx + 14} y={ry - 8} textAnchor="start" fontSize="9"
            fontFamily="DM Mono, monospace" letterSpacing="2" fill="#999">PULL</text>
      <text x={rx + 14} y={ry + 20} textAnchor="start" fontSize="26"
            fontFamily="Bebas Neue, sans-serif" letterSpacing="1" fill="#f0ede8">L{u}</text>

      {/* Core — left of left vertex */}
      <text x={lx - 14} y={ly - 8} textAnchor="end" fontSize="9"
            fontFamily="DM Mono, monospace" letterSpacing="2" fill="#999">CORE</text>
      <text x={lx - 14} y={ly + 20} textAnchor="end" fontSize="26"
            fontFamily="Bebas Neue, sans-serif" letterSpacing="1" fill="#f0ede8">L{c}</text>
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
    <div className="home-shell">
      {/* orange radial glow — fills entire screen behind content */}
      <div className="home-glow" aria-hidden="true" />

      {/* ── LOGO — schwebt frei, kein Kasten ── */}
      <div className="header home-header">
        <div className="header-content">
          <div className="header-logo">COR<span>VIS</span></div>
        </div>
      </div>

      {/* ── WOCHENTAGE-LEISTE ── */}
      <div className="week-bar">
        {ALL_DAYS.map(day => {
          const isDone = weekStatus[day];
          const isToday = day === todayName;
          return (
            <div key={day} className={`week-bar-day${isToday ? ' today' : ''}${isDone ? ' completed' : ''}`}>
              <span className="week-bar-label">{DAY_SHORT[day]}</span>
            </div>
          );
        })}
      </div>

      {/* ── MAIN CONTENT — flex: 1, verteilt Raum gleichmäßig ── */}
      <div className="home-content">

        {/* Gesamtstärke */}
        <section className="home-hero">
          <p className="home-hero-eyebrow">— Gesamtstärke</p>
          <span className="home-hero-total">{levels.total}</span>
        </section>

        {/* Stärke-Dreieck — section fills the dead vertical space */}
        <section className="home-triangle-section">
          <StrengthTriangle push={levels.push} pull={levels.pull} core={levels.core} />
        </section>

        {/* Stats */}
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

        {/* Buttons — bleibt unten */}
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
    </div>
  );
}
