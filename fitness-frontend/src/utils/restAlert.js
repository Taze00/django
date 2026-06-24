// Akustisches + haptisches Signal am Ende der Pause.
// Ton wird per Web Audio erzeugt (keine Audiodatei nötig). iOS verlangt, dass
// der AudioContext innerhalb einer Nutzer-Geste freigeschaltet wird — das
// passiert beim ersten Tap (Listener unten).

let audioCtx = null;

function getCtx() {
  if (!audioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (AC) audioCtx = new AC();
  }
  return audioCtx;
}

// Audio beim ersten Nutzer-Tap freischalten (iOS-Anforderung).
function unlockAudio() {
  const ctx = getCtx();
  if (ctx && ctx.state === 'suspended') ctx.resume();
}
if (typeof window !== 'undefined') {
  window.addEventListener('pointerdown', unlockAudio);
  window.addEventListener('touchstart', unlockAudio);
}

function beepAt(ctx, startOffset, freq) {
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.connect(g);
  g.connect(ctx.destination);
  o.type = 'sine';
  o.frequency.value = freq;
  const t = ctx.currentTime + startOffset;
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(0.3, t + 0.02);
  g.gain.exponentialRampToValueAtTime(0.0001, t + 0.3);
  o.start(t);
  o.stop(t + 0.32);
}

// Kurzer, klarer Doppel-Signalton.
export function playBeep() {
  try {
    const ctx = getCtx();
    if (!ctx) return;
    if (ctx.state === 'suspended') ctx.resume();
    beepAt(ctx, 0, 880);
    beepAt(ctx, 0.38, 1100);
  } catch (e) {
    /* Audio nicht verfügbar — still ignorieren */
  }
}

export function vibrate() {
  try {
    if (navigator.vibrate) navigator.vibrate([180, 80, 180]);
  } catch (e) {
    /* Vibration nicht verfügbar (z.B. iOS Safari) — ignorieren */
  }
}

// Signal wenn die App sichtbar ist: Ton + Vibration.
export function restAlert() {
  playBeep();
  vibrate();
}
