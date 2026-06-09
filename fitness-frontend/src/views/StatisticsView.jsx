import { useState, useMemo } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';

export default function StatisticsView() {
  const workouts = useWorkoutStore(state => state.workouts);
  const streak = useWorkoutStore(state => state.streak);
  const [expandedDate, setExpandedDate] = useState(null);

  // Streak comes from the backend (training-day based, rest days excused).
  const currentStreak = streak.current;
  const longestStreak = streak.longest;

  const stats = useMemo(() => {
    const r = { pushReps: 0, pullReps: 0, plankSeconds: 0 };
    workouts.forEach(w => {
      (w.sets || []).forEach(s => {
        if (s.exercise_name === 'Push-ups' && s.reps) r.pushReps += s.reps;
        else if (s.exercise_name === 'Pull-ups' && s.reps) r.pullReps += s.reps;
        else if (s.exercise_name === 'Planks' && s.seconds) r.plankSeconds += s.seconds;
      });
    });
    return r;
  }, [workouts]);

  const completedWorkouts = workouts
    .filter(w => w.sets && w.sets.length > 0)
    .sort((a, b) => new Date(b.date) - new Date(a.date));

  const formatDate = ds => new Date(ds).toLocaleDateString('de-DE', {
    weekday: 'long', day: 'numeric', month: 'long'
  });

  const groupSets = workout => {
    const g = {};
    (workout.sets || []).forEach(s => {
      if (!g[s.exercise_name]) g[s.exercise_name] = [];
      g[s.exercise_name].push(s);
    });
    return g;
  };

  return (
    <>
      <div className="header">
        <div className="header-content">
          <div className="header-logo">COR<span>VIS</span></div>
        </div>
      </div>

      <div className="main-content">
        <div className="stats-row">
          <div className="stats-cell">
            <p className="stats-cell-val">{stats.pushReps}</p>
            <p className="stats-cell-label">Push-ups</p>
          </div>
          <div className="stats-cell">
            <p className="stats-cell-val">{stats.pullReps}</p>
            <p className="stats-cell-label">Pull-ups</p>
          </div>
          <div className="stats-cell">
            <p className="stats-cell-val">{Math.floor(stats.plankSeconds / 60)}m</p>
            <p className="stats-cell-label">Core</p>
          </div>
        </div>

        <div className="streak-row">
          <div className="streak-cell">
            <p className="streak-val">{currentStreak}</p>
            <p className="streak-label">Aktuelle Serie</p>
          </div>
          <div className="streak-cell">
            <p className="streak-val">{longestStreak}</p>
            <p className="streak-label">Längste Serie</p>
          </div>
        </div>

        {completedWorkouts.length > 0 && (
          <>
            <p className="history-section-title">— Verlauf</p>
            {completedWorkouts.map(workout => (
              <div key={workout.id} className="history-card">
                <button
                  className="history-card-header"
                  onClick={() => setExpandedDate(expandedDate === workout.date ? null : workout.date)}
                >
                  <span className="history-card-date">{formatDate(workout.date)}</span>
                  <span className="history-card-toggle">{expandedDate === workout.date ? '−' : '+'}</span>
                </button>
                {expandedDate === workout.date && (
                  <div className="history-card-body">
                    {Object.entries(groupSets(workout)).map(([name, sets]) => (
                      <div key={name} className="history-ex-group">
                        <p className="history-ex-name">{name}</p>
                        <div className="history-sets">
                          {sets.map((s, i) => (
                            <span key={i} className={`history-set-chip ${s.is_drop_set ? 'drop' : ''}`}>
                              {s.is_drop_set
                                ? (s.drop_set_completed ? 'Drop ✓' : 'Drop')
                                : s.reps ? `S${s.set_number}: ${s.reps}` : `S${s.set_number}: ${s.seconds}s`}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </div>
    </>
  );
}
