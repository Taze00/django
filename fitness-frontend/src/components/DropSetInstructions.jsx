import { useState } from 'react';
import FormTip from './FormTip';
import { MAX_REPS, MAX_SECONDS, nurZiffern } from '../utils/eingabe';

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
  // Der Drop-Satz speicherte bisher nur, WELCHE Variante erreicht wurde - nie,
  // wie viel davon. In der Datenbank standen reps und seconds beide auf null,
  // der Satz zaehlte also nirgends mit. Die Zahl ist freiwillig: wer sie beim
  // Ausbelasten nicht mitzaehlt, kommt trotzdem weiter.
  const [wert, setWert] = useState('');
  const erreicht = progressions.find(p => p.id === selected);
  const zeitbasiert = erreicht?.target_type === 'time';
  const grenze = zeitbasiert ? MAX_SECONDS : MAX_REPS;
  const zuGross = wert !== '' && parseInt(wert, 10) > grenze;

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

      {selected && (
        <div className="drop-set-wert">
          <label className="drop-set-wert-label" htmlFor="drop-wert">
            Wie viele bei {erreicht?.name}? <span>freiwillig</span>
          </label>
          <div className="drop-set-wert-zeile">
            <input
              id="drop-wert"
              className="drop-set-wert-input"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={wert}
              onChange={e => setWert(nurZiffern(e.target.value))}
              placeholder="—"
            />
            <span className="drop-set-wert-einheit">{zeitbasiert ? 'Sek' : 'Wdh'}</span>
          </div>
          {zuGross && <p className="eingabe-hinweis">Höchstens {grenze}.</p>}
        </div>
      )}

      <button
        className="btn-drop-done"
        onClick={() => onComplete({
          progression: selected,
          wert: wert === '' ? null : parseInt(wert, 10),
        })}
        disabled={isSaving || !selected || zuGross}
      >
        {isSaving ? 'Speichere …' : 'Drop-Set abschließen ✓'}
      </button>
      <button className="btn-drop-skip" onClick={() => onComplete(false)} disabled={isSaving}>
        Überspringen
      </button>
    </div>
  );
}
