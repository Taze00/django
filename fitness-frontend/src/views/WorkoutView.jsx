import { useState, useEffect, useMemo } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import { useNavigate } from 'react-router-dom';
import SetInput from '../components/SetInput';
import TimerInput from '../components/TimerInput';
import RestTimer from '../components/RestTimer';
import DropSetInstructions from '../components/DropSetInstructions';
import WarmupChecklist from '../components/WarmupChecklist';
import CooldownChecklist from '../components/CooldownChecklist';
import ProgressionModal from '../components/ProgressionModal';
import FormTip from '../components/FormTip';
import { requestWakeLock, releaseWakeLock } from '../utils/wakeLock';

const REST_TIMES = { normal: 180, afterDrop: 300 };

// Passt ein gespeicherter Satz zu diesem Schritt?
function passtZuSchritt(satz, schritt) {
  return satz.exercise_name === schritt.exerciseName
    && satz.set_number === schritt.setNumber
    && Boolean(satz.is_drop_set) === (schritt.type === 'drop');
}

// Erster Schritt, zu dem noch kein Satz gespeichert ist. Nach einem Neuladen
// geht der Ablauf dort weiter, statt wieder bei Schritt 1 zu beginnen.
function naechsterOffenerSchritt(schritte, saetze) {
  const offen = schritte.findIndex(
    schritt => !saetze.some(satz => passtZuSchritt(satz, schritt)));
  return offen === -1 ? schritte.length : offen;
}

function satzWert(satz) {
  if (satz.is_drop_set) {
    return satz.drop_set_completed ? `Drop → ${satz.progression_name}` : 'Drop übersprungen';
  }
  if (satz.reps != null) return `${satz.reps}`;
  if (satz.seconds != null) return `${satz.seconds}s`;
  return '—';
}

// Was in dieser Sitzung schon steht - damit nach einem Neuladen sichtbar ist,
// was bereits gespeichert wurde. Jeder Chip ist zugleich der Weg zur
// Korrektur: ein Tippfehler in Satz 1 laesst sich auch von Schritt 8 aus
// heilen, ohne sich Schritt fuer Schritt zurueckzuhangeln.
function ErfassteSaetze({ saetze, onKorrigieren }) {
  if (!saetze.length) return null;
  return (
    <div className="wv-erfasst">
      <p className="wv-erfasst-titel">Bereits eingetragen · antippen zum Ändern</p>
      <div className="wv-erfasst-liste">
        {saetze.map(satz => (
          <button
            type="button"
            key={`${satz.exercise_name}-${satz.set_number}-${satz.is_drop_set}`}
            className={`wv-erfasst-chip ${satz.is_drop_set ? 'drop' : ''}`}
            onClick={() => onKorrigieren(satz)}
          >
            <span className="wv-erfasst-ex">{satz.exercise_name}</span>
            {satz.is_drop_set ? satzWert(satz) : `S${satz.set_number}: ${satzWert(satz)}`}
          </button>
        ))}
      </div>
    </div>
  );
}

// Ist der Satz in Wiederholungen oder in Sekunden aufgezeichnet? Massgeblich
// ist die Progression AM SATZ, nicht die aktuelle des Nutzers - dieselbe Regel
// wie in der Levellogik.
function satzTyp(satz, progressionen) {
  const prog = progressionen.find(p => p.id === satz.progression);
  if (prog) return prog.target_type;
  return satz.seconds != null ? 'time' : 'reps';
}

// Korrekturfeld fuer einen bereits gespeicherten Satz. Der Wert wird als Zahl
// geaendert - bei Zeitstufen muss der Timer also nicht noch einmal laufen, nur
// um einen Tippfehler zu heilen.
function KorrekturFeld({ satz, progressionen, leiter, isSaving, onSpeichern, onAbbrechen }) {
  const typ = satzTyp(satz, progressionen);
  const [wert, setWert] = useState(() => {
    if (satz.is_drop_set) return satz.drop_set_completed ? satz.progression : '';
    return String(satz.reps != null ? satz.reps : (satz.seconds != null ? satz.seconds : ''));
  });
  const prog = progressionen.find(p => p.id === satz.progression);

  const ungueltig = satz.is_drop_set
    ? false
    : (wert === '' || Number.isNaN(parseInt(wert, 10)) || parseInt(wert, 10) < 0);

  return (
    <div className="wv-korrektur" role="dialog" aria-label="Satz korrigieren">
      <p className="wv-korrektur-titel">
        {satz.exercise_name} · {satz.is_drop_set ? 'Drop-Set' : `Satz ${satz.set_number}`}
      </p>
      <p className="wv-korrektur-sub">
        {prog?.name || satz.progression_name}
        {!satz.is_drop_set && prog?.target_value != null && (
          <> · Ziel: {prog.target_type === 'reps' ? `${prog.target_value} Wdh` : `${prog.target_value} s`}</>
        )}
      </p>

      {satz.is_drop_set ? (
        <div className="wv-korrektur-leiter">
          {leiter.map(p => (
            <button
              type="button"
              key={p.id}
              className={`drop-set-item ${wert === p.id ? 'reached' : ''}`}
              onClick={() => setWert(p.id)}
            >
              <span className="drop-item-name">{p.name}</span>
              <span className="drop-item-check">{wert === p.id ? '✓' : ''}</span>
            </button>
          ))}
          <button
            type="button"
            className={`drop-set-item ${wert === '' ? 'reached' : ''}`}
            onClick={() => setWert('')}
          >
            <span className="drop-item-name">Übersprungen</span>
            <span className="drop-item-check">{wert === '' ? '✓' : ''}</span>
          </button>
        </div>
      ) : (
        <div className="wv-korrektur-eingabe">
          <input
            className="wv-korrektur-input"
            type="number"
            inputMode="numeric"
            min="0"
            value={wert}
            onChange={e => setWert(e.target.value)}
            autoFocus
          />
          <span className="wv-korrektur-einheit">{typ === 'reps' ? 'Wdh' : 'Sek'}</span>
        </div>
      )}

      <div className="wv-korrektur-knoepfe">
        <button className="btn-korrektur-ab" onClick={onAbbrechen} disabled={isSaving}>
          Abbrechen
        </button>
        <button
          className="btn-korrektur-ok"
          onClick={() => onSpeichern(satz.is_drop_set ? (wert === '' ? false : wert) : parseInt(wert, 10))}
          disabled={isSaving || ungueltig}
        >
          {isSaving ? 'Speichere …' : 'Speichern'}
        </button>
      </div>
    </div>
  );
}

// Sichtbare Rueckmeldung, ob gespeichert wurde. Bewusst auf Modulebene: eine
// im Rumpf von WorkoutView definierte Komponente waere bei jedem Rendern eine
// neue Funktion und wuerde jedes Mal neu montiert - genau das Muster, das
// hier eigentlich abgestellt wird.
function SpeicherHinweis({ zustand, titel, nachsatz, onRetry }) {
  if (!zustand) return null;
  return (
    <div className="save-note save-note--fehler" role="alert">
      <span className="save-note-text">
        <strong>{titel}</strong> {zustand.message} {nachsatz}
      </span>
      <button className="save-note-retry" onClick={onRetry}>Nochmal versuchen</button>
    </div>
  );
}

function buildWorkoutSteps(exercises) {
  const steps = [];
  const main = exercises.filter(e => e.category !== 'CORE');
  const core = exercises.filter(e => e.category === 'CORE');
  // 2 normal sets interleaved across main exercises
  for (let s = 1; s <= 2; s++) {
    for (const ex of main) {
      steps.push({ exerciseName: ex.name, setNumber: s, type: 'set' });
    }
  }
  // Drop sets for main
  for (const ex of main) {
    steps.push({ exerciseName: ex.name, setNumber: 3, type: 'drop' });
  }
  // Core: 2 sets + drop
  for (const ex of core) {
    steps.push({ exerciseName: ex.name, setNumber: 1, type: 'set' });
    steps.push({ exerciseName: ex.name, setNumber: 2, type: 'set' });
    steps.push({ exerciseName: ex.name, setNumber: 3, type: 'drop' });
  }
  return steps;
}

export default function WorkoutView() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isResting, setIsResting] = useState(false);
  const [currentWorkout, setCurrentWorkout] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [progressionData, setProgressionData] = useState(null);
  const [isWarmupComplete, setIsWarmupComplete] = useState(false);
  const [showCooldown, setShowCooldown] = useState(false);
  // isLoading gilt NUR fuer das anfaengliche Laden - es haengt den ganzen
  // Baum aus (siehe Guard unten). Das Speichern eines Satzes hat deshalb einen
  // eigenen Zustand: haenge SetInput/TimerInput waehrenddessen aus, ist die
  // Eingabe des Nutzers weg, sobald die Verbindung wackelt.
  const [isLoading, setIsLoading] = useState(true);
  const [saveState, setSaveState] = useState({ status: 'idle' });
  const [lastSaved, setLastSaved] = useState(null);
  const [erfasst, setErfasst] = useState([]);
  const [korrektur, setKorrektur] = useState(null);

  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const isInitialized = useWorkoutStore(state => state.isInitialized);
  const lastPerformance = useWorkoutStore(state => state.lastPerformance);
  const workouts = useWorkoutStore(state => state.workouts);
  const streak = useWorkoutStore(state => state.streak);
  const trainingDays = useWorkoutStore(state => state.trainingDays);
  const getCurrentWorkout = useWorkoutStore(state => state.getCurrentWorkout);
  const addSet = useWorkoutStore(state => state.addSet);
  const completeWorkout = useWorkoutStore(state => state.completeWorkout);
  const getLastPerformance = useWorkoutStore(state => state.getLastPerformance);

  const WORKOUT_STEPS = useMemo(() => buildWorkoutSteps(exercises), [exercises]);

  // Wake Lock für die gesamte Workout-Session: anfordern beim Betreten der View,
  // freigeben beim Verlassen (egal ob Abschluss, Abbruch oder Navigation).
  // visibilitychange: nach Hintergrund re-akquirieren, weil der Browser den Lock
  // beim Tab-Wechsel automatisch aufhebt.
  useEffect(() => {
    requestWakeLock();
    const onVisibility = () => { if (!document.hidden) requestWakeLock(); };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      releaseWakeLock();
    };
  }, []);

  useEffect(() => {
    if (isInitialized && exercises.length > 0) initializeWorkout();
  }, [isInitialized, exercises.length]);

  const initializeWorkout = async () => {
    try {
      const workout = await getCurrentWorkout();
      setCurrentWorkout(workout);

      // Die Saetze liegen bereits auf dem Server. Nach einem Neuladen setzt der
      // Ablauf deshalb am ersten offenen Schritt fort statt wieder bei 1 - und
      // das Aufwaermen entfaellt, wenn erkennbar schon trainiert wurde.
      const gespeichert = workout?.sets || [];
      setErfasst(gespeichert);
      if (gespeichert.length > 0) {
        const schritte = buildWorkoutSteps(exercises);
        const weiterAb = naechsterOffenerSchritt(schritte, gespeichert);
        setIsWarmupComplete(true);
        if (weiterAb >= schritte.length) {
          setCurrentStep(schritte.length - 1);
          setShowCooldown(true);
        } else {
          setCurrentStep(weiterAb);
        }
      }

      try { await getLastPerformance(); } catch {}
    } catch {}
    setIsLoading(false);
  };

  const getProgInfo = exerciseName => {
    const exercise = exercises.find(e => e.name === exerciseName);
    if (!exercise) return null;
    const userProg = userProgressions[String(exercise.id)];
    if (!userProg?.current_progression) return null;
    return {
      exercise,
      currentProgression: userProg.current_progression,
      lowerProgressions: exercise.progressions
        .filter(p => p.level < userProg.current_progression.level)
        .reverse(),
    };
  };

  // last_performance ist nach Uebungs-ID abgelegt und traegt die Felder
  // set1_reps/set1_seconds. Gesucht wurde frueher nach dem Uebungsnamen und
  // einem Feld "set1", das es nie gab - "Letztes Mal" erschien deshalb nie.
  // Der Typ kommt aus dem gefuellten Feld, nicht aus der heutigen Progression:
  // nach einem Aufstieg von Dead Hang auf Scapular Shrugs waeren 31 Sekunden
  // sonst als "31 Wdh" ausgewiesen.
  const getLastTime = (exercise, setNumber) => {
    const eintrag = lastPerformance?.[String(exercise.id)];
    if (!eintrag) return null;
    const reps = eintrag[`set${setNumber}_reps`];
    const sekunden = eintrag[`set${setNumber}_seconds`];
    if (reps != null) return { wert: reps, typ: 'reps' };
    if (sekunden != null) return { wert: sekunden, typ: 'time' };
    return null;
  };

  const getNextLabel = nextStep => {
    if (!nextStep) return 'Fertig!';
    if (nextStep.type === 'drop') return `${nextStep.exerciseName} Drop-Set`;
    return getProgInfo(nextStep.exerciseName)?.currentProgression?.name || nextStep.exerciseName;
  };

  const fehlertext = err => {
    if (!err?.response) return 'Keine Verbindung zum Server.';
    if (err.response.status === 409) {
      return err.response.data?.error || 'Dieses Workout ist bereits abgeschlossen.';
    }
    if (err.response.status === 401) return 'Sitzung abgelaufen — bitte neu anmelden.';
    return `Server-Fehler (${err.response.status}).`;
  };

  const handleSetComplete = async (value = null) => {
    setSaveState({ status: 'saving' });
    try {
      const step = WORKOUT_STEPS[currentStep];
      const isDropSet = step.type === 'drop';
      const progInfo = getProgInfo(step.exerciseName);
      if (!progInfo) { setSaveState({ status: 'idle' }); return; }

      // For drop-sets, `value` is the reached progression id (or false = skip).
      // We store that reached variant as the drop-set's progression so history
      // shows how far down the user had to go. This is a progress signal only —
      // it does NOT feed the level logic.
      const dropCompleted = isDropSet && value !== false;
      const dropProgressionId = (isDropSet && value !== false)
        ? value
        : progInfo.currentProgression.id;

      const reps = (!isDropSet && progInfo.currentProgression.target_type === 'reps') ? value : null;
      const secs = (!isDropSet && progInfo.currentProgression.target_type === 'time') ? value : null;

      const gespeicherterSatz = await addSet(
        currentWorkout.id,
        progInfo.exercise.id,
        isDropSet ? dropProgressionId : progInfo.currentProgression.id,
        step.setNumber,
        reps,
        secs,
        isDropSet ? REST_TIMES.afterDrop : REST_TIMES.normal,
        isDropSet,
        dropCompleted
      );

      // Erst nach der bestaetigten Antwort weiterschalten.
      setSaveState({ status: 'idle' });
      setErfasst(bisher => [
        ...bisher.filter(satz => !passtZuSchritt(satz, step)),
        gespeicherterSatz,
      ]);
      setLastSaved(isDropSet ? 'Drop-Set gespeichert' : `Satz ${step.setNumber} gespeichert`);
      if (currentStep === WORKOUT_STEPS.length - 1) {
        setShowCooldown(true);
      } else {
        setIsResting(true);
      }
    } catch (err) {
      // Nicht weiterschalten: der Schritt bleibt stehen, die Eingabe steht noch
      // im Feld (SetInput/TimerInput bleiben montiert) und laesst sich erneut
      // abschicken.
      console.error('Error saving set:', err);
      setSaveState({ status: 'error', value, message: fehlertext(err) });
    }
  };

  // Alle Progressionen flach, um die eines gespeicherten Satzes wiederzufinden.
  const alleProgressionen = useMemo(
    () => exercises.flatMap(e => e.progressions || []), [exercises]);

  const leiterFuer = satz => {
    const info = getProgInfo(satz.exercise_name);
    return info ? [info.currentProgression, ...info.lowerProgressions] : [];
  };

  // Korrektur ist bewusst dasselbe add_set wie beim ersten Eintragen: es ist
  // ein update_or_create auf (Workout, Uebung, Satznummer, Drop). Der alte Wert
  // wird dadurch ersetzt, nicht ergaenzt - und die Levellogik liest in
  // complete() ohnehin frisch aus der Datenbank. Der alte Wert kann also nicht
  // mehr zaehlen.
  const handleKorrekturSpeichern = async neuerWert => {
    const satz = korrektur;
    if (!satz) return;
    setSaveState({ status: 'saving' });
    try {
      const istDrop = Boolean(satz.is_drop_set);
      const typ = satzTyp(satz, alleProgressionen);
      const dropAbgeschlossen = istDrop && neuerWert !== false;
      // Die Progression des Satzes bleibt, wie sie war - nur der Wert aendert
      // sich. Beim Drop-Set IST die Variante der Wert.
      const progressionId = istDrop
        ? (dropAbgeschlossen ? neuerWert : (leiterFuer(satz)[0]?.id ?? satz.progression))
        : satz.progression;
      const reps = (!istDrop && typ === 'reps') ? neuerWert : null;
      const secs = (!istDrop && typ === 'time') ? neuerWert : null;

      const gespeichert = await addSet(
        currentWorkout.id, satz.exercise, progressionId, satz.set_number,
        reps, secs, satz.rest_time_seconds, istDrop, dropAbgeschlossen);

      setErfasst(bisher => bisher.map(x =>
        (x.exercise_name === satz.exercise_name
          && x.set_number === satz.set_number
          && Boolean(x.is_drop_set) === istDrop) ? gespeichert : x));
      setSaveState({ status: 'idle' });
      setKorrektur(null);
    } catch (err) {
      console.error('Error correcting set:', err);
      setSaveState({ status: 'korrekturError', message: fehlertext(err) });
    }
  };

  const handleKorrekturOeffnen = satz => {
    setSaveState({ status: 'idle' });
    setKorrektur(satz);
  };

  // Bewusst eine schlichte Funktion, keine Komponente: eine im Rumpf definierte
  // Komponente waere bei jedem Rendern eine neue Funktion, wuerde neu montiert -
  // und KorrekturFeld verloere den gerade eingetippten Wert. So sieht React
  // direkt das stabile KorrekturFeld an stabiler Stelle.
  const korrekturSchicht = () => korrektur && (
    <div className="wv-korrektur-schicht">
      <SpeicherHinweis
        zustand={saveState.status === 'korrekturError' ? saveState : null}
        titel="Nicht gespeichert."
        nachsatz="Der alte Wert steht noch."
        onRetry={() => setSaveState({ status: 'idle' })}
      />
      <KorrekturFeld
        satz={korrektur}
        progressionen={alleProgressionen}
        leiter={leiterFuer(korrektur)}
        isSaving={saveState.status === 'saving'}
        onSpeichern={handleKorrekturSpeichern}
        onAbbrechen={() => { setKorrektur(null); setSaveState({ status: 'idle' }); }}
      />
    </div>
  );

  const handleRestComplete = () => {
    setIsResting(false);
    setLastSaved(null);
    setCurrentStep(s => s + 1);
  };

  const handleExit = () => { if (window.confirm('Workout beenden?')) navigate('/'); };
  const handleModalClose = () => { setShowModal(false); navigate('/'); };

  const handleCooldownDone = async () => {
    setSaveState({ status: 'saving' });
    try {
      const result = await completeWorkout(currentWorkout.id);
      setSaveState({ status: 'idle' });
      setProgressionData(result);
      setShowCooldown(false);
      setShowModal(true);
    } catch (err) {
      console.error('Error completing workout:', err);
      setSaveState({ status: 'cooldownError', message: fehlertext(err) });
    }
  };

  if (isLoading || !isInitialized || !currentWorkout || WORKOUT_STEPS.length === 0) {
    return (
      <div className="loading-shell">
        <div className="loading-logo">COR<span>VIS</span></div>
        <div className="loading-spinner" />
        <p className="loading-text">Lade Training</p>
      </div>
    );
  }

  if (!isWarmupComplete) {
    return <WarmupChecklist onComplete={() => setIsWarmupComplete(true)} />;
  }

  if (showCooldown) {
    return (
      <>
        <SpeicherHinweis
          zustand={saveState.status === 'cooldownError' ? saveState : null}
          titel="Nicht abgeschlossen."
          nachsatz="Deine Sätze sind gespeichert."
          onRetry={handleCooldownDone}
        />
        <CooldownChecklist
          onComplete={handleCooldownDone}
          isSaving={saveState.status === 'saving'}
        />
      </>
    );
  }

  if (isResting) {
    const step = WORKOUT_STEPS[currentStep];
    const nextStep = WORKOUT_STEPS[currentStep + 1];
    return (
      <RestTimer
        seconds={step.type === 'drop' ? REST_TIMES.afterDrop : REST_TIMES.normal}
        nextExercise={getNextLabel(nextStep)}
        onComplete={handleRestComplete}
        hinweis={lastSaved}
      />
    );
  }

  const step = WORKOUT_STEPS[currentStep];
  const progInfo = getProgInfo(step.exerciseName);
  if (!progInfo) return <div className="loading-shell"><p className="loading-text">Fehler: Übung nicht gefunden</p></div>;

  const progressPct = ((currentStep + 1) / WORKOUT_STEPS.length) * 100;

  if (step.type === 'drop') {
    return (
      <div className="workout-shell">
        <header className="workout-header">
          <button className="workout-exit-btn" onClick={handleExit}>✕</button>
          <div className="workout-header-meta">
            <p className="workout-step-label">Schritt {currentStep + 1} / {WORKOUT_STEPS.length}</p>
            <div className="workout-progress-bar">
              <div className="workout-progress-fill" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        </header>
        <SpeicherHinweis
          zustand={saveState.status === 'error' ? saveState : null}
          titel="Nicht gespeichert."
          nachsatz="Deine Eingabe steht noch da."
          onRetry={() => handleSetComplete(saveState.value)}
        />
        <ErfassteSaetze saetze={erfasst} onKorrigieren={handleKorrekturOeffnen} />
        {korrekturSchicht()}
        <DropSetInstructions
          exercise={progInfo.exercise}
          progressions={[progInfo.currentProgression, ...progInfo.lowerProgressions]}
          lastReachedName={lastPerformance?.[String(progInfo.exercise.id)]?.drop_reached}
          onComplete={handleSetComplete}
          isSaving={saveState.status === 'saving'}
        />
        {showModal && <ProgressionModal upgrades={progressionData?.upgrades || []} downgrades={progressionData?.downgrades || []} workouts={workouts} streak={streak} trainingDays={trainingDays} onClose={handleModalClose} />}
      </div>
    );
  }

  const lastTime = getLastTime(progInfo.exercise, step.setNumber);

  return (
    <div className="workout-shell">
      <header className="workout-header">
        <button className="workout-exit-btn" onClick={handleExit}>✕</button>
        <div className="workout-header-meta">
          <p className="workout-step-label">Schritt {currentStep + 1} / {WORKOUT_STEPS.length}</p>
          <div className="workout-progress-bar">
            <div className="workout-progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
      </header>

      <div className="workout-main">
        <div className="workout-main-center">
          <SpeicherHinweis
            zustand={saveState.status === 'error' ? saveState : null}
            titel="Nicht gespeichert."
            nachsatz="Deine Eingabe steht noch da."
            onRetry={() => handleSetComplete(saveState.value)}
          />
          <ErfassteSaetze saetze={erfasst} onKorrigieren={handleKorrekturOeffnen} />
          {korrekturSchicht()}
          <div className="wv-info">
            <span className="wv-cat-pill">{progInfo.exercise.category}</span>
            <p className="wv-prog-name">{progInfo.currentProgression.name}</p>
            <p className="wv-set-num">Satz {step.setNumber}</p>
            {progInfo.currentProgression.target_value && (
              <p className="wv-target">
                Ziel: <strong>
                  {progInfo.currentProgression.target_type === 'reps'
                    ? `${progInfo.currentProgression.target_value} Wdh`
                    : `${progInfo.currentProgression.target_value} s`}
                </strong>
              </p>
            )}
            {lastTime && (
              <p className="wv-last">
                Letztes Mal:{' '}
                <span>
                  {lastTime.typ === 'reps'
                    ? `${lastTime.wert} Wdh`
                    : `${Math.floor(lastTime.wert / 60)}:${String(lastTime.wert % 60).padStart(2, '0')}`}
                </span>
              </p>
            )}
            <FormTip progressionName={progInfo.currentProgression.name} />
          </div>
          {progInfo.currentProgression.target_type === 'reps' ? (
            <SetInput
              setNumber={step.setNumber}
              exerciseName={step.exerciseName}
              progressionName={progInfo.currentProgression.name}
              onComplete={handleSetComplete}
              isSaving={saveState.status === 'saving'}
            />
          ) : (
            <TimerInput
              setNumber={step.setNumber}
              exerciseName={step.exerciseName}
              progressionName={progInfo.currentProgression.name}
              targetSeconds={progInfo.currentProgression.target_value}
              onComplete={handleSetComplete}
              isSaving={saveState.status === 'saving'}
            />
          )}
        </div>
      </div>

      {showModal && <ProgressionModal upgrades={progressionData?.upgrades || []} downgrades={progressionData?.downgrades || []} workouts={workouts} streak={streak} trainingDays={trainingDays} onClose={handleModalClose} />}
    </div>
  );
}
