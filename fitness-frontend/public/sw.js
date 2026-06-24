// CORVIS Service Worker — MINIMAL: nur Benachrichtigungen.
// BEWUSST KEIN Offline-Caching / kein fetch-Handler (das ist Etappe 3).

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// Tippt der Nutzer auf die Benachrichtigung: CORVIS-App in den Vordergrund.
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if (client.url.includes('/corvis-app') && 'focus' in client) {
            return client.focus();
          }
        }
        if (self.clients.openWindow) {
          return self.clients.openWindow('/corvis-app/');
        }
        return undefined;
      })
  );
});
