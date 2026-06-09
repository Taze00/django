import { useEffect, useRef } from 'react';

function Confetti({ count = 60 }) {
  const colors = ['#FF4D00', '#ff6a2a', '#f0ede8', '#ffb347', '#fff'];
  const pieces = Array.from({ length: count }, (_, i) => ({
    id: i,
    color: colors[i % colors.length],
    left: Math.random() * 100,
    delay: Math.random() * 1.2,
    size: 5 + Math.random() * 7,
    duration: 1.8 + Math.random() * 1.4,
    rotate: Math.random() * 360,
  }));
  return (
    <div className="confetti-wrap" aria-hidden="true">
      {pieces.map(p => (
        <div
          key={p.id}
          className="confetti-piece"
          style={{
            left: `${p.left}%`,
            width: p.size,
            height: p.size * 0.6,
            background: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
            transform: `rotate(${p.rotate}deg)`,
          }}
        />
      ))}
    </div>
  );
}

function UpgradeCard({ item, idx }) {
  return (
    <div className="lvl-card" style={{ animationDelay: `${0.15 + idx * 0.1}s` }}>
      <div className="lvl-card-top">
        <span className="lvl-card-arrow">↑</span>
        <span className="lvl-card-ex">{item.exercise}</span>
      </div>
      <div className="lvl-card-body">
        <div className="lvl-num-wrap">
          <span className="lvl-num old">{item.from_level}</span>
          <span className="lvl-arrow-big">→</span>
          <span className="lvl-num new">{item.to_level}</span>
        </div>
        {item.to_progression && (
          <p className="lvl-new-name">{item.to_progression}</p>
        )}
        {item.is_max_level && (
          <p className="lvl-max-badge">MAX LEVEL</p>
        )}
      </div>
    </div>
  );
}

function DowngradeCard({ item, idx }) {
  return (
    <div className="lvl-card lvl-card--down" style={{ animationDelay: `${0.15 + idx * 0.1}s` }}>
      <div className="lvl-card-top">
        <span className="lvl-card-arrow down">↓</span>
        <span className="lvl-card-ex">{item.exercise}</span>
      </div>
      <div className="lvl-card-body">
        <div className="lvl-num-wrap">
          <span className="lvl-num old">{item.from_level}</span>
          <span className="lvl-arrow-big">→</span>
          <span className="lvl-num new dim">{item.to_level}</span>
        </div>
        {item.to_progression && (
          <p className="lvl-new-name muted">{item.to_progression}</p>
        )}
      </div>
    </div>
  );
}

export default function ProgressionModal({ upgrades = [], downgrades = [], onClose }) {
  const hasUpgrades = upgrades.length > 0;
  const hasChanges = upgrades.length + downgrades.length > 0;

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      {hasUpgrades && <Confetti />}

      <div className="lvl-modal-box">
        {hasUpgrades ? (
          <>
            <p className="lvl-modal-eyebrow">— Level Update</p>
            <h2 className="lvl-modal-title">
              WEITER<span>GEKOMMEN</span>
            </h2>
            <p className="lvl-modal-sub">Du hast die Zielwerte erreicht.</p>
          </>
        ) : hasChanges ? (
          <>
            <p className="lvl-modal-eyebrow">— Level Update</p>
            <h2 className="lvl-modal-title">LEVEL<span>ANPASSUNG</span></h2>
          </>
        ) : (
          <>
            <p className="lvl-modal-eyebrow">— Workout</p>
            <h2 className="lvl-modal-title">ABGE<span>SCHLOSSEN</span></h2>
            <p className="lvl-modal-sub">Weiter so — gleiches Level beibehalten.</p>
          </>
        )}

        <div className="lvl-cards">
          {upgrades.map((u, i) => <UpgradeCard key={i} item={u} idx={i} />)}
          {downgrades.map((d, i) => <DowngradeCard key={i} item={d} idx={upgrades.length + i} />)}
        </div>

        <button className="modal-close-btn" onClick={onClose}>
          Fertig →
        </button>
      </div>
    </div>
  );
}
