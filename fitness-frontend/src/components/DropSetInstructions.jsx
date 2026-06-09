import { useState } from 'react';

/**
 * Drop-set: the user descends through easier variants to exhaustion, then taps
 * the variant they made it down to. That reached variant is reported back
 * (its progression id) so we can show progress over time. A higher reached
 * variant = stronger. This does NOT affect level progression — it's a visible
 * fatigue/progress signal only.
 */
export default function DropSetInstructions({ exercise, progressions, lastReachedName, onComplete }) {
  const [selected, setSelected] = useState(null);

  return (
    <div className="workout-main">
      <p className="workout-exercise-cat">Drop-Set</p>
      <p className="workout-exercise-name">{exercise.name}</p>
      <p className="workout-set-label">Geh durch die Varianten bis zur Erschöpfung</p>

      <p className="drop-set-intro">
        Starte mit deiner aktuellen Variante. Wenn du nicht mehr kannst, wechsle zur
        nächst einfacheren. Tippe am Ende die Variante, bei der du aufgehört hast.
      </p>

      {lastReachedName && (
        <p className="drop-set-last">Letztes Mal: <span>{lastReachedName}</span></p>
      )}

      <div className="drop-set-ladder">
        {progressions.map((prog, idx) => (
          <button
            key={prog.id}
            className={`drop-set-item ${selected === prog.id ? 'reached' : ''}`}
            onClick={() => setSelected(prog.id)}
          >
            <span className="drop-item-idx">{idx + 1}</span>
            <span className="drop-item-name">{prog.name}</span>
            <span className="drop-item-check">{selected === prog.id ? '✓' : ''}</span>
          </button>
        ))}
      </div>

      <button
        className="btn-drop-done"
        onClick={() => onComplete(selected)}
        disabled={!selected}
      >
        Drop-Set abschließen ✓
      </button>
      <button className="btn-drop-skip" onClick={() => onComplete(false)}>
        Überspringen
      </button>
    </div>
  );
}
