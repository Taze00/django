import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

const ALL_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function HomeView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const initialize = useWorkoutStore(state => state.initialize);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const workouts = useWorkoutStore(state => state.workouts);
  const trainingDays = useWorkoutStore(state => state.trainingDays);
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
    } catch {
      // ignore — UI stays as-is
    } finally {
      setResting(false);
    }
  };

  // Show the "Heute nicht" affordance only on an untrained, unrested training day.
  const showRestOption =
    streak.is_training_day_today && !streak.trained_today && !streak.rested_today;

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
          {streak.current > 0 && (
            <div className="header-streak" title={`Längste Serie: ${streak.longest}`}>
              <span className="streak-flame">🔥</span>
              <span className="streak-count">{streak.current}</span>
            </div>
          )}
        </div>
      </div>

      <div className="main-content">
        {/* Week strip */}
        <div className="week-strip">
          {ALL_DAYS.map((day, idx) => {
            const dayNum = idx + 1;
            const isTraining = trainingDays.includes(dayNum);
            const isDone = weekStatus[day];
            const isToday = day === todayName;
            return (
              <div key={day} className={`week-day ${isToday ? 'today' : ''} ${isDone ? 'completed' : ''} ${!isTraining ? 'rest' : ''}`}>
                <p className="week-day-name">{day}</p>
                <div className="week-day-dot">
                  {isDone && <span className="week-dot-inner">✓</span>}
                </div>
              </div>
            );
          })}
        </div>

        {/* Exercise cards — dynamic from store */}
        <div className="exercise-cards">
          {exercises.map(ex => {
            const prog = userProgressions[String(ex.id)];
            const currentProg = prog?.current_progression;
            return (
              <div key={ex.id} className="ex-card-home">
                <div className="ex-card-left">
                  <p className="ex-card-cat">{ex.category}</p>
                  <p className="ex-card-name">{ex.name}</p>
                  <p className="ex-card-prog">{currentProg?.name || '—'}</p>
                </div>
                <div className="ex-card-right">
                  <p className="ex-card-level">{currentProg?.level ?? '—'}</p>
                  <p className="ex-card-level-label">Level</p>
                </div>
              </div>
            );
          })}
        </div>

        <button className="btn-start" onClick={() => navigate('/workout')}>
          Training starten →
        </button>

        {streak.rested_today && (
          <p className="rest-note">Heute pausiert — deine Serie bleibt. Erhol dich gut. 💪</p>
        )}

        {showRestOption && !restConfirm && (
          <button className="btn-rest" onClick={() => setRestConfirm(true)}>
            Heute nicht
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
    </>
  );
}
