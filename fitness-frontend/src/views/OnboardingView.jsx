import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import api from '../api';

const DAYS = [
  { num: 1, name: 'Montag' },
  { num: 2, name: 'Dienstag' },
  { num: 3, name: 'Mittwoch' },
  { num: 4, name: 'Donnerstag' },
  { num: 5, name: 'Freitag' },
  { num: 6, name: 'Samstag' },
  { num: 7, name: 'Sonntag' },
];

// Exercise test config. levelOptions = the self-assessment choices the user
// picks from. defaultLevel = pre-selected sensible middle. testType drives
// whether the test set is a rep counter or a hold timer.
const EXERCISES = [
  {
    id: 1,
    key: 'push',
    name: 'Push-Ups',
    category: 'PUSH',
    testType: 'reps',
    defaultLevel: 4,
    levels: [
      { level: 1, name: 'Wall Push-ups', hint: 'Hände an der Wand' },
      { level: 2, name: 'Incline Push-ups', hint: 'Hände erhöht (Tisch/Bank)' },
      { level: 3, name: 'Knee Push-ups', hint: 'Auf den Knien' },
      { level: 4, name: 'Standard Push-ups', hint: 'Klassisch, voller Körper' },
      { level: 5, name: 'Diamond Push-ups', hint: 'Hände eng zusammen' },
      { level: 6, name: 'Decline Push-ups', hint: 'Füße erhöht' },
      { level: 7, name: 'Pseudo Planche', hint: 'Fortgeschritten' },
    ],
  },
  {
    id: 2,
    key: 'pull',
    name: 'Pull-Ups',
    category: 'PULL',
    testType: 'mixed',
    defaultLevel: 4,
    levels: [
      { level: 1, name: 'Dead Hang', hint: 'Einfach an der Stange hängen', type: 'time' },
      { level: 2, name: 'Scapular Shrugs', hint: 'Hängen + Schultern ziehen', type: 'reps' },
      { level: 3, name: 'Active Hang', hint: 'Aktives Hängen', type: 'time' },
      { level: 4, name: 'Pull-up Negatives', hint: 'Hochspringen, langsam runter', type: 'reps' },
      { level: 5, name: 'Band-Assisted Pull-ups', hint: 'Mit Widerstandsband', type: 'reps' },
      { level: 6, name: 'Standard Pull-ups', hint: 'Voller Klimmzug', type: 'reps' },
      { level: 7, name: 'Chest-to-Bar', hint: 'Fortgeschritten', type: 'reps' },
    ],
  },
  {
    id: 3,
    key: 'plank',
    name: 'Planks',
    category: 'CORE',
    testType: 'time',
    defaultLevel: 3,
    levels: [
      { level: 1, name: 'Knee Plank', hint: 'Auf den Knien' },
      { level: 2, name: 'Incline Plank', hint: 'Hände erhöht' },
      { level: 3, name: 'Standard Plank', hint: 'Voller Körper, gerade Linie' },
      { level: 4, name: 'Feet-Elevated Plank', hint: 'Füße erhöht' },
      { level: 5, name: 'Extended Plank', hint: 'Arme nach vorne gestreckt' },
      { level: 6, name: 'RKC Plank', hint: 'Maximale Spannung' },
      { level: 7, name: 'One-Arm Plank', hint: 'Fortgeschritten' },
    ],
  },
];

// ── Rep counter input ──
function RepTest({ onSubmit }) {
  const [reps, setReps] = useState('');
  return (
    <div className="onb-test-input">
      <input
        className="onb-number-input"
        type="number"
        inputMode="numeric"
        min="0"
        value={reps}
        onChange={e => setReps(e.target.value)}
        autoFocus
        placeholder="0"
      />
      <span className="onb-test-unit">Wiederholungen</span>
      <button
        className="onb-btn-primary"
        onClick={() => onSubmit(parseInt(reps, 10) || 0)}
        disabled={reps === ''}
      >
        Weiter →
      </button>
    </div>
  );
}

// ── Hold timer input ──
function TimeTest({ onSubmit }) {
  const [elapsed, setElapsed] = useState(0);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => setElapsed(p => p + 1), 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [running]);

  const fmt = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

  return (
    <div className="onb-test-input">
      <p className={`onb-timer ${running ? 'running' : ''}`}>{fmt(elapsed)}</p>
      <button className="onb-btn-timer" onClick={() => setRunning(r => !r)}>
        {running ? '⏸ Stop' : elapsed > 0 ? '▶ Weiter' : '▶ Start'}
      </button>
      <button
        className="onb-btn-primary"
        onClick={() => onSubmit(elapsed)}
        disabled={elapsed === 0}
      >
        Weiter →
      </button>
    </div>
  );
}

export default function OnboardingView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);

  // Steps: 0=welcome, 1=days, 2..4=exercise tests, 5=reveal
  const [step, setStep] = useState(0);
  const [selectedDays, setSelectedDays] = useState([1, 2, 4, 5, 6]);
  const [assessments, setAssessments] = useState({}); // {exId: level}
  const [results, setResults] = useState({});         // {exId: testValue}
  const [calibrated, setCalibrated] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // For the per-exercise test screen: track sub-phase (assess | test)
  const [phase, setPhase] = useState('assess');

  const exIndex = step - 2; // 0,1,2 during exercise steps
  const currentEx = exIndex >= 0 && exIndex < EXERCISES.length ? EXERCISES[exIndex] : null;

  const toggleDay = num => setSelectedDays(prev =>
    prev.includes(num) ? prev.filter(d => d !== num) : [...prev, num].sort((a, b) => a - b)
  );

  // Determine the test type for the currently self-assessed level.
  const getTestTypeForLevel = (ex, level) => {
    if (ex.testType === 'mixed') {
      const lvl = ex.levels.find(l => l.level === level);
      return lvl?.type || 'reps';
    }
    return ex.testType;
  };

  const handleAssess = level => {
    setAssessments(prev => ({ ...prev, [currentEx.id]: level }));
    setPhase('test');
  };

  const handleTest = value => {
    setResults(prev => ({ ...prev, [currentEx.id]: value }));
    setPhase('assess');
    if (exIndex < EXERCISES.length - 1) {
      setStep(step + 1);
    } else {
      submitCalibration({ ...results, [currentEx.id]: value });
    }
  };

  const submitCalibration = async (finalResults) => {
    setIsLoading(true);
    setError('');
    try {
      const payload = {
        training_days: selectedDays,
        results: EXERCISES.map(ex => ({
          exercise: ex.id,
          self_assessed_level: assessments[ex.id] ?? ex.defaultLevel,
          test_result: finalResults[ex.id] ?? 0,
        })),
      };
      const res = await api.post('/onboarding/calibrate/', payload);
      setCalibrated(res.data.results);

      // Reload user so onboarding_completed flag updates.
      const userRes = await api.get('/user/');
      useAuthStore.setState({ user: userRes.data });

      setStep(5);
    } catch (err) {
      setError(err.response?.data?.error || 'Kalibrierung fehlgeschlagen. Versuch es nochmal.');
    } finally {
      setIsLoading(false);
    }
  };

  const finish = () => navigate('/');

  const totalSteps = 5; // days + 3 exercises + reveal
  const progress = Math.min(step, totalSteps) / totalSteps;

  return (
    <div className="onb-shell">
      <div className="onb-card">

        {/* ── STEP 0: WELCOME ── */}
        {step === 0 && (
          <div className="onb-screen">
            <p className="onb-eyebrow">Willkommen bei</p>
            <div className="onb-logo">COR<span>VIS</span></div>
            <p className="onb-welcome-text">
              Hey {user?.username || 'Athlet'}. Bevor du startest, findet CORVIS dein
              richtiges Level — du schätzt dich ein, machst einen kurzen Test, und
              wir justieren automatisch.
            </p>
            <button className="onb-btn-primary" onClick={() => setStep(1)}>
              Los geht's →
            </button>
          </div>
        )}

        {/* ── STEP 1: TRAINING DAYS ── */}
        {step === 1 && (
          <div className="onb-screen">
            <p className="onb-eyebrow">— Schritt 1</p>
            <h2 className="onb-title">Deine<br />Trainingstage</h2>
            <p className="onb-sub">An welchen Tagen willst du trainieren? Empfehlung: 4–5 Tage.</p>
            <div className="onb-days">
              {DAYS.map(d => (
                <button
                  key={d.num}
                  className={`onb-day ${selectedDays.includes(d.num) ? 'active' : ''}`}
                  onClick={() => toggleDay(d.num)}
                >
                  <span>{d.name}</span>
                  <span className="onb-day-dot" />
                </button>
              ))}
            </div>
            <button
              className="onb-btn-primary"
              onClick={() => setStep(2)}
              disabled={selectedDays.length === 0}
            >
              Weiter →
            </button>
          </div>
        )}

        {/* ── STEPS 2-4: EXERCISE TESTS ── */}
        {currentEx && (
          <div className="onb-screen">
            <p className="onb-eyebrow">— {currentEx.category} · Übung {exIndex + 1}/3</p>

            {phase === 'assess' && (
              <>
                <h2 className="onb-title">{currentEx.name}</h2>
                <p className="onb-sub">Welche Variante schaffst du? Schätz dich ein — wir testen es gleich.</p>
                <div className="onb-levels">
                  {currentEx.levels.map(l => (
                    <button
                      key={l.level}
                      className={`onb-level ${(assessments[currentEx.id] ?? currentEx.defaultLevel) === l.level ? 'active' : ''}`}
                      onClick={() => handleAssess(l.level)}
                    >
                      <span className="onb-level-num">L{l.level}</span>
                      <span className="onb-level-info">
                        <span className="onb-level-name">{l.name}</span>
                        <span className="onb-level-hint">{l.hint}</span>
                      </span>
                      <span className="onb-level-arrow">→</span>
                    </button>
                  ))}
                </div>
              </>
            )}

            {phase === 'test' && (() => {
              const level = assessments[currentEx.id] ?? currentEx.defaultLevel;
              const levelInfo = currentEx.levels.find(l => l.level === level);
              const testType = getTestTypeForLevel(currentEx, level);
              return (
                <>
                  <h2 className="onb-title">{levelInfo?.name}</h2>
                  <p className="onb-sub">
                    {testType === 'time'
                      ? 'Halte so lange du kannst. CORVIS misst die Zeit.'
                      : 'Mach so viele saubere Wiederholungen wie du schaffst.'}
                  </p>
                  {testType === 'time'
                    ? <TimeTest onSubmit={handleTest} />
                    : <RepTest onSubmit={handleTest} />}
                  <button className="onb-btn-back" onClick={() => setPhase('assess')}>
                    ← Andere Variante wählen
                  </button>
                </>
              );
            })()}
          </div>
        )}

        {/* ── STEP 5: REVEAL ── */}
        {step === 5 && (
          <div className="onb-screen">
            {isLoading ? (
              <>
                <div className="onb-logo">COR<span>VIS</span></div>
                <div className="onb-spinner" />
                <p className="onb-sub">CORVIS berechnet dein Level…</p>
              </>
            ) : (
              <>
                <p className="onb-eyebrow">— Deine Kalibrierung</p>
                <h2 className="onb-title">Dein Start<br />steht fest.</h2>
                <p className="onb-sub">CORVIS hat dein Level aus deinem Test berechnet:</p>

                <div className="onb-reveal-list">
                  {calibrated?.map((r, i) => (
                    <div key={r.exercise_id} className="onb-reveal-card" style={{ animationDelay: `${0.15 + i * 0.12}s` }}>
                      <div className="onb-reveal-top">
                        <span className="onb-reveal-ex">{r.exercise}</span>
                        {r.reason === 'up' && <span className="onb-reveal-tag up">↑ höher als gedacht</span>}
                        {r.reason === 'down' && <span className="onb-reveal-tag down">angepasst</span>}
                        {r.reason === 'stay' && <span className="onb-reveal-tag stay">✓ bestätigt</span>}
                      </div>
                      <div className="onb-reveal-body">
                        <span className="onb-reveal-level">L{r.calibrated_level}</span>
                        <div className="onb-reveal-detail">
                          <span className="onb-reveal-prog">{r.progression_name}</span>
                          <span className="onb-reveal-target">
                            Ziel: {r.target_value}{r.target_type === 'time' ? 's' : ' Wdh'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {error && <p className="onb-error">{error}</p>}

                <button className="onb-btn-primary" onClick={finish}>
                  Training starten →
                </button>
              </>
            )}
          </div>
        )}

        {/* ── PROGRESS BAR ── */}
        {step > 0 && step < 5 && (
          <div className="onb-progress">
            <div className="onb-progress-fill" style={{ width: `${progress * 100}%` }} />
          </div>
        )}
      </div>
    </div>
  );
}
