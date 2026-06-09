import { useState, useEffect, useRef } from 'react';

export default function RestTimer({ seconds, nextExercise, onComplete }) {
  const [remaining, setRemaining] = useState(seconds);
  const intervalRef = useRef(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setRemaining(prev => {
        if (prev <= 1) { clearInterval(intervalRef.current); onComplete(); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(intervalRef.current);
  }, []);

  const fmt = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

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
