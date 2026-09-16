/**
 * Der Draftzustand im Browser.
 *
 * Eine einzige Quelle der Wahrheit, mit `abonnieren()` fuer alles, was
 * sich darauf neu zeichnen muss. Ohne das wuerde jeder Klick an drei
 * Stellen von Hand nachgezogen - und eine davon wuerde man vergessen.
 *
 * Der Zustand ist absichtlich klein: Modus, Map, drei Listen, zwei
 * Schalter. Alles Abgeleitete (Phase, Empfehlungen, Bewertung) rechnet
 * der Server, damit Anzeige und Bewertung nicht auseinander laufen.
 */

export const BANS_GESAMT = 6;
export const PICKS_JE_TEAM = 3;

const LEER = () => ({
  mode: null,
  map: null,
  own_picks: [],
  enemy_picks: [],
  bans: [],
  own_team_first_pick: true,

  // Reine Anzeigezustaende - gehen nicht an den Server.
  //
  // `modus` ist der Ban/Pick-Schalter aus der Aktionsleiste. Er stand
  // frueher nicht im Zustand, sondern steckte in einem Knopf
  // ("Ban-Phase beenden"), der nur in eine Richtung ging: einmal aus der
  // Ban-Phase heraus, nie zurueck. Ein echter Draft braucht beides -
  // man verklickt sich, oder der Gegner bannt noch, waehrend man die
  // eigenen Picks schon durchspielt.
  modus: 'ban',
  // Einmalige Zielkorrektur durch Klick auf einen freien Slot. Gilt fuer
  // genau eine Auswahl und faellt danach auf die Reihenfolge zurueck.
  seite: null,
});

let zustand = LEER();
const zuhoerer = new Set();

export function hole() {
  return zustand;
}

/** Nur die Felder, die der Server kennt. */
export function fuerServer() {
  const { mode, map, own_picks, enemy_picks, bans, own_team_first_pick } = zustand;
  return { mode, map, own_picks, enemy_picks, bans, own_team_first_pick };
}

export function abonnieren(fn) {
  zuhoerer.add(fn);
  return () => zuhoerer.delete(fn);
}

function melden() {
  zuhoerer.forEach((fn) => fn(zustand));
}

export function setzen(aenderung) {
  zustand = { ...zustand, ...aenderung };
  melden();
}

export function zuruecksetzen() {
  const { mode, map, own_team_first_pick } = zustand;
  zustand = { ...LEER(), mode, map, own_team_first_pick };
  melden();
}

/** Alles, was nicht mehr waehlbar ist. */
export function gesperrt() {
  return new Set([...zustand.own_picks, ...zustand.enemy_picks, ...zustand.bans]);
}

/**
 * Wohin gehoert der naechste Klick?
 *
 * Bildet die Standardreihenfolge 1-2-2-1 nach - dieselbe, die der
 * Server in services/context.py benutzt. Sie steht hier ein zweites
 * Mal, weil die Oberflaeche schon VOR der Antwort wissen muss, wohin
 * ein Klick geht; der Server bleibt die Instanz, die es bewertet.
 *
 * Reihenfolge der Entscheidung:
 *   1. Ban-Modus und noch Bans frei  -> Ban. Der Schalter gewinnt, damit
 *      ein Klick darauf sofort wirkt und nicht erst "ab dem naechsten Mal".
 *   2. Eine angeklickte freie Position -> die.
 *   3. Sonst die Standardreihenfolge.
 */
const REIHENFOLGE = ['first', 'second', 'second', 'first', 'first', 'second'];

export function naechstesZiel() {
  if (zustand.modus === 'ban' && zustand.bans.length < BANS_GESAMT) return 'ban';

  if (zustand.seite === 'ban' && zustand.bans.length < BANS_GESAMT) return 'ban';
  if (zustand.seite === 'wir' && zustand.own_picks.length < PICKS_JE_TEAM) return 'wir';
  if (zustand.seite === 'gegner' && zustand.enemy_picks.length < PICKS_JE_TEAM) return 'gegner';

  const gesamt = zustand.own_picks.length + zustand.enemy_picks.length;
  if (gesamt >= REIHENFOLGE.length) return null;

  const unser = zustand.own_team_first_pick ? 'first' : 'second';
  const dran = REIHENFOLGE[gesamt];
  const seite = dran === unser ? 'wir' : 'gegner';

  // Weicht der tatsaechliche Stand von der Reihenfolge ab (der Nutzer
  // hat korrigiert), zaehlt der Platz, der noch frei ist.
  const liste = seite === 'wir' ? zustand.own_picks : zustand.enemy_picks;
  if (liste.length >= PICKS_JE_TEAM) return seite === 'wir' ? 'gegner' : 'wir';
  return seite;
}

/**
 * Die laufende Nummer der naechsten Aktion - fuer "UNSER PICK 2/3".
 * Ohne sie muesste die Anzeige denselben Schluss noch einmal ziehen.
 */
export function zielStand() {
  const ziel = naechstesZiel();
  if (ziel === 'ban') return { ziel, nummer: zustand.bans.length + 1, von: BANS_GESAMT };
  if (ziel === 'wir') return { ziel, nummer: zustand.own_picks.length + 1, von: PICKS_JE_TEAM };
  if (ziel === 'gegner') return { ziel, nummer: zustand.enemy_picks.length + 1, von: PICKS_JE_TEAM };
  return { ziel: null, nummer: 0, von: 0 };
}

export function hinzufuegen(slug) {
  const ziel = naechstesZiel();
  if (!ziel || gesperrt().has(slug)) return false;

  if (ziel === 'ban') {
    const bans = [...zustand.bans, slug];
    // Sind alle sechs Bans gesetzt, schaltet die Leiste von selbst auf
    // Pick. Die Automatik bleibt - nur ist sie jetzt sichtbar, weil sie
    // denselben Schalter umlegt, den auch der Nutzer bedient.
    setzen({
      bans,
      seite: null,
      modus: bans.length >= BANS_GESAMT ? 'pick' : zustand.modus,
    });
  } else if (ziel === 'wir') {
    setzen({ own_picks: [...zustand.own_picks, slug], seite: null, modus: 'pick' });
  } else {
    setzen({ enemy_picks: [...zustand.enemy_picks, slug], seite: null, modus: 'pick' });
  }
  return true;
}

export function entfernen(slug) {
  setzen({
    own_picks: zustand.own_picks.filter((s) => s !== slug),
    enemy_picks: zustand.enemy_picks.filter((s) => s !== slug),
    bans: zustand.bans.filter((s) => s !== slug),
  });
}
