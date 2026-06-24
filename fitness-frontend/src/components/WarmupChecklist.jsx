import { useState } from 'react';

const ITEMS = [
  { name: 'Handgelenke',  desc: 'Kreisen + sanft in beide Richtungen dehnen' },
  { name: 'Schultern',    desc: 'Große Armkreise vor- und rückwärts' },
  { name: 'Ellbogen',     desc: 'Arme strecken und beugen, locker kreisen' },
  { name: 'Rücken',       desc: 'Katze-Kuh oder sanftes Rumpfdrehen' },
  { name: 'Beine',        desc: 'Hüftkreisen + lockere Kniebeugen ohne Gewicht' },
];

export default function WarmupChecklist({ onComplete }) {
  const [checked, setChecked] = useState({});

  const toggle = name => setChecked(prev => ({ ...prev, [name]: !prev[name] }));
  const allDone = ITEMS.every(i => checked[i.name]);

  return (
    <div className="warmup-shell">
      <p className="warmup-title">Aufwärmen</p>
      <p className="warmup-sub">Beweg kurz durch die Liste — dann geht's los.</p>

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
        {allDone ? 'Training starten →' : `Noch ${ITEMS.filter(i => !checked[i.name]).length} offen`}
      </button>
    </div>
  );
}
