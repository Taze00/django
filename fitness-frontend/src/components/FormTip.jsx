import { useState } from 'react';
import { EXERCISE_INFO } from '../data/exerciseInfo';

export default function FormTip({ progressionName }) {
  const [open, setOpen] = useState(false);
  const info = EXERCISE_INFO[progressionName];
  if (!info) return null;
  return (
    <div className="form-tip">
      <button className="form-tip-toggle" onClick={() => setOpen(o => !o)}>
        Form-Tipp {open ? '▴' : '▾'}
      </button>
      {open && (
        <div className="form-tip-body">
          <p className="form-tip-desc">{info.desc}</p>
          {info.youtube && (
            <a
              className="form-tip-link"
              href={info.youtube}
              target="_blank"
              rel="noopener noreferrer"
            >
              YouTube ansehen →
            </a>
          )}
        </div>
      )}
    </div>
  );
}
