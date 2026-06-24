// Screen Wake Lock: hält das Display während der gesamten aktiven Workout-Session
// wach. Wird von WorkoutView gesteuert (Mount = anfordern, Unmount = freigeben).
// Sauberer Fallback wenn der Browser die API nicht unterstützt — App läuft normal.

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
