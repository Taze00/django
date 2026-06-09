import { useState } from 'react';

const ITEMS = ['Handgelenke', 'Schultern', 'Ellbogen', 'Rücken', 'Beine'];

export default function WarmupChecklist({ onComplete }) {
  const [checked, setChecked] = useState({});

  const toggle = item => setChecked(prev => ({ ...prev, [item]: !prev[item] }));
  const allDone = ITEMS.every(i => checked[i]);

  return (
    <div className="warmup-shell">
      <p className="warmup-title">Aufwärmen</p>
      <p className="warmup-sub">Beweg kurz durch die Liste — dann geht's los.</p>

      <div className="warmup-list">
        {ITEMS.map(item => (
          <div
            key={item}
            className={`warmup-item ${checked[item] ? 'checked' : ''}`}
            onClick={() => toggle(item)}
          >
            <div className="warmup-check">
              {checked[item] && <span className="warmup-check-inner">✓</span>}
            </div>
            <span className="warmup-item-label">{item}</span>
          </div>
        ))}
      </div>

      <button className="btn-warmup-done" onClick={onComplete} disabled={!allDone}>
        {allDone ? 'Training starten →' : `Noch ${ITEMS.filter(i => !checked[i]).length} offen`}
      </button>
    </div>
  );
}
