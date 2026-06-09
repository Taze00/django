import { useState, useMemo } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';

// Renders one timeline entry's content based on its type.
function TimelineEntry({ event }) {
  if (event.type === 'journey_start') {
    return (
      <div className="tl-entry tl-start">
        <p className="tl-entry-title">{event.label || 'Deine Reise beginnt'}</p>
        <p className="tl-entry-date">{formatTLDate(event.date)}</p>
      </div>
    );
  }
  if (event.type === 'level_up') {
    return (
      <div className="tl-entry tl-levelup">
        <div className="tl-entry-head">
          <span className="tl-entry-ex">{event.exercise}</span>
          <span className="tl-entry-jump">L{event.from_level} → L{event.to_level}</span>
        </div>
        <p className="tl-entry-title">{event.progression_name}</p>
        <p className="tl-entry-date">{formatTLDate(event.date)}</p>
      </div>
    );
  }
  if (event.type === 'streak_milestone') {
    return (
      <div className="tl-entry tl-streak">
        <p className="tl-entry-title">{event.label}</p>
        <p className="tl-entry-date">{formatTLDate(event.date)}</p>
      </div>
    );
  }
  if (event.type === 'first_time') {
    return (
      <div className="tl-entry tl-first">
        <span className="tl-entry-ex">{event.exercise}</span>
        <p className="tl-entry-title">{event.label}</p>
        <p className="tl-entry-date">{formatTLDate(event.date)}</p>
      </div>
    );
  }
  return null;
}

function formatTLDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: 'short', year: 'numeric' });
}

export default function StatisticsView() {
  const workouts = useWorkoutStore(state => state.workouts);
  const streak = useWorkoutStore(state => state.streak);
  const timeline = useWorkoutStore(state => state.timeline);
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

        {timeline.length > 0 && (
          <>
            <p className="history-section-title">— Deine Reise</p>
            <div className="timeline">
              {timeline.map(event => (
                <div key={event.id} className="tl-row">
                  <div className="tl-marker">
                    <span className="tl-dot" />
                    <span className="tl-line" />
                  </div>
                  <TimelineEntry event={event} />
                </div>
              ))}
            </div>
          </>
        )}

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
                                ? (s.drop_set_completed
                                    ? `Drop → ${s.progression_name}`
                                    : 'Drop übersprungen')
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
