/**
 * Verdrahtung: Ereignisse -> Zustand -> Server -> Anzeige.
 *
 * Diese Datei haelt keine Logik und kein Aussehen - sie verbindet nur.
 * Wer wissen will, WAS bewertet wird, liest das Backend; wer wissen
 * will, WIE es aussieht, liest ui.js; wer wissen will, was passiert,
 * wenn man klickt, liest diese Datei.
 */

import * as api from './api.js';
import * as zustand from './state.js';
import * as ui from './ui.js';

const $ = (id) => document.getElementById(id);

let katalog = new Map();      // slug -> Brawler
let brawlerListe = [];
let modi = [];
let persoenlich = {};
let bewertungen = new Map();  // slug -> {score, rang}
let filter = { suche: '', rolle: null };
let laufendeAnfrage = 0;

// ─── Start ──────────────────────────────────────────────────
async function start() {
  try {
    const daten = await api.katalog();
    brawlerListe = daten.brawler;
    katalog = new Map(daten.brawler.map((b) => [b.slug, b]));
    modi = daten.modi;
    persoenlich = daten.persoenlich || {};
  } catch (fehler) {
    $('panel').textContent = `Katalog konnte nicht geladen werden: ${fehler.message}`;
    return;
  }

  fuelleModi();
  baueRollenfilter();
  verdrahte();

  zustand.abonnieren(zeichne);
  // Erste Map vorauswaehlen - ohne Map keine sinnvolle Bewertung.
  if (modi.length && modi[0].maps.length) {
    zustand.setzen({ mode: modi[0].slug, map: modi[0].maps[0].slug });
  } else {
    zeichne();
  }
}

function fuelleModi() {
  const auswahl = $('modus');
  auswahl.replaceChildren();
  modi.forEach((m) => {
    const option = document.createElement('option');
    option.value = m.slug;
    option.textContent = m.name;
    auswahl.appendChild(option);
  });
  fuelleMaps(modi[0]);
}

function fuelleMaps(modus) {
  const auswahl = $('karte');
  auswahl.replaceChildren();
  if (!modus) return;
  modus.maps.forEach((k) => {
    const option = document.createElement('option');
    option.value = k.slug;
    option.textContent = k.name;
    option.title = k.notiz || '';
    auswahl.appendChild(option);
  });
}

function baueRollenfilter() {
  const container = $('rollenfilter');
  const rollen = [...new Set(brawlerListe.flatMap((b) => b.tags))].sort();
  rollen.forEach((rolle) => {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.textContent = rolle;
    knopf.dataset.rolle = rolle;
    container.appendChild(knopf);
  });
}

// ─── Ereignisse ─────────────────────────────────────────────
function verdrahte() {
  $('modus').addEventListener('change', (e) => {
    const modus = modi.find((m) => m.slug === e.target.value);
    fuelleMaps(modus);
    zustand.setzen({ mode: e.target.value, map: modus?.maps[0]?.slug || null });
  });

  $('karte').addEventListener('change', (e) => zustand.setzen({ map: e.target.value }));

  document.querySelectorAll('[data-firstpick]').forEach((knopf) => {
    knopf.addEventListener('click', () => {
      document.querySelectorAll('[data-firstpick]').forEach((k) => k.classList.remove('ist-aktiv'));
      knopf.classList.add('ist-aktiv');
      zustand.setzen({ own_team_first_pick: knopf.dataset.firstpick === 'wir' });
    });
  });

  $('ban-fertig').addEventListener('click', () => zustand.setzen({ banphase: false, ziel: null }));
  $('zuruecksetzen').addEventListener('click', () => {
    document.querySelector('.hinweis-demo')?.scrollIntoView({ behavior: 'smooth' });
    zustand.zuruecksetzen();
  });

  $('suche').addEventListener('input', (e) => {
    filter = { ...filter, suche: e.target.value };
    zeichneNurGitter();
  });

  $('rollenfilter').addEventListener('click', (e) => {
    const knopf = e.target.closest('[data-rolle]');
    if (!knopf) return;
    const neue = filter.rolle === knopf.dataset.rolle ? null : knopf.dataset.rolle;
    filter = { ...filter, rolle: neue };
    $('rollenfilter').querySelectorAll('button').forEach((k) => {
      k.classList.toggle('ist-aktiv', k.dataset.rolle === neue);
    });
    zeichneNurGitter();
  });

  // Klick auf eine Brawlerkarte: an die aktuelle Zielposition setzen.
  $('gitter').addEventListener('click', (e) => {
    const karte = e.target.closest('[data-slug]');
    if (karte && !karte.disabled) zustand.hinzufuegen(karte.dataset.slug);
  });

  // Klick auf einen belegten Slot: Pick zuruecknehmen. Klick auf einen
  // freien Slot: dorthin zielen (fuer Korrekturen ausserhalb der
  // Standardreihenfolge).
  document.querySelector('.draftbereich').addEventListener('click', (e) => {
    const slot = e.target.closest('.slot');
    if (!slot) return;
    if (slot.dataset.entfernen) zustand.entfernen(slot.dataset.entfernen);
    else if (slot.dataset.ziel) zustand.setzen({ ziel: slot.dataset.ziel });
  });

  // Klick auf eine Empfehlung oder einen Ban-Vorschlag.
  $('panel').addEventListener('click', async (e) => {
    const ban = e.target.closest('[data-slug]');
    if (ban) { zustand.hinzufuegen(ban.dataset.slug); return; }
    const vorschlag = e.target.closest('[data-detail]');
    if (!vorschlag) return;
    try {
      const daten = await api.detail(zustand.fuerServer(), vorschlag.dataset.detail);
      ui.zeigeDetail(daten);
    } catch (fehler) {
      alert(fehler.message);
    }
  });

  $('modal-schliessen').addEventListener('click', ui.schliesseModal);
  $('modal').addEventListener('click', (e) => {
    if (e.target === $('modal')) ui.schliesseModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') ui.schliesseModal();
  });
}

// ─── Zeichnen ───────────────────────────────────────────────
function zeichneNurGitter() {
  ui.zeichneGitter(brawlerListe, zustand.gesperrt(), bewertungen, persoenlich, filter);
}

function zeichne() {
  const z = zustand.hole();
  const ziel = zustand.naechstesZiel();

  ui.zeichneSlots('slots-gegner', z.enemy_picks, 3, katalog, 'gegner', ziel === 'gegner');
  ui.zeichneSlots('slots-wir', z.own_picks, 3, katalog, 'wir', ziel === 'wir');
  ui.zeichneSlots('slots-ban', z.bans, 6, katalog, 'ban', ziel === 'ban', 'slot--ban');
  zeichneNurGitter();

  const ziele = { ban: 'Ban wählen', wir: 'Unser Pick', gegner: 'Gegnerischer Pick' };
  $('ziel').textContent = ziel ? ziele[ziel] : 'Draft vollständig';
  $('ban-fertig').hidden = !z.banphase;

  hole();
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
  try {
    const fertig = z.own_picks.length === 3 && z.enemy_picks.length === 3;
    const antwort = fertig
      ? await api.endanalyse(zustand.fuerServer())
      : await api.empfehlen(zustand.fuerServer());
    if (lauf !== laufendeAnfrage) return;

    bewertungen = new Map(
      (antwort.empfehlungen || []).map((e, i) => [e.slug, { score: e.score, rang: i }])
    );
    zeichneNurGitter();

    if (antwort.endanalyse) {
      ui.zeichneMatchplan(antwort.endanalyse);
      ui.zeichneSiegchance(antwort.endanalyse.siegchance);
    } else {
      ui.zeichnePanel(antwort);
      ui.zeichneSiegchance(antwort.siegchance);
    }

    const stand = antwort.draft_state || {};
    $('phase').textContent = stand.phase_label || '—';
    if (antwort.datenlage) $('datenlage').textContent = antwort.datenlage.hinweis;
    $('wir-hinweis').textContent = stand.am_zug === 'own' ? 'am Zug' : '';
    $('gegner-hinweis').textContent = stand.am_zug === 'enemy' ? 'am Zug' : '';
  } catch (fehler) {
    if (lauf !== laufendeAnfrage) return;
    $('panel').replaceChildren();
    const p = document.createElement('p');
    p.className = 'panel-leer';
    p.textContent = `Fehler: ${fehler.message}`;
    $('panel').appendChild(p);
  }
}

start();
