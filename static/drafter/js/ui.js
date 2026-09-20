/**
 * Zeichnen: Aktionsleiste, Brett, Gitter, Panel, Map-Waehler, Modal.
 *
 * Alles hier ist reine Darstellung - kein Zustand, keine Netzanfragen.
 * Jede Funktion bekommt Daten und schreibt DOM. Dadurch bleibt
 * nachvollziehbar, wo etwas herkommt, wenn die Anzeige falsch aussieht:
 * entweder liefert der Server es falsch, oder hier wird es falsch
 * hingeschrieben - nie beides vermischt.
 *
 * Leitlinie fuer die Live-Ansicht (Leiste, Brett, Gitter, Panel):
 * **so wenig Text wie moeglich**. Ein Draft laeuft in Sekunden; was
 * gelesen werden muss, statt erkannt zu werden, kostet einen Pick.
 * Ganze Saetze stehen deshalb nur im Detailfenster und im Matchplan -
 * beides Ansichten, die man ausdruecklich oeffnet.
 */

const $ = (id) => document.getElementById(id);

/** Text sicher einsetzen. Alles Servergelieferte laeuft hier durch. */
function t(text) {
  return document.createTextNode(text == null ? '' : String(text));
}

function el(tag, klassen, text) {
  const knoten = document.createElement(tag);
  if (klassen) knoten.className = klassen;
  if (text != null) knoten.appendChild(t(text));
  return knoten;
}

/**
 * Bereits geladene Bild-URLs.
 *
 * Gitter und Panel werden bei jedem Pick neu gebaut. Ein neues <img>
 * mit `decoding="async"` bekaeme dabei einen Frame ohne Bild - das
 * Kuerzel darunter blitzte bei jedem Klick einmal auf. Was schon
 * einmal geladen war, kommt deshalb sofort und synchron aus dem Cache.
 */
const geladen = new Set();
// Und umgekehrt: was einmal nicht geladen hat, wird nicht bei jedem
// Neuzeichnen erneut angefragt - der Platzhalter bleibt einfach stehen.
const fehlend = new Set();

/**
 * Portrait bzw. Map-Bild mit Kuerzel-Platzhalter.
 *
 * Immer zuerst der eingefaerbte Platzhalter mit Kuerzel - er steht ab
 * dem ersten Frame da, die Kachel springt nicht, und er bleibt, falls
 * die Datei fehlt oder nicht laedt. Das Bild liegt als echtes <img>
 * darueber (lazy, mit fester Groesse), nicht als CSS-Hintergrund:
 * so laedt der Browser nur, was in Sichtweite kommt, und ein Fehler
 * ist ein Ereignis, auf das man reagieren kann.
 */
function bildKnoten(url, kuerzel, farbe, klasse, groesse) {
  const knoten = el('span', `${klasse} bild`);
  knoten.style.background = farbe || '#3a3f4b';
  knoten.appendChild(el('span', 'bild-kuerzel', kuerzel));
  if (!url || fehlend.has(url)) return knoten;

  const img = document.createElement('img');
  img.alt = '';                   // Name steht daneben bzw. im title
  img.width = groesse;
  img.height = groesse;
  if (geladen.has(url)) {
    knoten.classList.add('ist-geladen');
    img.decoding = 'sync';
  } else {
    img.loading = 'lazy';
    img.decoding = 'async';
    img.addEventListener('load', () => {
      geladen.add(url);
      knoten.classList.add('ist-geladen');
    }, { once: true });
    // Fehlt die Datei, bleibt der Platzhalter - kein kaputtes Bildsymbol.
    img.addEventListener('error', () => { fehlend.add(url); img.remove(); }, { once: true });
  }
  img.src = url;
  knoten.appendChild(img);
  return knoten;
}

function bild(brawler, klasse, groesse) {
  return bildKnoten(
    brawler.image_url,
    brawler.initialen || brawler.name.slice(0, 2).toUpperCase(),
    brawler.farbe, klasse, groesse,
  );
}

// ─── Aktionsleiste ──────────────────────────────────────────
const ZIEL_TEXT = {
  ban: 'Ban',
  wir: 'Unser Pick',
  gegner: 'Gegner-Pick',
};

/**
 * Der wichtigste Text der Seite: was jetzt zu tun ist.
 *
 * Gross, farbig nach Seite und mit laufender Nummer ("UNSER PICK 2/3").
 * Vorher stand hier nur die Phase des Servers ("Mittlerer Pick") - die
 * sagt, wie bewertet wird, aber nicht, wohin der naechste Klick geht.
 */
export function zeichneJetzt(stand, zusatz, hatMap) {
  const kasten = $('jetzt');
  const text = $('jetzt-text');
  kasten.classList.remove('jetzt--ban', 'jetzt--wir', 'jetzt--gegner', 'jetzt--fertig');

  if (!hatMap) {
    kasten.classList.add('jetzt--fertig');
    text.textContent = 'Map wählen';
    $('jetzt-zusatz').textContent = 'ohne Map keine Bewertung';
    return;
  }
  if (!stand.ziel) {
    kasten.classList.add('jetzt--fertig');
    text.textContent = 'Draft komplett';
    $('jetzt-zusatz').textContent = zusatz || 'Matchplan rechts';
    return;
  }
  kasten.classList.add(`jetzt--${stand.ziel}`);
  text.textContent = `${ZIEL_TEXT[stand.ziel]} ${stand.nummer}/${stand.von}`;
  $('jetzt-zusatz').textContent = zusatz || '';
}

export function zeichneMapKnopf(modus, karte) {
  const knopf = $('mapknopf');
  $('mapknopf-modus').textContent = modus ? modus.name : '—';
  $('mapknopf-name').textContent = karte ? karte.name : 'wählen';
  knopf.classList.toggle('ist-leer', !karte);

  // Vorschaubild der gesetzten Map - zur Bestaetigung auf einen Blick.
  // Der Platz dafuer wird vom Server reserviert (data-bildplatz), sobald
  // irgendeine Map ein Bild hat - und bleibt dann auch fuer Maps ohne
  // Bild stehen, mit Kuerzel. Sonst sprang der Text bei jedem Mapwechsel
  // zwischen "mit" und "ohne" Bild um die Bildbreite hin und her.
  const platz = knopf.dataset.bildplatz === '1' || !!(karte && karte.image_url);
  knopf.querySelector('.mapknopf-bild')?.remove();
  knopf.classList.toggle('hat-bild', platz);
  if (platz) {
    knopf.prepend(bildKnoten(karte && karte.image_url,
      modus ? modus.name.slice(0, 2).toUpperCase() : '', 'var(--bg-3)', 'mapknopf-bild', 34));
  }
}

// ─── Brett ──────────────────────────────────────────────────
export function zeichneSlots(containerId, slugs, anzahl, katalog, ziel, aktiv, klasse) {
  const container = $(containerId);
  container.replaceChildren();

  for (let i = 0; i < anzahl; i += 1) {
    const slug = slugs[i];
    const slot = el('button', `slot ${klasse || ''}`);
    slot.type = 'button';
    if (slug) {
      const b = katalog.get(slug);
      slot.classList.add('ist-belegt');
      slot.style.borderColor = b.farbe;
      slot.appendChild(bild(b, 'slot-bild', 48));
      slot.appendChild(el('span', 'slot-name', b.name));
      if (b.limited) {
        slot.classList.add('ist-limited');
        slot.appendChild(el('span', 'slot-limited', 'LD'));
      }
      slot.title = `${b.name} entfernen`;
      slot.setAttribute('aria-label', `${b.name} entfernen`);
      slot.dataset.entfernen = slug;
    } else {
      const istZiel = aktiv && i === slugs.length;
      if (istZiel) slot.classList.add('ist-ziel');
      slot.appendChild(el('span', 'slot-leer', istZiel ? '▸' : ''));
      slot.title = istZiel ? 'Hier landet die nächste Auswahl' : 'Hierhin zielen';
      slot.dataset.ziel = ziel;
    }
    container.appendChild(slot);
  }
}

// ─── Brawler-Gitter ─────────────────────────────────────────
/**
 * Sortierungen des Gitters.
 *
 * Voreinstellung ist A-Z und nicht Score: die Kachelposition bleibt
 * damit ueber den ganzen Draft stabil, und ein bekannter Brawler wird
 * gefunden, ohne zu lesen. Wer nach Score sortiert, bekommt nach jedem
 * Pick ein neu gemischtes Gitter - gut zum Stoebern, schlecht zum
 * Wiederfinden. Die Empfehlungen stehen ohnehin im rechten Panel, und
 * die besten Kacheln tragen im Gitter Rang und Score.
 */
const SORTIERER = {
  name: (a, b) => a.name.localeCompare(b.name, 'de'),
  rolle: (a, b) => (a._rollenrang - b._rollenrang) || a.name.localeCompare(b.name, 'de'),
  score: (a, b) => (b._score - a._score) || a.name.localeCompare(b.name, 'de'),
};

export function zeichneGitter(brawler, gesperrt, bewertungen, persoenlich, filter, rollenrang) {
  const gitter = $('gitter');
  gitter.replaceChildren();
  // Im Ban-Modus markiert der Rang die Ban-Empfehlungen, nicht die
  // Pickvorschlaege - die Kachel faerbt sich dann grau statt orange.
  gitter.classList.toggle('ist-banmodus', !!filter.banRang);

  const suche = (filter.suche || '').trim().toLowerCase();
  const rolle = filter.rolle;
  const nurMeine = filter.nurMeine;

  const passend = brawler.filter((b) => {
    if (rolle === '__limited') { if (!b.limited) return false; }
    else if (rolle && !b.tags.includes(rolle)) return false;
    if (nurMeine && (persoenlich[b.slug] || 50) <= 50) return false;
    if (suche && !b.name.toLowerCase().includes(suche)) return false;
    return true;
  });

  // Sortierschluessel einmal anhaengen statt in jedem Vergleich neu
  // nachzuschlagen - der Vergleicher laeuft O(n log n) mal.
  passend.forEach((b) => {
    const bewertung = bewertungen.get(b.slug);
    b._score = bewertung ? bewertung.score : -1;
    b._rollenrang = rollenrang[b.rolle] ?? 99;
    // Wer "ga" tippt, meint Gale und nicht Belle mit "Marksman".
    // Treffer am Wortanfang kommen deshalb vor Treffer in der Mitte -
    // innerhalb der Gruppe gilt weiter die gewaehlte Sortierung.
    b._praefix = suche && b.name.toLowerCase().startsWith(suche) ? 0 : 1;
  });

  const sortierer = SORTIERER[filter.sortierung] || SORTIERER.name;
  passend.sort((a, b) => (a._praefix - b._praefix) || sortierer(a, b));

  passend.forEach((b) => {
    const kachel = el('button', 'kachel');
    kachel.type = 'button';
    kachel.dataset.slug = b.slug;
    kachel.title = `${b.name} · ${b.rollen.join(' · ')}`;

    if (gesperrt.has(b.slug)) {
      kachel.classList.add('ist-gesperrt');
      kachel.disabled = true;
    }

    kachel.appendChild(bild(b, 'kachel-bild', 60));
    kachel.appendChild(el('span', 'kachel-name', b.name));

    const bewertung = bewertungen.get(b.slug);
    if (!bewertung && b.limited) {
      // Weder Profil noch genug Messwerte: kein Score, sichtbar "LD".
      kachel.classList.add('ist-limited');
      kachel.title = `${b.name} · Limited Data: zu wenig Daten für eine Bewertung`;
      kachel.appendChild(el('span', 'kachel-score kachel-score--limited', 'LD'));
    } else if (bewertung) {
      // Rang nur fuer die Spitze - sonst traegt jede Kachel eine Zahl,
      // die niemanden interessiert, und die Spitze faellt nicht mehr auf.
      if (bewertung.rang != null && bewertung.rang < 6) {
        kachel.classList.add('ist-empfohlen');
        if (bewertung.rang === 0) kachel.classList.add('ist-bester');
        const rang = el('span', 'kachel-rang', bewertung.rang + 1);
        rang.title = filter.banRang
          ? `Ban-Empfehlung #${bewertung.rang + 1}`
          : `Empfehlung #${bewertung.rang + 1}`;
        kachel.appendChild(rang);
      }
      const score = el('span', 'kachel-score', bewertung.score);
      if (bewertung.score >= 60) score.classList.add('ist-gut');
      else if (bewertung.score < 45) score.classList.add('ist-schwach');
      if (bewertung.stufe === 'gemessen') {
        // Score nur aus Messwerten: sichtbar anders als ein voll bewerteter.
        score.classList.add('kachel-score--teil');
        kachel.title = `${b.name} · nur Messdaten, Datenabdeckung ${bewertung.abdeckung} %`;
      }
      kachel.appendChild(score);
    }

    const sicher = persoenlich[b.slug];
    if (sicher != null && sicher !== 50) {
      const balken = el('span', 'kachel-sicher');
      balken.style.width = `${Math.max(6, sicher)}%`;
      balken.classList.add(sicher > 50 ? 'ist-hoch' : 'ist-niedrig');
      kachel.appendChild(balken);
    }

    gitter.appendChild(kachel);
  });

  if (!passend.length) {
    gitter.appendChild(el('p', 'panel-leer', 'Kein Brawler passt zu diesem Filter.'));
  }
  return passend;
}

// ─── Gruende ────────────────────────────────────────────────
function gruendeListe(pro, contra) {
  const liste = el('ul', 'gruende');
  (pro || []).forEach((g) => {
    const li = el('li', 'pro', g.text);
    if (g.quelle === 'heuristik') li.appendChild(el('span', 'quelle-heuristik', ' (geschätzt)'));
    liste.appendChild(li);
  });
  (contra || []).forEach((g) => liste.appendChild(el('li', 'contra', g.text)));
  return liste;
}

/**
 * Die drei staerksten Komponenten als Chips.
 *
 * Im Live-Draft steht bewusst NICHT der ausformulierte Grund
 * ("gehoert auf Hard Rock Mine zu den staerksten Picks"), sondern
 * "Map & Modus +18": gleiche Aussage, ein Blick statt einer Zeile, und
 * mit dem Betrag zusaetzlich die Groessenordnung. Der ganze Satz steht
 * im Detailfenster - und im `title`, fuer alle, die hinsehen wollen.
 */
/**
 * Kurzform der Komponenten fuer die Chips. Die langen Namen ("Map &
 * Modus", "Teambedarf") stehen weiter im Detailfenster; auf der Karte
 * zaehlt, dass drei Chips in eine Zeile passen.
 */
const CHIP_KURZ = {
  map_mode: 'Map', meta: 'Meta', counter: 'Counter', synergy: 'Synergie',
  team_need: 'Team', draft_position: 'Position', personal: 'Du',
  flexibility: 'Flex', redundancy: 'Doppelt', weakness: 'Angreifbar',
};

function grundChips(komponenten) {
  const kasten = el('span', 'chips');
  const stark = (komponenten || [])
    // Die Datenlage ist kein Grund fuer oder gegen einen Pick, sondern
    // ein Vorbehalt gegenueber allen anderen - sie steht oben in der
    // Leiste und im Detailfenster, hier verdraengte sie einen echten Grund.
    .filter((k) => k.key !== 'uncertainty' && Math.abs(k.beitrag) >= 1)
    .sort((a, b) => Math.abs(b.beitrag) - Math.abs(a.beitrag))
    .slice(0, 3);

  stark.forEach((k) => {
    const chip = el('span', `chip ${k.beitrag >= 0 ? 'ist-plus' : 'ist-minus'}`);
    chip.appendChild(el('span', 'chip-label', CHIP_KURZ[k.key] || k.label));
    chip.appendChild(el('span', 'chip-wert',
      `${k.beitrag > 0 ? '+' : ''}${Math.round(k.beitrag)}`));
    if (k.gruende && k.gruende.length) {
      chip.title = k.gruende.map((g) => g.text).join('\n');
    }
    kasten.appendChild(chip);
  });
  return kasten;
}

// ─── Score-Aufschlüsselung ──────────────────────────────────
/**
 * Die Komponententabelle - nur noch im Detailfenster.
 *
 * Sie stand frueher aufklappbar in jeder Empfehlungskarte. Das war im
 * Live-Draft totes Gewicht: elf Zeilen je Karte, acht Karten. Die
 * Karten tragen jetzt die drei staerksten Komponenten als Chips, die
 * vollstaendige Tabelle oeffnet das Fragezeichen.
 */
function aufschluesselung(komponenten) {
  const kasten = el('div', 'komponenten');
  const groesster = Math.max(...komponenten.map((k) => Math.abs(k.beitrag)), 1);

  komponenten.forEach((k) => {
    const zeile = el('div', 'komponente');
    if (k.verfuegbar === false) {
      zeile.classList.add('ist-ohne-wirkung', 'ist-unbekannt');
      zeile.appendChild(el('span', 'komponente-label', k.label));
      zeile.appendChild(el('span', 'komponente-unbekannt', 'keine Daten - ausgelassen'));
      kasten.appendChild(zeile);
      return;
    }
    if (Math.abs(k.beitrag) < 0.05) zeile.classList.add('ist-ohne-wirkung');

    // Quelle mitnennen: Measured, Measured + Prior oder Profile. Ohne sie
    // sieht eine gemessene Zeile aus wie eine geschaetzte.
    const label = el('span', 'komponente-label', `${k.label} · ${k.quelle || 'Unknown'}`);
    if (k.gruende && k.gruende.length) {
      label.title = k.gruende.map((g) => g.text).join('\n');
    }
    zeile.appendChild(label);

    const balken = el('div', 'komponente-balken');
    const fuellung = el('div', `komponente-fuellung ${k.beitrag >= 0 ? 'ist-plus' : 'ist-minus'}`);
    fuellung.style.width = `${(Math.abs(k.beitrag) / groesster) * 50}%`;
    balken.appendChild(fuellung);
    zeile.appendChild(balken);

    zeile.appendChild(el('span', 'komponente-roh',
      `${k.wert >= 0 ? '+' : ''}${k.wert.toFixed(2)} × ${k.gewicht.toFixed(2)}`));
    zeile.appendChild(el('span', 'komponente-wert',
      `${k.beitrag > 0 ? '+' : ''}${k.beitrag.toFixed(1)}`));
    kasten.appendChild(zeile);
  });
  return kasten;
}

/**
 * Counter- oder Synergiewerte Paar fuer Paar.
 *
 * Gleiche Darstellung wie die Aufschluesselung, damit beide Tabellen
 * ohne Umgewoehnung zu lesen sind: Name und Quelle links, Balken in der
 * Mitte, der Wert rechts. Ein Paar ohne Datenlage steht ausdruecklich
 * als unbekannt drin - es fehlt nicht.
 */
function paartabelle(zeilen) {
  const kasten = el('div', 'komponenten');
  const groesster = Math.max(...zeilen.map((z) => Math.abs(z.punkte)), 1);

  zeilen.forEach((z) => {
    const zeile = el('div', 'komponente');
    if (!z.bekannt) {
      zeile.classList.add('ist-ohne-wirkung', 'ist-unbekannt');
      zeile.appendChild(el('span', 'komponente-label', z.name));
      zeile.appendChild(el('span', 'komponente-unbekannt', 'nichts bekannt - zählt nicht mit'));
      kasten.appendChild(zeile);
      return;
    }
    if (Math.abs(z.punkte) < 0.05) zeile.classList.add('ist-ohne-wirkung');

    const quelle = z.heuristisch ? `${z.quelle} (Heuristik)` : z.quelle;
    const label = el('span', 'komponente-label', `${z.name} · ${quelle}`);
    if (z.grund) label.title = z.grund;
    zeile.appendChild(label);

    const balken = el('div', 'komponente-balken');
    const fuellung = el('div', `komponente-fuellung ${z.punkte >= 0 ? 'ist-plus' : 'ist-minus'}`);
    fuellung.style.width = `${(Math.abs(z.punkte) / groesster) * 50}%`;
    balken.appendChild(fuellung);
    zeile.appendChild(balken);

    zeile.appendChild(el('span', 'komponente-roh', `Sicherheit ${z.sicherheit.toFixed(2)}`));
    // Drei Stellen, nicht zwei wie bei den Komponenten: gemessene
    // Paarwerte liegen oft bei wenigen Tausendsteln, und "+0.00" neben
    // einem sichtbaren Balken sieht aus wie ein Fehler.
    zeile.appendChild(el('span', 'komponente-wert',
      `${z.wert > 0 ? '+' : ''}${z.wert.toFixed(3)}`));
    kasten.appendChild(zeile);
  });
  return kasten;
}

// ─── Empfehlungspanel ───────────────────────────────────────
/**
 * Zeigt an, dass eine Antwort unterwegs ist - **ohne** die alte zu
 * loeschen. Ein leeres Panel nach jedem Klick ist der Unterschied
 * zwischen "reagiert sofort" und "haengt": die vorige Empfehlung ist
 * eine Sekunde lang eine bessere Auskunft als nichts.
 */
export function panelLaedt(an) {
  $('panel-rahmen').classList.toggle('ist-laedt', !!an);
}

function kopfzeile(text, zusatz) {
  const zeile = el('div', 'panel-kopf');
  zeile.appendChild(el('h2', null, text));
  if (zusatz) zeile.appendChild(el('span', 'panel-kopf-zusatz', zusatz));
  return zeile;
}

/**
 * Eine anklickbare Empfehlungskarte.
 *
 * Der ganze Kasten setzt den Pick bzw. den Ban - genau ein Klick vom
 * Lesen zum Setzen. Frueher oeffnete ein Klick nur die Begruendung, und
 * den Brawler musste man danach im Gitter wiederfinden.
 *
 * Deshalb ZWEI Knoepfe nebeneinander statt ineinander (ein Button im
 * Button ist ungueltiges HTML und fuer Tastatur und Screenreader kaputt):
 * der grosse waehlt, das Fragezeichen erklaert.
 */
function vorschlagsKarte(e, rang, zielText) {
  const karte = el('div', `vorschlag${rang === 0 ? ' vorschlag--top' : ''}`);

  const waehlen = el('button', 'vorschlag-waehlen');
  waehlen.type = 'button';
  waehlen.dataset.waehlen = e.slug;
  waehlen.title = `${e.name} als ${zielText} setzen`;

  waehlen.appendChild(el('span', 'vorschlag-rang', rang + 1));
  waehlen.appendChild(bild(e, 'vorschlag-bild', 40));

  const kern = el('span', 'vorschlag-kern');
  kern.appendChild(el('span', 'vorschlag-name', e.name));
  // Hauptrolle aus dem Katalog ("Controller"), nicht die Coach-Zeile
  // ("Controller / Peel für Mitspieler") - die steht im Detailfenster.
  kern.appendChild(el('span', 'vorschlag-rolle', (e.rollen || [])[0] || e.rolle || ''));
  waehlen.appendChild(kern);

  const score = el('span', 'vorschlag-score', e.score);
  if (e.datenstufe && e.datenstufe !== 'profil') {
    // Teildaten: statt der Siegchance steht, worauf der Score beruht.
    score.appendChild(el('span', 'vorschlag-wp vorschlag-wp--teil', `Daten ${e.datenabdeckung}%`));
  } else if (e.win_probability != null) {
    score.appendChild(el('span', 'vorschlag-wp', `${Math.round(e.win_probability)}%`));
  }
  waehlen.appendChild(score);
  // Eigene Zeile ueber die volle Kartenbreite - neben Portrait und Score
  // passten nur zwei Chips, der dritte brach um und machte jede Karte
  // doppelt so hoch.
  waehlen.appendChild(grundChips(e.komponenten));
  karte.appendChild(waehlen);

  const info = el('button', 'vorschlag-info', '?');
  info.type = 'button';
  info.dataset.detail = e.slug;
  info.setAttribute('aria-label', `Warum ${e.name}? Vollständige Begründung`);
  karte.appendChild(info);
  return karte;
}

/** Eine Ban-Karte. Gleiche Bedienung, andere Farbe. */
function banKarte(ban, rang) {
  const karte = el('div', `vorschlag vorschlag--ban${rang === 0 ? ' vorschlag--top' : ''}`);
  const waehlen = el('button', 'vorschlag-waehlen');
  waehlen.type = 'button';
  waehlen.dataset.waehlen = ban.slug;
  waehlen.title = `${ban.name} bannen`;

  waehlen.appendChild(el('span', 'vorschlag-rang', rang + 1));
  waehlen.appendChild(bild(ban, 'vorschlag-bild', 40));

  const kern = el('span', 'vorschlag-kern');
  kern.appendChild(el('span', 'vorschlag-name', ban.name));
  kern.appendChild(el('span', 'vorschlag-rolle', (ban.rollen || [])[0] || ''));
  waehlen.appendChild(kern);

  waehlen.appendChild(el('span', 'vorschlag-score', ban.score));
  karte.appendChild(waehlen);

  // Die Ban-Gruende sind ganze Saetze des Servers - sie stehen nicht auf
  // der Karte, sondern hinter dem Fragezeichen.
  if ((ban.gruende || []).length) {
    const info = el('button', 'vorschlag-info', '?');
    info.type = 'button';
    info.dataset.bangruende = ban.slug;
    info.setAttribute('aria-label', `Warum ${ban.name} bannen?`);
    karte.appendChild(info);
  }
  return karte;
}

/** Ban-Begruendung im Detailfenster - die Daten liegen schon in der Antwort. */
export function zeigeBanGruende(ban) {
  const inhalt = $('modal-inhalt');
  inhalt.replaceChildren();
  inhalt.appendChild(detailKopf(ban, `${(ban.rollen || [])[0] || ''} · Ban-Score ${ban.score}/100`));
  inhalt.appendChild(el('h3', null, 'Warum bannen'));
  const liste = el('ul', 'liste');
  ban.gruende.forEach((g) => liste.appendChild(el('li', null, g)));
  inhalt.appendChild(liste);
  $('modal').hidden = false;
  $('modal-schliessen').focus();
}

/** Kopf des Detailfensters: Portrait, Name, Unterzeile. */
function detailKopf(e, unterzeile) {
  const kopf = el('div', 'modal-kopf');
  kopf.appendChild(bild(e, 'modal-bild', 64));
  const text = el('div');
  const titel = el('h2', null, e.name);
  titel.id = 'modal-titel';
  text.appendChild(titel);
  text.appendChild(el('p', 'modal-unterzeile', unterzeile));
  kopf.appendChild(text);
  return kopf;
}

export function zeichnePanel(antwort, ziel, ohneDaten) {
  const panel = $('panel');
  panel.replaceChildren();

  // Gepickte Brawler ohne Profil gehen nicht in die Bewertung ein - das
  // muss man sehen, sonst wirkt die Empfehlung, als kenne sie sie.
  if (ohneDaten && ohneDaten.length) {
    const zeile = el('div', 'panel-limited');
    zeile.appendChild(el('span', 'chip chip--limited', 'LD'));
    zeile.appendChild(el('span', null, `Ohne Profil, nur Messwerte: ${ohneDaten.join(', ')}`));
    panel.appendChild(zeile);
  }

  const banModus = ziel === 'ban';
  const zielText = ZIEL_TEXT[ziel] || 'Pick';

  if (banModus) {
    const bans = antwort.ban_empfehlungen || [];
    panel.appendChild(kopfzeile('Bannen', 'Klick = Ban'));
    if (bans.length) {
      const liste = el('div', 'vorschlaege');
      bans.forEach((ban, i) => liste.appendChild(banKarte(ban, i)));
      panel.appendChild(liste);
    } else {
      panel.appendChild(el('p', 'panel-leer',
        'Ban-Empfehlungen gibt es nur vor dem ersten Pick. Bannen geht weiter über das Gitter.'));
    }
  } else if (antwort.empfehlungen && antwort.empfehlungen.length) {
    panel.appendChild(kopfzeile(
      ziel === 'gegner' ? 'Stärkste Kandidaten' : 'Empfehlung',
      ziel === 'gegner' ? 'Klick = eintragen' : 'Klick = Pick',
    ));
    const liste = el('div', 'vorschlaege');
    antwort.empfehlungen.forEach((e, i) => {
      liste.appendChild(vorschlagsKarte(e, i, zielText));
    });
    panel.appendChild(liste);
  } else {
    panel.appendChild(el('p', 'panel-leer', 'Keine Kandidaten übrig.'));
  }

  if (antwort.team_analyse && !banModus) {
    const analyse = antwort.team_analyse;
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, `Uns fehlt · Deckung ${analyse.deckungsgrad}%`));
    const luecken = el('div', 'luecken');
    (analyse.luecken || []).slice(0, 4).forEach((l) => {
      const zeile = el('div', `luecke${l.kritisch ? ' ist-kritisch' : ''}`);
      zeile.appendChild(el('span', null, l.label));
      const balken = el('div', 'luecke-balken');
      const fuellung = el('div', 'luecke-fuellung');
      fuellung.style.width = `${Math.min(100, l.dringlichkeit)}%`;
      balken.appendChild(fuellung);
      zeile.appendChild(balken);
      zeile.appendChild(el('span', 'luecke-wert', `${l.dringlichkeit}`));
      luecken.appendChild(zeile);
    });
    if (!analyse.luecken || !analyse.luecken.length) {
      luecken.appendChild(el('p', 'panel-leer', 'Keine nennenswerte Lücke offen.'));
    }
    abschnitt.appendChild(luecken);
    panel.appendChild(abschnitt);
  }

  if (antwort.hinweise && antwort.hinweise.length) {
    const abschnitt = el('div', 'abschnitt');
    antwort.hinweise.forEach((h) => abschnitt.appendChild(el('p', 'panel-leer', h)));
    panel.appendChild(abschnitt);
  }
}

export function panelFehler(nachricht) {
  const panel = $('panel');
  panel.replaceChildren();
  panel.appendChild(el('p', 'panel-fehler', nachricht));
}

export function zeichneSiegchance(siegchance) {
  const kasten = $('siegchance');
  kasten.replaceChildren();
  if (!siegchance) return;
  kasten.appendChild(el('span', 'siegchance-label', 'Draft-Stärke'));
  kasten.appendChild(el('span', 'siegchance-wert', `${Math.round(siegchance.prozent)}%`));
  kasten.title = `Confidence: ${siegchance.confidence_label}`
    + (siegchance.ist_heuristik ? ' · heuristisch' : '');
}

// ─── Map-Waehler ────────────────────────────────────────────
/**
 * Maps als durchsuchbare Liste statt als Dropdown.
 *
 * Ein <select> mit allen Maps des Spiels ist im Draft unbenutzbar: man
 * kann nicht tippen, nicht filtern, und "die von letzter Woche" steht
 * irgendwo in der Mitte. Hier steht zuletzt Benutztes oben, darunter
 * alles nach Modus gruppiert, und das Suchfeld filtert ueber Map- UND
 * Modusname.
 */
export function zeichneMapListe(modi, suchtext, letzte, aktuellerSlug) {
  const liste = $('mapwaehler-liste');
  liste.replaceChildren();
  const suche = (suchtext || '').trim().toLowerCase();

  const zeile = (modus, karte) => {
    const knopf = el('button', 'mapzeile');
    knopf.type = 'button';
    knopf.dataset.mode = modus.slug;
    knopf.dataset.map = karte.slug;
    if (karte.slug === aktuellerSlug) knopf.classList.add('ist-aktuell');

    knopf.appendChild(bildKnoten(karte.image_url, modus.name.slice(0, 2).toUpperCase(),
      'var(--bg-3)', 'mapzeile-bild', 40));

    const text = el('span', 'mapzeile-text');
    text.appendChild(el('span', 'mapzeile-name', karte.name));
    text.appendChild(el('span', 'mapzeile-modus', modus.name));
    knopf.appendChild(text);
    if (karte.notiz) knopf.title = karte.notiz;
    return knopf;
  };

  const passt = (modus, karte) => !suche
    || karte.name.toLowerCase().includes(suche)
    || modus.name.toLowerCase().includes(suche);

  let treffer = 0;

  // 1. Zuletzt benutzt - nur ohne Suchtext. Wer tippt, sucht gezielt.
  if (!suche && letzte.length) {
    const gruppe = el('div', 'mapwaehler-gruppe');
    gruppe.appendChild(el('h3', null, 'Zuletzt benutzt'));
    letzte.forEach((eintrag) => {
      const modus = modi.find((m) => m.slug === eintrag.mode);
      const karte = modus && modus.maps.find((k) => k.slug === eintrag.map);
      if (!karte) return;
      gruppe.appendChild(zeile(modus, karte));
      treffer += 1;
    });
    if (treffer) liste.appendChild(gruppe);
  }

  // 2. Alles, nach Modus gruppiert.
  modi.forEach((modus) => {
    const karten = modus.maps.filter((k) => passt(modus, k));
    if (!karten.length) return;
    const gruppe = el('div', 'mapwaehler-gruppe');
    gruppe.appendChild(el('h3', null, modus.name));
    karten.forEach((k) => { gruppe.appendChild(zeile(modus, k)); treffer += 1; });
    liste.appendChild(gruppe);
  });

  if (!treffer) liste.appendChild(el('p', 'panel-leer', 'Keine Map passt.'));
  markiereMapzeile(0);
}

/**
 * Den Waehlerkasten unter seinen Knopf haengen.
 *
 * Die Position kommt aus dem Rechteck des Knopfes und nicht aus einer
 * festen Zahl im CSS: darueber liegen Kopfzeile, Demo-Hinweis und
 * Aktionsleiste, und jede davon aendert ihre Hoehe, sobald ihr Text
 * umbricht. Auf schmalen Fenstern steht der Kasten mittig - dort setzt
 * das Stylesheet `position: static` und diese Werte laufen ins Leere.
 */
export function mapWaehlerAusrichten(knopf) {
  const kasten = $('mapwaehler').querySelector('.mapwaehler-kasten');
  const r = knopf.getBoundingClientRect();
  kasten.style.top = `${Math.round(r.bottom + 6)}px`;
  kasten.style.left = `${Math.round(Math.min(r.left, window.innerWidth - kasten.offsetWidth - 12))}px`;
}

/** Tastaturmarkierung im Map-Waehler. Gibt die markierte Zeile zurueck. */
export function markiereMapzeile(schritt, relativ) {
  const zeilen = [...$('mapwaehler-liste').querySelectorAll('.mapzeile')];
  if (!zeilen.length) return null;
  let index = zeilen.findIndex((z) => z.classList.contains('ist-markiert'));
  if (index < 0) index = 0;
  const neu = relativ
    ? Math.max(0, Math.min(zeilen.length - 1, index + schritt))
    : Math.max(0, Math.min(zeilen.length - 1, schritt));
  zeilen.forEach((z) => z.classList.remove('ist-markiert'));
  zeilen[neu].classList.add('ist-markiert');
  zeilen[neu].scrollIntoView({ block: 'nearest' });
  return zeilen[neu];
}

// ─── Matchplan ──────────────────────────────────────────────
export function zeichneMatchplan(analyse) {
  const panel = $('panel');
  panel.replaceChildren();
  panel.appendChild(kopfzeile('Matchplan', 'Draft steht'));

  // 1. Datenlage zuerst. Wer die Einschätzung liest, soll vorher
  //    wissen, worauf sie sich stützt - nicht hinterher.
  if (analyse.datenlage) {
    const kasten = el('div', 'datenlage-kasten');
    kasten.appendChild(el('strong', null,
      `Data Confidence: ${analyse.datenlage.confidence_label} `
      + `(${analyse.datenlage.confidence})`));
    kasten.appendChild(el('p', null, analyse.datenlage.hinweis));
    panel.appendChild(kasten);
  }

  // 2. Win Condition - der eine Satz, wie dieses Team gewinnt.
  if (analyse.win_condition) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Win Condition'));
    abschnitt.appendChild(el('p', null, analyse.win_condition));
    panel.appendChild(abschnitt);
  }

  // 3. Die drei Spieler.
  const plan = el('div', 'matchplan');
  analyse.team.forEach((spieler) => {
    const kasten = el('div', 'matchplan-spieler');
    kasten.style.borderLeftColor = spieler.farbe;

    const kopf = el('div', 'matchplan-kopf');
    kopf.appendChild(el('span', 'matchplan-name', spieler.name));
    kopf.appendChild(el('span', 'matchplan-rolle', spieler.rolle));
    if (spieler.lane) {
      const lane = el('span', 'matchplan-lane', spieler.lane);
      if (spieler.lane_grund) lane.title = spieler.lane_grund;
      kopf.appendChild(lane);
    }
    kasten.appendChild(kopf);

    const zeile = (art, text, klasse) => {
      if (!text) return;
      const z = el('div', `matchplan-zeile ${klasse || ''}`);
      z.appendChild(el('span', 'matchplan-art', art));
      z.appendChild(el('span', null, text));
      kasten.appendChild(z);
    };

    zeile('Hauptaufgabe', spieler.hauptaufgabe);
    if (spieler.bevorzugtes_matchup) {
      zeile('Bevorzugt',
        `gegen ${spieler.bevorzugtes_matchup.gegner} `
        + `(${spieler.bevorzugtes_matchup.vorteil > 0 ? '+' : ''}${spieler.bevorzugtes_matchup.vorteil})`,
        'ist-gut');
    }
    if (spieler.zu_vermeidendes_matchup) {
      zeile('Vermeiden',
        `gegen ${spieler.zu_vermeidendes_matchup.gegner} `
        + `(${spieler.zu_vermeidendes_matchup.vorteil})`,
        'ist-schlecht');
    }

    // Weitere Aufgaben unterhalb der Hauptaufgabe - ohne sie zu doppeln.
    const weitere = (spieler.aufgaben || []).filter((a) => a !== spieler.hauptaufgabe);
    if (weitere.length) {
      const liste = el('ul', 'liste');
      weitere.forEach((a) => liste.appendChild(el('li', null, a)));
      kasten.appendChild(liste);
    }
    if ((spieler.vermeiden || []).length) {
      const liste = el('ul', 'liste liste--warnung');
      spieler.vermeiden.forEach((v) => liste.appendChild(el('li', null, v)));
      kasten.appendChild(liste);
    }
    if ((spieler.warnungen || []).length) {
      const klappe = document.createElement('details');
      klappe.className = 'klappe';
      const titel = document.createElement('summary');
      titel.textContent = `Worauf ${spieler.name} achten muss (${spieler.warnungen.length})`;
      klappe.appendChild(titel);
      const liste = el('ul', 'liste liste--warnung');
      spieler.warnungen.forEach((w) => liste.appendChild(el('li', null, w)));
      klappe.appendChild(liste);
      kasten.appendChild(klappe);
    }
    if (spieler.build) {
      const teile = [];
      if (spieler.build.gadget) teile.push(spieler.build.gadget.name);
      if (spieler.build.star_power) teile.push(spieler.build.star_power.name);
      if ((spieler.build.gears || []).length) teile.push(spieler.build.gears.join(', '));
      if (spieler.build.hypercharge) teile.push(spieler.build.hypercharge.name);
      if (teile.length) zeile('Build', teile.join(' · '));
      if (spieler.build.hinweis) {
        kasten.appendChild(el('p', 'panel-leer', spieler.build.hinweis));
      }
    }
    plan.appendChild(kasten);
  });
  panel.appendChild(plan);

  // 4. Matchup-Zuordnung als Teamübersicht.
  if (analyse.matchups && analyse.matchups.length) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Matchup-Zuordnung'));
    analyse.matchups.forEach((m) => {
      const zeile = el('div', 'matchplan-paar');
      zeile.appendChild(el('span', null, `${m.unser} → ${m.gegner}`));
      const wert = el('span', 'luecke-wert', m.vorteil > 0 ? `+${m.vorteil}` : `${m.vorteil}`);
      wert.style.color = m.vorteil > 0.05 ? 'var(--gut)'
        : m.vorteil < -0.05 ? 'var(--gegner)' : 'var(--text-leise)';
      zeile.appendChild(wert);
      abschnitt.appendChild(zeile);
    });
    panel.appendChild(abschnitt);
  }

  // 5. Was tun, wenn der Gegner die Zuordnung aufbricht.
  if (analyse.lane_tausch && analyse.lane_tausch.length) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Wenn der Gegner tauscht'));
    const liste = el('ul', 'liste');
    analyse.lane_tausch.forEach((p) => liste.appendChild(el('li', null, `${p.wenn} → ${p.dann}`)));
    abschnitt.appendChild(liste);
    panel.appendChild(abschnitt);
  }

  // 6. Teamschwächen - mit der Angabe, wer sie ausnutzen kann.
  if (analyse.schwaechen && analyse.schwaechen.length) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Schwächen unseres Teams'));
    analyse.schwaechen.forEach((sch) => {
      const zeile = el('div', `schwaeche${sch.ausgenutzt_von ? ' ist-ausnutzbar' : ''}`);
      zeile.appendChild(el('span', 'schwaeche-punkt'));
      zeile.appendChild(el('span', null, sch.text));
      abschnitt.appendChild(zeile);
    });
    panel.appendChild(abschnitt);
  }

  if (analyse.gefahren && analyse.gefahren.length) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Gefahren'));
    const liste = el('ul', 'liste liste--warnung');
    analyse.gefahren.forEach((g) => liste.appendChild(el('li', null, g)));
    abschnitt.appendChild(liste);
    panel.appendChild(abschnitt);
  }

  // 7. Startpositionen zuletzt - ausdrücklich ein Vorschlag.
  if (analyse.lanes && analyse.lanes.length) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Startpositionen (Vorschlag)'));
    analyse.lanes.forEach((l) => {
      const zeile = el('div', 'matchplan-paar');
      zeile.appendChild(el('span', null, l.lane));
      zeile.appendChild(el('span', 'luecke-wert', l.brawler));
      if (l.grund) zeile.title = l.grund;
      abschnitt.appendChild(zeile);
    });
    panel.appendChild(abschnitt);
  }
}

// Die fuenf Groessen einer Empfehlung nebeneinander. Bewusst schlicht und
// ohne eigenes Layout: das ist eine Debug-Ansicht, kein Umbau der Oberflaeche.
// Sie beantworten verschiedene Fragen und werden deshalb nie verrechnet.
// Der Objective Fit mischt Messung und Fachwissen. Beide Anteile muessen
// dastehen, sonst liest sich ein negativer Gesamtwert neben einer positiv
// gemessenen Differenz wie ein Widerspruch.
function objectiveHinweis(o) {
  if (!o) return 'keine Auskunft zum Modusziel';
  const teile = [];
  if (o.differenz_pp !== null) {
    const vz = o.differenz_pp > 0 ? '+' : '';
    teile.push(`Messung ${vz}${o.differenz_pp} pp gegenüber seinem eigenen Schnitt `
      + `(${o.modus_spiele} Partien, ${Math.round(o.mess_anteil * 100)} %)`);
    if (o.map_spiele) {
      const mvz = o.map_diff_pp > 0 ? '+' : '';
      teile.push(`auf dieser Map ${mvz}${o.map_diff_pp} pp (${o.map_spiele} Partien)`);
    }
  }
  if (o.qualitativ !== null && o.mess_anteil < 1) {
    const qvz = o.qualitativ > 0 ? '+' : '';
    teile.push(`Fachwissen ${qvz}${o.qualitativ.toFixed(2)}`
      + (o.aspekt ? ` (${o.aspekt})` : '')
      + ` · ${Math.round((1 - o.mess_anteil) * 100)} %`);
  }
  return teile.join(' · ') || o.text;
}

function erklaerungsTafel(x) {
  const abschnitt = el('div', 'erklaerung');
  abschnitt.appendChild(el('h3', null, 'Die fünf Größen'));
  const punkte = (w) => `${w > 0 ? '+' : ''}${w.toFixed(1)}`;
  const cs = x.current_strength;
  const sc = x.statistical_confidence;
  const zeilen = [
    ['Current Strength', punkte(cs.punkte),
      cs.empirisch
        ? `${(cs.rate * 100).toFixed(1)} % aus ${cs.spiele} Partien `
          + `(effektiv ${cs.n_effektiv}) · ${cs.quelle}`
        : `${cs.hinweis}${cs.rate === null ? '' : ` (gepflegter Wert ${(cs.rate * 100).toFixed(1)} %)`}`],
    ['Objective Fit', x.objective_fit ? punkte(x.objective_fit.punkte) : '–',
      objectiveHinweis(x.objective_fit)],
    ['Draft Fit', punkte(x.draft_fit.punkte),
      x.draft_fit.komponenten.map((k) => `${k.label} ${punkte(k.punkte)}`).join(' · ')
        || 'keine Komponente berechenbar'],
    ['Personal', punkte(x.personal.punkte),
      x.personal.gepflegt ? 'eigene Sicherheit gepflegt' : 'nicht gepflegt'],
    ['Data Coverage', `${x.data_coverage.prozent} %`,
      x.data_coverage.label
        + (x.data_coverage.ausgelassen.length
          ? ` · ohne ${x.data_coverage.ausgelassen.join(', ')}` : '')],
    ['Statistical Confidence', sc.gesamt.toFixed(2),
      `${sc.label} · Messung ${sc.messung.toFixed(2)}`
        + (sc.intervall
          ? ` · ${(sc.intervall[0] * 100).toFixed(1)}–${(sc.intervall[1] * 100).toFixed(1)} %`
          : '')],
  ];
  zeilen.forEach(([name, wert, hinweis]) => {
    const zeile = el('div', 'erklaerung-zeile');
    zeile.appendChild(el('span', 'erklaerung-name', name));
    zeile.appendChild(el('span', 'erklaerung-wert', wert));
    zeile.appendChild(el('span', 'erklaerung-hinweis', hinweis));
    abschnitt.appendChild(zeile);
  });
  return abschnitt;
}

// ─── Modal ──────────────────────────────────────────────────
export function zeigeDetail(e) {
  const inhalt = $('modal-inhalt');
  inhalt.replaceChildren();

  // Der Rang steht vorn: bei einem Brawler, den niemand vorschlaegt, ist
  // er die erste Frage ("wo steht er ueberhaupt?").
  const rangtext = e.rang ? `Rang ${e.rang} von ${e.kandidaten} · ` : '';
  inhalt.appendChild(detailKopf(e,
    `${rangtext}${e.rolle} · Score ${e.score}/100 · ~${e.win_probability}% Siegchance · `
    + `Confidence: ${e.confidence_label} · `
    + `Datenabdeckung ${e.datenabdeckung} % · ${e.datenabdeckung_label}`));

  if (e.erklaerung) inhalt.appendChild(erklaerungsTafel(e.erklaerung));

  // Mit welchen Zahlen gerechnet wurde. Faellt das bevorzugte Fenster
  // ("seit Patch") aus, steht das hier - sonst gingen 7-Tage-Werte
  // stillschweigend als Patchstand durch.
  const fl = e.statistikfenster;
  if (fl && fl.hauptfenster) {
    const zeile = el('p', 'fensterlage');
    const namen = { seit_patch: 'seit Patch', '7d': '7 Tage', '30d': '30 Tage', '90d': '90 Tage' };
    zeile.appendChild(el('strong', null, `Fenster: ${namen[fl.hauptfenster] || fl.hauptfenster}`));
    if (fl.grund) zeile.appendChild(el('span', null, ` — ${fl.grund}`));
    inhalt.appendChild(zeile);
  }

  if (e.pro.length || e.contra.length) {
    inhalt.appendChild(el('h3', null, 'Warum dieser Pick'));
    inhalt.appendChild(gruendeListe(e.pro, e.contra));
  }

  if (e.komponenten) {
    inhalt.appendChild(el('h3', null, 'Woraus der Score entsteht'));
    inhalt.appendChild(aufschluesselung(e.komponenten));
    inhalt.appendChild(el('p', 'komponenten-fuss',
      `Beitrag = Wert × Gewicht. Summe ${(e.score - 50) > 0 ? '+' : ''}`
      + `${e.score - 50} auf den Anker 50 ergibt Score ${e.score}.`));
  }

  const m = e.matchups;
  if (m && (m.counter.length || m.synergie.length)) {
    // Die Komponente mittelt diese Werte - hier stehen sie einzeln.
    // Ohne sie sieht man "Counter -0,1" und weiss nicht, ob das drei
    // laue Matchups sind oder zwei gute und ein katastrophales.
    if (m.counter.length) {
      inhalt.appendChild(el('h3', null, 'Counter gegen jeden Gegner'));
      inhalt.appendChild(paartabelle(m.counter));
    }
    if (m.synergie.length) {
      inhalt.appendChild(el('h3', null, 'Synergie mit jedem Mitspieler'));
      inhalt.appendChild(paartabelle(m.synergie));
    }
  }

  if (e.bevorzugtes_matchup || e.zu_vermeidendes_matchup) {
    inhalt.appendChild(el('h3', null, 'Matchups'));
    const kasten = el('div', 'build');
    if (e.bevorzugtes_matchup) {
      const z = el('div', 'build-zeile');
      z.appendChild(el('span', 'build-art', 'Bevorzugt'));
      z.appendChild(el('span', null,
        `gegen ${e.bevorzugtes_matchup.gegner} (${e.bevorzugtes_matchup.vorteil > 0 ? '+' : ''}${e.bevorzugtes_matchup.vorteil})`));
      kasten.appendChild(z);
    }
    if (e.zu_vermeidendes_matchup) {
      const z = el('div', 'build-zeile');
      z.appendChild(el('span', 'build-art', 'Vermeiden'));
      z.appendChild(el('span', null,
        `gegen ${e.zu_vermeidendes_matchup.gegner} (${e.zu_vermeidendes_matchup.vorteil})`));
      kasten.appendChild(z);
    }
    inhalt.appendChild(kasten);
  }

  if (e.aufgaben && e.aufgaben.length) {
    inhalt.appendChild(el('h3', null, 'Deine Aufgabe'));
    const liste = el('ul', 'liste');
    e.aufgaben.forEach((a) => liste.appendChild(el('li', null, a)));
    inhalt.appendChild(liste);
  }
  if (e.vermeiden && e.vermeiden.length) {
    inhalt.appendChild(el('h3', null, 'Nicht deine Aufgabe'));
    const liste = el('ul', 'liste');
    e.vermeiden.forEach((v) => liste.appendChild(el('li', null, v)));
    inhalt.appendChild(liste);
  }
  if (e.warnungen && e.warnungen.length) {
    inhalt.appendChild(el('h3', null, 'Worauf du achten musst'));
    const liste = el('ul', 'liste liste--warnung');
    e.warnungen.forEach((w) => liste.appendChild(el('li', null, w)));
    inhalt.appendChild(liste);
  }

  if (e.build) {
    inhalt.appendChild(el('h3', null, 'Empfohlener Build'));
    const kasten = el('div', 'build');
    const zeile = (art, wert) => {
      if (!wert) return;
      const z = el('div', 'build-zeile');
      z.appendChild(el('span', 'build-art', art));
      z.appendChild(el('span', null, wert));
      kasten.appendChild(z);
    };
    zeile('Gadget', e.build.gadget && e.build.gadget.name
      + (e.build.gadget.alternative ? ` (sonst: ${e.build.gadget.alternative})` : ''));
    zeile('Star Power', e.build.star_power && e.build.star_power.name);
    zeile('Gears', (e.build.gears || []).join(' + '));
    zeile('Hypercharge', e.build.hypercharge && e.build.hypercharge.name);
    inhalt.appendChild(kasten);
    if (e.build.gruende && e.build.gruende.length) {
      const liste = el('ul', 'liste');
      e.build.gruende.forEach((g) => liste.appendChild(el('li', null, g)));
      inhalt.appendChild(liste);
    }
    if (e.build.hinweis) {
      inhalt.appendChild(el('p', 'panel-leer', e.build.hinweis));
    }
  }

  $('modal').hidden = false;
  $('modal-schliessen').focus();
}

export function schliesseModal() {
  $('modal').hidden = true;
}

export function modalOffen() {
  return !$('modal').hidden;
}
