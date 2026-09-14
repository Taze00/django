/**
 * Zugriff auf die Draft-Schnittstelle.
 *
 * Eine Datei, damit CSRF-Token und Fehlerbehandlung genau einmal
 * existieren. Jede Antwort ist JSON - auch im Fehlerfall -, deshalb
 * braucht kein Aufrufer eine Sonderbehandlung fuer HTML-Fehlerseiten.
 */

const BASIS = '/draft/api/';

async function post(pfad, rumpf) {
  const antwort = await fetch(BASIS + pfad, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': window.DRAFTER.csrf,
    },
    body: JSON.stringify(rumpf),
  });
  const daten = await antwort.json().catch(() => ({ fehler: 'Unlesbare Antwort vom Server' }));
  if (!antwort.ok) throw new Error(daten.fehler || `Fehler ${antwort.status}`);
  return daten;
}

export async function katalog() {
  const antwort = await fetch(BASIS + 'katalog/');
  if (!antwort.ok) throw new Error('Katalog konnte nicht geladen werden');
  return antwort.json();
}

export const empfehlen = (zustand) => post('recommend/', zustand);
export const endanalyse = (zustand) => post('final-analysis/', zustand);
export const detail = (zustand, brawler) => post('detail/', { ...zustand, brawler });
export const confidenceSpeichern = (brawler, confidence) =>
  post('confidence/', { brawler, confidence });
