function Confetti({ count = 60 }) {
  const colors = ['#FF4D00', '#ff6a2a', '#f0ede8', '#ffb347', '#fff'];
  const pieces = Array.from({ length: count }, (_, i) => ({
    id: i,
    color: colors[i % colors.length],
    left: Math.random() * 100,
    delay: Math.random() * 1.2,
    size: 5 + Math.random() * 7,
    duration: 1.8 + Math.random() * 1.4,
    rotate: Math.random() * 360,
  }));
  return (
    <div className="confetti-wrap" aria-hidden="true">
      {pieces.map(p => (
        <div
          key={p.id}
          className="confetti-piece"
          style={{
            left: `${p.left}%`,
            width: p.size,
            height: p.size * 0.6,
            background: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
            transform: `rotate(${p.rotate}deg)`,
          }}
        />
      ))}
    </div>
  );
}

function UpgradeCard({ item, idx }) {
  return (
    <div className="lvl-card" style={{ animationDelay: `${0.3 + idx * 0.1}s` }}>
      <div className="lvl-card-top">
        <span className="lvl-card-arrow">↑</span>
        <span className="lvl-card-ex">{item.exercise}</span>
      </div>
      <div className="lvl-card-body">
        <div className="lvl-num-wrap">
          <span className="lvl-num old">{item.from_level}</span>
          <span className="lvl-arrow-big">→</span>
          <span className="lvl-num new">{item.to_level}</span>
        </div>
        {item.to_progression && (
          <p className="lvl-new-name">{item.to_progression}</p>
        )}
        {item.is_max_level && (
          <p className="lvl-max-badge">MAX LEVEL</p>
        )}
      </div>
    </div>
  );
}

function DowngradeCard({ item, idx }) {
  return (
    <div className="lvl-card lvl-card--down" style={{ animationDelay: `${0.3 + idx * 0.1}s` }}>
      <div className="lvl-card-top">
        <span className="lvl-card-arrow down">↓</span>
        <span className="lvl-card-ex">{item.exercise}</span>
      </div>
      <div className="lvl-card-body">
        <div className="lvl-num-wrap">
          <span className="lvl-num old">{item.from_level}</span>
          <span className="lvl-arrow-big">→</span>
          <span className="lvl-num new dim">{item.to_level}</span>
        </div>
        {item.to_progression && (
          <p className="lvl-new-name muted">{item.to_progression}</p>
        )}
      </div>
    </div>
  );
}

function formatTime(totalSeconds) {
  const s = Math.round(totalSeconds);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return rem > 0 ? `${m}:${String(rem).padStart(2, '0')} min` : `${m} min`;
}

function getNextTrainingDay(trainingDays) {
  if (!trainingDays?.length) return null;
  // trainingDays: 1=Mon..7=Sun → JS Date.getDay(): 0=Sun..6=Sat
  const toJs = d => (d === 7 ? 0 : d);
  const jsDays = trainingDays.map(toJs);
  const today = new Date();
  const todayJs = today.getDay();
  const names = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
  for (let i = 1; i <= 7; i++) {
    const next = (todayJs + i) % 7;
    if (jsDays.includes(next)) {
      if (i === 1) return `Morgen · ${names[next]}`;
      if (i === 2) return `Übermorgen · ${names[next]}`;
      return names[next];
    }
  }
  return null;
}

function SessionBlock({ workouts }) {
  const todayStr = new Date().toISOString().slice(0, 10);
  const todayWorkout = workouts?.find(w => w.date === todayStr && w.completed);

  const exSummary = {};
  if (todayWorkout?.sets?.length) {
    for (const s of todayWorkout.sets) {
      if (s.is_drop_set && !s.drop_set_completed) continue;
      const name = s.exercise_name;
      if (!exSummary[name]) exSummary[name] = { reps: 0, seconds: 0, hasReps: false, hasTime: false };
      if (s.reps != null) { exSummary[name].reps += s.reps; exSummary[name].hasReps = true; }
      if (s.seconds != null) { exSummary[name].seconds += s.seconds; exSummary[name].hasTime = true; }
    }
  }

  const entries = Object.entries(exSummary);
  if (!entries.length) return null;

  return (
    <div className="pm-block pm-block--session">
      <p className="pm-block-label">Heute geleistet</p>
      {entries.map(([name, data]) => (
        <div key={name} className="pm-session-row">
          <span className="pm-session-ex">{name}</span>
          <span className="pm-session-val">
            {data.hasReps && `${data.reps} Wdh.`}
            {data.hasTime && formatTime(data.seconds)}
          </span>
        </div>
      ))}
    </div>
  );
}

function StreakBlock({ streak }) {
  if (!streak?.current) return null;
  const isRecord = streak.current > 1 && streak.current === streak?.longest;
  return (
    <div className="pm-block pm-block--streak">
      <div className="pm-streak-num">{streak.current}</div>
      <div className="pm-streak-right">
        <span className="pm-streak-label">
          {streak.current === 1 ? 'Tag am Stück' : 'Tage am Stück'}
        </span>
        {isRecord && <span className="pm-streak-record">Neuer Rekord</span>}
      </div>
    </div>
  );
}

function NextBlock({ trainingDays }) {
  const nextDay = getNextTrainingDay(trainingDays);
  if (!nextDay) return null;
  return (
    <div className="pm-block pm-block--next">
      <span className="pm-next-label">Nächstes Training</span>
      <span className="pm-next-val">{nextDay}</span>
    </div>
  );
}

export default function ProgressionModal({ upgrades = [], downgrades = [], workouts = [], streak = {}, trainingDays = [], onClose }) {
  const hasUpgrades = upgrades.length > 0;
  const hasDowngrades = downgrades.length > 0;
  const hasChanges = upgrades.length + downgrades.length > 0;

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      {hasUpgrades && <Confetti />}

      <div className="lvl-modal-box">

        {/* ── LEVEL-UP STATE ── */}
        {hasUpgrades && (
          <>
            <div className="pm-hero pm-hero--up">
              <p className="pm-hero-eyebrow">— Level Update</p>
              <h2 className="pm-hero-title">LEVEL<span>UP</span></h2>
              <p className="pm-hero-sub">Du hast die Zielwerte erreicht.</p>
            </div>
            <div className="lvl-cards">
              {upgrades.map((u, i) => <UpgradeCard key={i} item={u} idx={i} />)}
            </div>
          </>
        )}

        {/* ── DOWNGRADE STATE ── */}
        {!hasUpgrades && hasDowngrades && (
          <>
            <div className="pm-hero pm-hero--down">
              <p className="pm-hero-eyebrow">— Level Update</p>
              <h2 className="pm-hero-title">NEUES<span>LEVEL</span></h2>
              <p className="pm-hero-sub">CORVIS hat dein Level angepasst — das macht dich langfristig stärker.</p>
            </div>
            <div className="lvl-cards">
              {downgrades.map((d, i) => <DowngradeCard key={i} item={d} idx={i} />)}
            </div>
          </>
        )}

        {/* ── NO-CHANGE STATE ── */}
        {!hasChanges && (
          <div className="pm-hero pm-hero--done">
            <p className="pm-hero-eyebrow">— Workout</p>
            <h2 className="pm-hero-title">DONE<span>.</span></h2>
            <p className="pm-hero-sub">Sauber durchgezogen.</p>
          </div>
        )}

        {/* ── SESSION + STREAK + NEXT ── */}
        <div className="pm-summary">
          <SessionBlock workouts={workouts} />
          <StreakBlock streak={streak} />
          <NextBlock trainingDays={trainingDays} />
        </div>

        <button className="modal-close-btn" onClick={onClose}>
          Fertig →
        </button>
      </div>
    </div>
  );
}
