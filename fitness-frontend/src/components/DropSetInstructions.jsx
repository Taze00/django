import { useState } from 'react';

export default function DropSetInstructions({ exercise, progressions, onComplete }) {
  return (
    <div className="workout-main">
      <p className="workout-exercise-cat">Drop-Set</p>
      <p className="workout-exercise-name">{exercise.name}</p>
      <p className="workout-set-label">Geh durch die Varianten bis zur Erschöpfung</p>

      <p className="drop-set-intro">
        Starte mit deiner aktuellen Variante. Wenn du nicht mehr kannst, wechsle zur nächst einfacheren und mach weiter.
      </p>

      <div className="drop-set-ladder">
        {progressions.map((prog, idx) => (
          <div key={prog.id} className="drop-set-item">
            <span className="drop-item-idx">{idx + 1}</span>
            <span className="drop-item-name">{prog.name}</span>
          </div>
        ))}
      </div>

      <button className="btn-drop-done" onClick={() => onComplete(true)}>
        Drop-Set abgeschlossen ✓
      </button>
      <button className="btn-drop-skip" onClick={() => onComplete(false)}>
        Überspringen
      </button>
    </div>
  );
}
