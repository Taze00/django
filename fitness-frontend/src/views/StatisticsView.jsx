import { useState } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import { formatTimeShort } from '../utils/formatTime';

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

// Was in einem Satz steht. Der Test muss auf null pruefen, nicht auf
// Wahrheitswert: 0 Wiederholungen sind ein gueltiger Eintrag - wer keine
// einzige geschafft hat, traegt 0 ein. Mit `s.reps ? ...` fiel dieser Fall in
// den Zeitzweig und ergab "S1: nulls", weil seconds null war.
function satzText(s) {
  if (s.is_drop_set) {
    return s.drop_set_completed ? `Drop → ${s.progression_name}` : 'Drop übersprungen';
  }
  if (s.reps != null) return `S${s.set_number}: ${s.reps}`;
  if (s.seconds != null) return `S${s.set_number}: ${s.seconds}s`;
  return `S${s.set_number}: —`;
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
  const serverStats = useWorkoutStore(state => state.stats);
  const workoutsCount = useWorkoutStore(state => state.workoutsCount);
  const workoutsNextPage = useWorkoutStore(state => state.workoutsNextPage);
  const isLoadingMore = useWorkoutStore(state => state.isLoadingMore);
  const loadMoreWorkouts = useWorkoutStore(state => state.loadMoreWorkouts);
  const [expandedDate, setExpandedDate] = useState(null);

  // Streak comes from the backend (training-day based, rest days excused).
  const currentStreak = streak.current;
  const longestStreak = streak.longest;

  // Die Summen kommen vom Server. Hier ueber `workouts` zu summieren ging nur
  // bis zum 20. Training: die Liste ist paginiert (PAGE_SIZE 20), ab dem 21.
  // fiel die Gesamtsumme, ohne dass irgendwo stand warum.
  const stats = {
    pushReps: serverStats.push_reps || 0,
    pullReps: serverStats.pull_reps || 0,
    pullSeconds: serverStats.pull_seconds || 0,
    plankSeconds: serverStats.plank_seconds || 0,
  };

  // Solange es noch keine Wiederholung gibt, ist die Hang-Zeit die Leistung -
  // dann steht sie oben statt einer nichtssagenden 0.
  const pullHead = stats.pullReps > 0
    ? String(stats.pullReps)
    : (stats.pullSeconds > 0 ? formatTimeShort(stats.pullSeconds) : '0');
  const pullSub = stats.pullReps > 0
    ? (stats.pullSeconds > 0 ? `+ ${formatTimeShort(stats.pullSeconds)} Hang` : null)
    : (stats.pullSeconds > 0 ? 'Hang' : null);

  // Dieselbe Regel wie ueberall sonst: ein Tag zaehlt, wenn das Workout
  // abgeschlossen ist. Vorher genuegte hier ein einziger Satz - ein
  // abgebrochenes Training stand damit im Verlauf, ohne anderswo zu zaehlen.
  const completedWorkouts = workouts
    .filter(w => w.completed)
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
            <p className="stats-cell-val">{pullHead}</p>
            <p className="stats-cell-label">Pull-ups</p>
            {pullSub && <p className="stats-cell-sub">{pullSub}</p>}
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
                  {workout.duration_seconds > 0 && (
                    <span className="history-card-dauer">{formatTimeShort(workout.duration_seconds)}</span>
                  )}
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
                              {satzText(s)}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {workoutsNextPage && (
              <button
                className="btn-mehr-laden"
                onClick={() => loadMoreWorkouts()}
                disabled={isLoadingMore}
              >
                {isLoadingMore
                  ? 'Lädt …'
                  : `Weitere ${workoutsCount - completedWorkouts.length} von ${workoutsCount} laden`}
              </button>
            )}
          </>
        )}
      </div>
    </>
  );
}
