// Grenzen und Filter fuer eingetragene Werte.
//
// Die Grenzen spiegeln fitness/models.py (MAX_REPS, MAX_SECONDS). Massgeblich
// ist das Backend - hier geht es nur darum, dass der Nutzer den Fehler sieht,
// bevor er absendet.
export const MAX_REPS = 500;
export const MAX_SECONDS = 7200;

// Nur Ziffern durchlassen. Mit type="number" laesst sich "7.5" eintippen, und
// parseInt macht daraus still eine 7 - der Nutzer sieht nie, dass seine
// Eingabe veraendert wurde. Hier entsteht die Nachkommastelle gar nicht erst.
export function nurZiffern(text) {
  return String(text ?? '').replace(/[^0-9]/g, '');
}
