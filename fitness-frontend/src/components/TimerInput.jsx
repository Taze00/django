import { useState, useEffect, useRef } from 'react';

export default function TimerInput({ setNumber, exerciseName, progressionName, targetSeconds, lastTime, onComplete }) {
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

  const handleDone = () => {
    setRunning(false);
    onComplete(elapsed);
  };

  return (
    <div className="workout-input-wrap">
      {lastTime !== null && lastTime !== undefined && (
        <p className="workout-last">Letztes Mal: <span>{fmt(lastTime)}</span></p>
      )}
      <p className={`timer-display ${running ? 'running' : ''}`}>{fmt(elapsed)}</p>
      <button
        className="timer-btn"
        onClick={() => setRunning(r => !r)}
      >
        {running ? '⏸ Pause' : elapsed > 0 ? '▶ Weiter' : '▶ Start'}
      </button>
      <button className="btn-done" onClick={handleDone} disabled={elapsed === 0}>
        Satz abschließen →
      </button>
    </div>
  );
}
