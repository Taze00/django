// System-Benachrichtigungen über den minimalen Service Worker.
// Auf iOS funktionieren Web-Benachrichtigungen nur als installierte PWA
// (Zum Home-Bildschirm) ab iOS 16.4 — sonst greift sauber der Fallback
// (nur Ton + Vibration), ohne Fehler.

let swRegistration = null;

export function notificationsSupported() {
  return (
    typeof window !== 'undefined' &&
    'Notification' in window &&
    'serviceWorker' in navigator
  );
}

export function notificationPermission() {
  if (!notificationsSupported()) return 'unsupported';
  return Notification.permission; // 'default' | 'granted' | 'denied'
}

// Registriert den SW (ohne Permission-Abfrage, ohne Prompt).
export async function initServiceWorker() {
  if (!('serviceWorker' in navigator)) return null;
  try {
    swRegistration = await navigator.serviceWorker.register('/static/fitness/sw.js');
    return swRegistration;
  } catch (e) {
    return null;
  }
}

// Per Nutzer-Geste (Tap) aufrufen — iOS verlangt eine Geste.
export async function requestNotificationPermission() {
  if (!notificationsSupported()) return 'unsupported';
  try {
    const result = await Notification.requestPermission();
    if (result === 'granted' && !swRegistration) await initServiceWorker();
    return result;
  } catch (e) {
    return 'denied';
  }
}

async function getRegistration() {
  if (swRegistration) return swRegistration;
  if (!('serviceWorker' in navigator)) return null;
  try {
    const reg = await navigator.serviceWorker.getRegistration('/static/fitness/sw.js');
    if (reg) {
      swRegistration = reg;
      return reg;
    }
  } catch (e) {
    /* ignore */
  }
  return initServiceWorker();
}

// Hintergrund-Benachrichtigung am Pausenende. Gibt false zurück (kein Fehler),
// wenn keine Erlaubnis / nicht unterstützt — Aufrufer fällt auf Ton+Vibration.
export async function showRestDoneNotification() {
  try {
    if (notificationPermission() !== 'granted') return false;
    const reg = await getRegistration();
    if (!reg) return false;
    await reg.showNotification('Pause vorbei 💪', {
      body: "Weiter geht's — die nächste Übung wartet.",
      icon: '/static/fitness/icon-192.png',
      badge: '/static/fitness/icon-192.png',
      tag: 'corvis-rest',
      renotify: true,
      vibrate: [180, 80, 180],
    });
    return true;
  } catch (e) {
    return false;
  }
}
