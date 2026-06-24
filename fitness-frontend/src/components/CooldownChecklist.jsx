import { useState } from 'react';

const ITEMS = [
  { name: 'Brust dehnen',         desc: 'Arm an Türrahmen/Wand, Oberkörper langsam wegdrehen' },
  { name: 'Schultern & Trizeps',  desc: 'Arm über den Kopf, am Ellbogen sanft ziehen' },
  { name: 'Rücken & Lat',         desc: 'An etwas festhalten, Becken zurückschieben (oder Katze-Kuh)' },
  { name: 'Bizeps & Unterarme',   desc: 'Arm gestreckt, Handfläche nach außen drehen' },
  { name: 'Rumpf & Bauch',        desc: 'Sanfte Cobra / leichtes Zurückbeugen' },
];

export default function CooldownChecklist({ onComplete }) {
  const [checked, setChecked] = useState({});

  const toggle = name => setChecked(prev => ({ ...prev, [name]: !prev[name] }));
  const allDone = ITEMS.every(i => checked[i.name]);

  return (
    <div className="warmup-shell">
      <p className="warmup-title">Cool-down</p>
      <p className="warmup-sub">Dehn kurz die trainierten Muskeln — gut für die Regeneration.</p>

      <div className="warmup-list">
        {ITEMS.map(item => (
          <div
            key={item.name}
            className={`warmup-item cooldown-item ${checked[item.name] ? 'checked' : ''}`}
            onClick={() => toggle(item.name)}
          >
            <div className="warmup-check">
              {checked[item.name] && <span className="warmup-check-inner">✓</span>}
            </div>
            <div className="cooldown-item-text">
              <span className="warmup-item-label">{item.name}</span>
              <span className="cooldown-item-desc">{item.desc}</span>
            </div>
          </div>
        ))}
      </div>

      <button className="btn-warmup-done" onClick={onComplete} disabled={!allDone}>
        {allDone ? 'Fertig →' : `Noch ${ITEMS.filter(i => !checked[i.name]).length} offen`}
      </button>
      <button className="btn-cooldown-skip" onClick={onComplete}>
        Überspringen
      </button>
    </div>
  );
}
