import { useState, useEffect, useRef } from 'react';
import { restAlert } from '../utils/restAlert';
import { showRestDoneNotification } from '../utils/notify';

export default function RestTimer({ seconds, nextExercise, onComplete }) {
  // Ziel-Zeitstempel statt Runterzählen: bleibt korrekt, auch wenn der Browser
  // den Timer drosselt/pausiert (z.B. App im Hintergrund).
  const endAtRef = useRef(Date.now() + seconds * 1000);
  const completedRef = useRef(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const [remaining, setRemaining] = useState(seconds);
  // True, wenn die Pause ablief, während die App im Hintergrund war —
  // zeigt beim Zurückkommen einen "Pause vorbei"-Hinweis.
  const [finishedWhileHidden, setFinishedWhileHidden] = useState(false);

  useEffect(() => {
    const computeRemaining = () =>
      Math.max(0, Math.ceil((endAtRef.current - Date.now()) / 1000));

    const finishVisible = () => {
      if (completedRef.current) return;
      completedRef.current = true;
      restAlert(); // Ton + Vibration, da App sichtbar
      onCompleteRef.current();
    };

    const tick = () => {
      const r = computeRemaining();
      setRemaining(r);
      if (r <= 0 && !completedRef.current) {
        if (document.hidden) {
          // App im Hintergrund: nicht automatisch weiterspringen, stattdessen
          // System-Benachrichtigung (falls erlaubt) + "Pause vorbei"-Hinweis
          // beim Zurückkommen.
          completedRef.current = true;
          setFinishedWhileHidden(true);
          showRestDoneNotification();
        } else {
          finishVisible();
        }
      }
    };

    // Beim Zurückkommen prüfen, ob die Pause während der Abwesenheit ablief.
    const onVisibility = () => {
      if (document.hidden) return;
      if (!completedRef.current && Date.now() >= endAtRef.current) {
        completedRef.current = true;
        restAlert(); // jetzt sichtbar -> Ton + Vibration
        setFinishedWhileHidden(true);
      } else if (!completedRef.current) {
        setRemaining(computeRemaining());
      } else {
        setRemaining(computeRemaining());
      }
    };

    const id = setInterval(tick, 250);
    document.addEventListener('visibilitychange', onVisibility);
    tick();
    return () => {
      clearInterval(id);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);

  const fmt = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

  if (finishedWhileHidden) {
    return (
      <div className="rest-shell">
        <p className="rest-label">Pause vorbei</p>
        <p className="rest-timer">0:00</p>
        <div className="rest-next">
          Weiter geht's
          <span>{nextExercise}</span>
        </div>
        <button className="btn-skip-rest" onClick={onComplete}>Weiter →</button>
      </div>
    );
  }

  return (
    <div className="rest-shell">
      <p className="rest-label">Pause</p>
      <p className="rest-timer">{fmt(remaining)}</p>
      <div className="rest-next">
        Nächste Übung
        <span>{nextExercise}</span>
      </div>
      <button className="btn-skip-rest" onClick={onComplete}>Überspringen →</button>
    </div>
  );
}
