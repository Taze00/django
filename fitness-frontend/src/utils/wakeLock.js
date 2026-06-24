// Screen Wake Lock: hält das Display während einer laufenden Pause an, damit
// iOS den Timer nicht einfriert und der Pausen-Ton zuverlässig kommt.
// Nur während der aktiven Pause halten (Akku!). Sauberer Fallback, wenn der
// Browser die API nicht unterstützt oder die Anfrage fehlschlägt.

let sentinel = null;

export async function requestWakeLock() {
  try {
    if (!('wakeLock' in navigator)) return;
    // Vorhandenen Lock nicht doppeln.
    if (sentinel) return;
    sentinel = await navigator.wakeLock.request('screen');
    // Geht der Lock verloren (z.B. Tab versteckt), Referenz aufräumen.
    sentinel.addEventListener('release', () => { sentinel = null; });
  } catch (e) {
    sentinel = null; // still ignorieren, App läuft normal weiter
  }
}

export async function releaseWakeLock() {
  try {
    if (sentinel) await sentinel.release();
  } catch (e) {
    /* ignorieren */
  } finally {
    sentinel = null;
  }
}
