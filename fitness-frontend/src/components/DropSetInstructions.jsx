import { useState } from 'react';
import FormTip from './FormTip';

/**
 * Drop-set: the user descends through easier variants to exhaustion, then taps
 * the variant they made it down to. That reached variant is reported back
 * (its progression id) so we can show progress over time. A higher reached
 * variant = stronger. This does NOT affect level progression — it's a visible
 * fatigue/progress signal only.
 */
export default function DropSetInstructions({ exercise, progressions, lastReachedName, onComplete, isSaving = false }) {
  // Auf der untersten Stufe gibt es nichts Leichteres, zu dem man absteigen
  // koennte - die Leiter haette genau einen Eintrag, und die Anweisung "geh
  // durch die Varianten" waere sinnlos. Dann gibt es keine Leiter, sondern nur
  // die Aufforderung, bis zur Erschoepfung zu machen.
  const ohneLeiter = progressions.length <= 1;
  const [selected, setSelected] = useState(ohneLeiter ? (progressions[0]?.id ?? null) : null);

  return (
    <div className="workout-main">
      <p className="workout-exercise-cat">Drop-Set</p>
      <p className="workout-exercise-name">{exercise.name}</p>
      <p className="workout-set-label">
        {ohneLeiter ? 'Letzter Satz bis zur Erschöpfung' : 'Geh durch die Varianten bis zur Erschöpfung'}
      </p>
      <FormTip progressionName={progressions[0]?.name} />

      <p className="drop-set-intro">
        {ohneLeiter
          ? `Du stehst auf der untersten Stufe — darunter gibt es nichts Leichteres.
             Mach von ${progressions[0]?.name ?? 'dieser Variante'} so viele, wie du schaffst.`
          : `Starte mit deiner aktuellen Variante. Wenn du nicht mehr kannst, wechsle zur
             nächst einfacheren. Tippe am Ende die Variante, bei der du aufgehört hast.`}
      </p>

      {lastReachedName && !ohneLeiter && (
        <p className="drop-set-last">Letztes Mal: <span>{lastReachedName}</span></p>
      )}

      {!ohneLeiter && (
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
      )}

      <button
        className="btn-drop-done"
        onClick={() => onComplete(selected)}
        disabled={isSaving || !selected}
      >
        {isSaving ? 'Speichere …' : 'Drop-Set abschließen ✓'}
      </button>
      <button className="btn-drop-skip" onClick={() => onComplete(false)} disabled={isSaving}>
        Überspringen
      </button>
    </div>
  );
}
