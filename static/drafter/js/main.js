/**
 * Verdrahtung: Ereignisse -> Zustand -> Server -> Anzeige.
 *
 * Diese Datei haelt keine Logik und kein Aussehen - sie verbindet nur.
 * Wer wissen will, WAS bewertet wird, liest das Backend; wer wissen
 * will, WIE es aussieht, liest ui.js; wer wissen will, was passiert,
 * wenn man klickt, liest diese Datei.
 *
 * Grundsatz der Oberflaeche: **nichts wartet auf den Server.** Ein Klick
 * setzt den Pick sofort ins Brett und ins Gitter; die Empfehlung kommt
 * nach. Solange sie unterwegs ist, bleibt die vorherige stehen und wird
 * nur gedaempft - ein leeres Panel nach jedem Klick fuehlt sich an wie
 * ein Haenger, auch wenn die Antwort in 200 ms da ist.
 */

import * as api from './api.js';
import * as zustand from './state.js';
import * as ui from './ui.js';

const $ = (id) => document.getElementById(id);

let katalog = new Map();      // slug -> Brawler
let brawlerListe = [];
let modi = [];
let rollen = [];              // [{key, label}] in kanonischer Reihenfolge
let rollenrang = {};          // key -> Index, fuer die Sortierung "Rolle"
let persoenlich = {};
let bewertungen = new Map();  // slug -> {score, rang|null}
let filter = { suche: '', rolle: null, nurMeine: false, sortierung: 'name', banRang: false };
let laufendeAnfrage = 0;
let letzteMaps = [];          // [{mode, map}] - zuletzt benutzt, aus localStorage
let letzteAntwort = null;     // fuer die Ban-Begruendung hinter dem Fragezeichen

/**
 * Picks ohne Profil laut Server (Teamanalysen). Die Engine rechnet sie
 * als unbekannt - nicht als 0 -, das Panel nennt sie trotzdem, damit
 * klar ist, dass fuer sie nur Messwerte zaehlen.
 */
function ohneProfil(antwort) {
  return [
    ...((antwort.team_analyse || {}).unbekannt || []),
    ...((antwort.gegner_analyse || {}).unbekannt || []),
  ];
}

// ─── Gedaechtnis des Browsers ───────────────────────────────
// Bewusst nur Bedienkomfort: Sortierung und zuletzt benutzte Maps. Der
// Draftzustand selbst gehoert NICHT hierher - ein halb gefuellter Draft
// von gestern ist beim naechsten Start eine Falle, keine Hilfe.
const SPEICHER = 'drafter:';

function gelesen(schluessel, ersatz) {
  try {
    const roh = localStorage.getItem(SPEICHER + schluessel);
    return roh ? JSON.parse(roh) : ersatz;
  } catch (fehler) {
    return ersatz;
  }
}

function geschrieben(schluessel, wert) {
  try {
    localStorage.setItem(SPEICHER + schluessel, JSON.stringify(wert));
  } catch (fehler) {
    /* Privater Modus oder gesperrter Speicher - die Seite lebt ohne. */
  }
}

// ─── Start ──────────────────────────────────────────────────
async function start() {
  try {
    const daten = await api.katalog();
    brawlerListe = daten.brawler;
    katalog = new Map(daten.brawler.map((b) => [b.slug, b]));
    modi = daten.modi;
    rollen = daten.rollen || [];
    rollen.forEach((r, i) => { rollenrang[r.key] = i; });
    persoenlich = daten.persoenlich || {};
  } catch (fehler) {
    ui.panelFehler(`Katalog konnte nicht geladen werden: ${fehler.message}`);
    return;
  }

  filter.sortierung = gelesen('sortierung', 'name');
  $('sortierung').value = filter.sortierung;
  letzteMaps = gelesen('letzte-maps', []);

  baueRollenfilter();
  verdrahte();
  zustand.abonnieren(zeichne);

  // Map vorauswaehlen: die zuletzt benutzte, sonst die erste. Ohne Map
  // gibt es keine Bewertung - und der haeufigste Fall ist, dass man
  // dieselbe Map noch einmal draftet.
  const letzte = letzteMaps[0];
  const modus = (letzte && modi.find((m) => m.slug === letzte.mode)) || modi[0];
  const karte = modus && (
    (letzte && modus.maps.find((k) => k.slug === letzte.map)) || modus.maps[0]
  );
  if (modus && karte) {
    zustand.setzen({ mode: modus.slug, map: karte.slug });
  } else {
    zeichne();
  }
}

function baueRollenfilter() {
  const container = $('rollenfilter');
  container.replaceChildren();

  // Nur Rollen, die im aktiven Pool wirklich vorkommen - ein Filter,
  // der garantiert nichts findet, ist nur ein Knopf zum Danebentippen.
  const vorhanden = new Set(brawlerListe.flatMap((b) => b.tags));
  rollen.filter((r) => vorhanden.has(r.key)).forEach((r) => {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.textContent = r.label;
    knopf.dataset.rolle = r.key;
    container.appendChild(knopf);
  });

  // Ersatzkategorie fuer Brawler ohne gepflegtes Profil - die offizielle
  // API liefert keine Rollen, und erfinden werden wir keine.
  if (brawlerListe.some((b) => b.limited)) {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.className = 'rollenfilter-limited';
    knopf.textContent = 'Limited Data';
    knopf.dataset.rolle = '__limited';
    knopf.title = 'Brawler ohne gepflegtes Profil: wählbar, aber nicht bewertet';
    container.appendChild(knopf);
  }

  // "Meine" nur anbieten, wenn ueberhaupt Sicherheitswerte gepflegt
  // sind - als Gast ohne Werte waere der Filter immer leer.
  if (Object.values(persoenlich).some((w) => w > 50)) {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.className = 'rollenfilter-meine';
    knopf.textContent = '★ Meine';
    knopf.dataset.meine = '1';
    knopf.title = 'Nur Brawler, bei denen deine Sicherheit über 50 liegt';
    container.appendChild(knopf);
  }
}

// ─── Ereignisse ─────────────────────────────────────────────
function verdrahte() {
  // --- Aktionsleiste ---
  document.querySelectorAll('[data-firstpick]').forEach((knopf) => {
    knopf.addEventListener('click', () => {
      document.querySelectorAll('[data-firstpick]').forEach((k) => k.classList.remove('ist-aktiv'));
      knopf.classList.add('ist-aktiv');
      zustand.setzen({ own_team_first_pick: knopf.dataset.firstpick === 'wir' });
    });
  });

  document.querySelectorAll('[data-modus]').forEach((knopf) => {
    knopf.addEventListener('click', () => modusSetzen(knopf.dataset.modus));
  });

  $('zuruecksetzen').addEventListener('click', () => zustand.zuruecksetzen());

  // --- Map-Waehler ---
  $('mapknopf').addEventListener('click', () => mapWaehlerOeffnen());
  $('mapsuche').addEventListener('input', () => {
    ui.zeichneMapListe(modi, $('mapsuche').value, letzteMaps, zustand.hole().map);
  });
  $('mapsuche').addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); ui.markiereMapzeile(1, true); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); ui.markiereMapzeile(-1, true); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      const zeile = $('mapwaehler-liste').querySelector('.mapzeile.ist-markiert');
      if (zeile) mapSetzen(zeile.dataset.mode, zeile.dataset.map);
    }
  });
  $('mapwaehler').addEventListener('click', (e) => {
    const zeile = e.target.closest('.mapzeile');
    if (zeile) { mapSetzen(zeile.dataset.mode, zeile.dataset.map); return; }
    if (e.target === $('mapwaehler')) mapWaehlerSchliessen();
  });

  // --- Suche, Sortierung, Rollenfilter ---
  $('suche').addEventListener('input', (e) => {
    filter = { ...filter, suche: e.target.value };
    zeichneNurGitter();
  });
  // Enter im Suchfeld nimmt den ersten Treffer. Wer den Namen kennt,
  // kommt damit ohne Maus und ohne Hinsehen zum Pick.
  $('suche').addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const erste = $('gitter').querySelector('.kachel:not([disabled])');
    if (!erste) return;
    if (analysemodus) zeigeAnalyse(erste.dataset.slug);
    else waehle(erste.dataset.slug);
  });

  $('sortierung').addEventListener('change', (e) => {
    filter = { ...filter, sortierung: e.target.value };
    geschrieben('sortierung', filter.sortierung);
    zeichneNurGitter();
  });

  $('rollenfilter').addEventListener('click', (e) => {
    const knopf = e.target.closest('button');
    if (!knopf) return;
    if (knopf.dataset.meine) {
      filter = { ...filter, nurMeine: !filter.nurMeine };
      knopf.classList.toggle('ist-aktiv', filter.nurMeine);
    } else {
      const neue = filter.rolle === knopf.dataset.rolle ? null : knopf.dataset.rolle;
      filter = { ...filter, rolle: neue };
      $('rollenfilter').querySelectorAll('[data-rolle]').forEach((k) => {
        k.classList.toggle('ist-aktiv', k.dataset.rolle === neue);
      });
    }
    zeichneNurGitter();
  });

  // --- Gitter ---
  $('gitter').addEventListener('click', async (e) => {
    const kachel = e.target.closest('[data-slug]');
    if (!kachel || kachel.disabled) return;
    if (analysemodus) { await zeigeAnalyse(kachel.dataset.slug); return; }
    waehle(kachel.dataset.slug);
  });

  // --- Analysemodus ---
  $('analysemodus').addEventListener('click', () => analyseUmschalten(!analysemodus));

  // --- Brett: belegter Slot = zuruecknehmen, freier Slot = dorthin zielen ---
  document.querySelector('.brett').addEventListener('click', (e) => {
    const slot = e.target.closest('.slot');
    if (!slot) return;
    if (slot.dataset.entfernen) {
      zustand.entfernen(slot.dataset.entfernen);
    } else if (slot.dataset.ziel) {
      zustand.setzen({
        seite: slot.dataset.ziel,
        modus: slot.dataset.ziel === 'ban' ? 'ban' : 'pick',
      });
    }
  });

  // --- Panel: Karte waehlt, Fragezeichen erklaert ---
  $('panel').addEventListener('click', async (e) => {
    const info = e.target.closest('[data-detail]');
    if (info) {
      try {
        ui.zeigeDetail(await api.detail(zustand.fuerServer(), info.dataset.detail));
      } catch (fehler) {
        ui.panelFehler(fehler.message);
      }
      return;
    }
    const banInfo = e.target.closest('[data-bangruende]');
    if (banInfo) {
      const ban = ((letzteAntwort || {}).ban_empfehlungen || [])
        .find((b) => b.slug === banInfo.dataset.bangruende);
      if (ban) ui.zeigeBanGruende(ban);
      return;
    }
    const karte = e.target.closest('[data-waehlen]');
    if (karte) waehle(karte.dataset.waehlen);
  });

  // --- Modal ---
  $('modal-schliessen').addEventListener('click', ui.schliesseModal);
  $('modal').addEventListener('click', (e) => {
    if (e.target === $('modal')) ui.schliesseModal();
  });

  document.addEventListener('keydown', tastatur);
}

/**
 * Tastenkuerzel.
 *
 * Zusatzkomfort, nie Voraussetzung: jede Taste hier hat einen sichtbaren
 * Knopf daneben. Deshalb steht das Kuerzel auch AUF dem Knopf - ein
 * Shortcut, den man nicht sieht, benutzt niemand.
 *
 * In einem Eingabefeld gilt nur Escape und Strg+K; sonst waere "b"
 * im Suchfeld ein Moduswechsel statt eines Buchstabens.
 */
function tastatur(e) {
  const imFeld = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName);

  if (e.key === 'Escape') {
    if (ui.modalOffen()) { ui.schliesseModal(); return; }
    if (!$('mapwaehler').hidden) { mapWaehlerSchliessen(); return; }
    if (imFeld && e.target.id === 'suche') {
      if (e.target.value) { e.target.value = ''; filter = { ...filter, suche: '' }; zeichneNurGitter(); }
      else e.target.blur();
    }
    return;
  }

  if (e.key.toLowerCase() === 'k' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    sucheFokussieren();
    return;
  }
  if (imFeld || e.ctrlKey || e.metaKey || e.altKey) return;

  if (e.key === '/') { e.preventDefault(); sucheFokussieren(); return; }
  if (e.key.toLowerCase() === 'b') { e.preventDefault(); modusSetzen('ban'); return; }
  if (e.key.toLowerCase() === 'p') { e.preventDefault(); modusSetzen('pick'); return; }
  if (e.key.toLowerCase() === 'm') { e.preventDefault(); mapWaehlerOeffnen(); return; }

  // 1-9 nehmen die n-te Empfehlung. Der schnellste Weg von "gelesen"
  // zu "gesetzt", ohne die Hand von der Tastatur zu nehmen.
  if (/^[1-9]$/.test(e.key)) {
    const karten = $('panel').querySelectorAll('[data-waehlen]');
    const karte = karten[Number(e.key) - 1];
    if (karte) { e.preventDefault(); waehle(karte.dataset.waehlen); }
  }
}

function sucheFokussieren() {
  const feld = $('suche');
  feld.focus();
  feld.select();
}

function modusSetzen(modus) {
  document.querySelectorAll('[data-modus]').forEach((k) => {
    k.classList.toggle('ist-aktiv', k.dataset.modus === modus);
  });
  // `seite` mit zuruecksetzen: eine vorher angeklickte Zielposition
  // wuerde den Schalter sonst stillschweigend ueberstimmen.
  zustand.setzen({ modus, seite: null });
}

/**
 * Einen Brawler setzen - egal ob aus Gitter, Empfehlung oder Tastatur.
 *
 * Genau ein Weg, damit "Klick in der Empfehlung" und "Klick im Gitter"
 * nicht auseinander laufen koennen (das war die Anforderung: beides muss
 * identisch wirken).
 */
function waehle(slug) {
  // Setzt den Pick und zeichnet ueber den Abonnenten alles neu.
  if (!zustand.hinzufuegen(slug)) return;

  // Suche leeren, Fokus lassen, wo er war. Der naechste Pick ist ein
  // anderer Brawler - ein stehengebliebener Suchtext versteckt genau
  // die Kacheln, die man als naechstes braucht. Wer im Suchfeld steht,
  // bleibt dort und kann sofort weitertippen.
  const feld = $('suche');
  if (feld.value) {
    feld.value = '';
    filter = { ...filter, suche: '' };
    zeichneNurGitter();
  }
}

// ─── Zeichnen ───────────────────────────────────────────────
// Analysemodus: der Klick auf eine Kachel erklaert, statt zu waehlen.
// Bewusst NICHT gespeichert - ein Modus, der einen Tag spaeter noch
// aktiv waere, laesst den naechsten Pick ins Leere gehen.
let analysemodus = false;

function analyseUmschalten(an) {
  analysemodus = an;
  $('analysemodus').setAttribute('aria-pressed', an ? 'true' : 'false');
  $('gitter').classList.toggle('ist-analyse', an);
}

/** Vollstaendige Bewertung eines beliebigen Brawlers zeigen.
 *
 * Dieselbe Schnittstelle wie das Fragezeichen auf einer Empfehlungskarte -
 * nur eben fuer jeden Kandidaten, auch wenn ihn niemand vorschlaegt.
 */
async function zeigeAnalyse(slug) {
  try {
    ui.zeigeDetail(await api.detail(zustand.fuerServer(), slug));
  } catch (fehler) {
    ui.panelFehler(fehler.message);
  }
}

function zeichneNurGitter() {
  ui.zeichneGitter(brawlerListe, zustand.gesperrt(), bewertungen, persoenlich,
    filter, rollenrang);
}

function zeichne() {
  const z = zustand.hole();
  const stand = zustand.zielStand();
  const ziel = stand.ziel;

  // Der Rang im Gitter zeigt im Ban-Modus die Ban-Empfehlungen.
  filter = { ...filter, banRang: ziel === 'ban' };

  ui.zeichneSlots('slots-gegner', z.enemy_picks, 3, katalog, 'gegner', ziel === 'gegner');
  ui.zeichneSlots('slots-wir', z.own_picks, 3, katalog, 'wir', ziel === 'wir');
  ui.zeichneSlots('slots-ban', z.bans, 6, katalog, 'ban', ziel === 'ban', 'slot--ban');
  zeichneNurGitter();

  const modus = modi.find((m) => m.slug === z.mode);
  ui.zeichneMapKnopf(modus, modus && modus.maps.find((k) => k.slug === z.map));
  ui.zeichneJetzt(stand, null, !!z.map);

  document.querySelectorAll('[data-modus]').forEach((k) => {
    k.classList.toggle('ist-aktiv', k.dataset.modus === z.modus);
  });

  $('wir-hinweis').textContent = `${z.own_picks.length}/3`;
  $('gegner-hinweis').textContent = `${z.enemy_picks.length}/3`;
  $('ban-hinweis').textContent = `${z.bans.length}/6`;

  hole();
}

function mapWaehlerOeffnen() {
  const waehler = $('mapwaehler');
  waehler.hidden = false;
  $('mapknopf').setAttribute('aria-expanded', 'true');
  $('mapsuche').value = '';
  ui.zeichneMapListe(modi, '', letzteMaps, zustand.hole().map);
  ui.mapWaehlerAusrichten($('mapknopf'));
  $('mapsuche').focus();
}

function mapWaehlerSchliessen() {
  $('mapwaehler').hidden = true;
  $('mapknopf').setAttribute('aria-expanded', 'false');
  $('mapknopf').focus();
}

function mapSetzen(modeSlug, mapSlug) {
  letzteMaps = [{ mode: modeSlug, map: mapSlug }]
    .concat(letzteMaps.filter((e) => e.map !== mapSlug))
    .slice(0, 5);
  geschrieben('letzte-maps', letzteMaps);
  mapWaehlerSchliessen();
  zustand.setzen({ mode: modeSlug, map: mapSlug });
}

/**
 * Empfehlungen holen.
 *
 * Der Zaehler verhindert, dass eine langsame aeltere Antwort eine
 * neuere ueberschreibt - bei schnellem Klicken sonst die haeufigste
 * Fehlerquelle in solchen Oberflaechen.
 */
async function hole() {
  const z = zustand.hole();
  if (!z.map) return;

  const lauf = ++laufendeAnfrage;
  ui.panelLaedt(true);
  try {
    const fertig = z.own_picks.length === 3 && z.enemy_picks.length === 3;
    const daten = zustand.fuerServer();
    const antwort = fertig
      ? await api.endanalyse(daten)
      : await api.empfehlen(daten);
    if (lauf !== laufendeAnfrage) return;
    letzteAntwort = antwort;

    const ziel = zustand.naechstesZiel();
    bewertungen = bewertungenBauen(antwort, ziel);
    zeichneNurGitter();

    if (antwort.endanalyse) {
      ui.zeichneMatchplan(antwort.endanalyse);
      ui.zeichneSiegchance(antwort.endanalyse.siegchance);
    } else {
      ui.zeichnePanel(antwort, ziel, ohneProfil(antwort));
      ui.zeichneSiegchance(antwort.siegchance);
    }

    const zusatz = (antwort.draft_state || {}).phase_label;
    ui.zeichneJetzt(zustand.zielStand(), zusatz, true);
    datenlageZeigen(antwort);
  } catch (fehler) {
    if (lauf !== laufendeAnfrage) return;
    ui.panelFehler(`Fehler: ${fehler.message}`);
  } finally {
    if (lauf === laufendeAnfrage) ui.panelLaedt(false);
  }
}

/**
 * Score je Kachel + Rang der Spitze.
 *
 * `scores` enthaelt JEDEN bewerteten Kandidaten, nicht nur die acht
 * angezeigten - erst damit kann das Gitter nach Empfehlung sortieren
 * und jede Kachel einen Wert tragen.
 *
 * Der Rang kommt im Ban-Modus aus den Ban-Empfehlungen. Der Score tut
 * das ausdruecklich NICHT: Ban- und Pick-Score messen Verschiedenes,
 * und zwei Skalen im selben Badge waeren nicht zu unterscheiden. Im
 * Gitter steht deshalb durchgehend der Pick-Score ("wie stark ist der
 * hier"), markiert sind die Ban-Kandidaten.
 */
function bewertungenBauen(antwort, ziel) {
  const werte = new Map();
  const stufen = antwort.datenstufen || {};
  Object.entries(antwort.scores || {}).forEach(([slug, score]) => {
    const stufe = stufen[slug] || {};
    werte.set(slug, { score, rang: null, stufe: stufe.stufe, abdeckung: stufe.abdeckung });
  });
  const spitze = ziel === 'ban'
    ? (antwort.ban_empfehlungen || [])
    : (antwort.empfehlungen || []);
  spitze.forEach((e, i) => {
    const vorhanden = werte.get(e.slug);
    werte.set(e.slug, { ...(vorhanden || { score: e.score }), rang: i });
  });
  return werte;
}

function datenlageZeigen(antwort) {
  const kasten = $('datenlage');
  const lage = antwort.datenlage || (antwort.endanalyse || {}).datenlage;
  if (!lage) { kasten.textContent = '—'; return; }
  const spitze = (antwort.empfehlungen || [])[0];
  const label = spitze ? spitze.confidence_label : lage.confidence_label;
  kasten.textContent = `Daten: ${label || '—'}`;
  kasten.title = lage.hinweis || '';
}

start();
