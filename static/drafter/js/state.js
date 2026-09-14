/**
 * Der Draftzustand im Browser.
 *
 * Eine einzige Quelle der Wahrheit, mit `abonnieren()` fuer alles, was
 * sich darauf neu zeichnen muss. Ohne das wuerde jeder Klick an drei
 * Stellen von Hand nachgezogen - und eine davon wuerde man vergessen.
 *
 * Der Zustand ist absichtlich klein: Modus, Map, drei Listen, ein
 * Schalter. Alles Abgeleitete (Phase, wer am Zug ist, Empfehlungen)
 * rechnet der Server, damit Anzeige und Bewertung nicht auseinander
 * laufen koennen.
 */

const LEER = () => ({
  mode: null,
  map: null,
  own_picks: [],
  enemy_picks: [],
  bans: [],
  own_team_first_pick: true,
  // Reine Anzeigezustaende - gehen nicht an den Server.
  banphase: true,
  ziel: null,
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
 */
const REIHENFOLGE = ['first', 'second', 'second', 'first', 'first', 'second'];

export function naechstesZiel() {
  if (zustand.ziel) return zustand.ziel;
  if (zustand.banphase && zustand.bans.length < 6) return 'ban';

  const gesamt = zustand.own_picks.length + zustand.enemy_picks.length;
  if (gesamt >= 6) return null;

  const unser = zustand.own_team_first_pick ? 'first' : 'second';
  const dran = REIHENFOLGE[gesamt];
  const seite = dran === unser ? 'wir' : 'gegner';

  // Weicht der tatsaechliche Stand von der Reihenfolge ab (der Nutzer
  // hat korrigiert), zaehlt der Platz, der noch frei ist.
  const liste = seite === 'wir' ? zustand.own_picks : zustand.enemy_picks;
  if (liste.length >= 3) return seite === 'wir' ? 'gegner' : 'wir';
  return seite;
}

export function hinzufuegen(slug) {
  const ziel = naechstesZiel();
  if (!ziel || gesperrt().has(slug)) return false;

  if (ziel === 'ban') setzen({ bans: [...zustand.bans, slug], ziel: null });
  else if (ziel === 'wir') setzen({ own_picks: [...zustand.own_picks, slug], ziel: null });
  else setzen({ enemy_picks: [...zustand.enemy_picks, slug], ziel: null });
  return true;
}

export function entfernen(slug) {
  setzen({
    own_picks: zustand.own_picks.filter((s) => s !== slug),
    enemy_picks: zustand.enemy_picks.filter((s) => s !== slug),
    bans: zustand.bans.filter((s) => s !== slug),
  });
}
