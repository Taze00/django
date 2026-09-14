/**
 * Zeichnen: Slots, Gitter, Panel, Modal.
 *
 * Alles hier ist reine Darstellung - kein Zustand, keine Netzanfragen.
 * Jede Funktion bekommt Daten und schreibt DOM. Dadurch bleibt
 * nachvollziehbar, wo etwas herkommt, wenn die Anzeige falsch aussieht:
 * entweder liefert der Server es falsch, oder hier wird es falsch
 * hingeschrieben - nie beides vermischt.
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

/** Portrait oder eingefaerbter Platzhalter mit Kuerzel. */
function bild(brawler, klasse) {
  const knoten = el('div', klasse);
  if (brawler.image_url) {
    knoten.style.backgroundImage = `url("${brawler.image_url.replace(/["\\]/g, '')}")`;
  } else {
    knoten.style.background = brawler.farbe || '#3a3f4b';
    knoten.appendChild(t(brawler.initialen || brawler.name.slice(0, 2).toUpperCase()));
  }
  return knoten;
}

// ─── Slots ──────────────────────────────────────────────────
export function zeichneSlots(containerId, slugs, anzahl, katalog, ziel, aktiv, klasse) {
  const container = $(containerId);
  container.replaceChildren();

  for (let i = 0; i < anzahl; i += 1) {
    const slug = slugs[i];
    const slot = el('div', `slot ${klasse || ''}`);
    if (slug) {
      const b = katalog.get(slug);
      slot.classList.add('ist-belegt');
      slot.style.borderColor = b.farbe;
      slot.appendChild(bild(b, 'slot-bild'));
      const kuerzel = slot.querySelector('.slot-bild');
      if (!b.image_url) kuerzel.classList.add('slot-kuerzel');
      slot.appendChild(el('span', 'slot-name', b.name));
      slot.title = `${b.name} entfernen`;
      slot.dataset.entfernen = slug;
    } else {
      const istZiel = aktiv && i === slugs.length;
      if (istZiel) slot.classList.add('ist-ziel');
      slot.appendChild(el('span', null, istZiel ? 'wählen' : '—'));
      slot.dataset.ziel = ziel;
    }
    container.appendChild(slot);
  }
}

// ─── Brawler-Gitter ─────────────────────────────────────────
export function zeichneGitter(brawler, gesperrt, bewertungen, persoenlich, filter) {
  const gitter = $('gitter');
  gitter.replaceChildren();

  const suche = (filter.suche || '').trim().toLowerCase();
  const rolle = filter.rolle;

  brawler
    .filter((b) => !suche || b.name.toLowerCase().includes(suche))
    .filter((b) => !rolle || b.tags.includes(rolle))
    .forEach((b) => {
      const karte = el('button', 'karte');
      karte.type = 'button';
      karte.dataset.slug = b.slug;

      if (gesperrt.has(b.slug)) {
        karte.classList.add('ist-gesperrt');
        karte.disabled = true;
      }

      const bewertung = bewertungen.get(b.slug);
      if (bewertung) {
        if (bewertung.rang < 3) karte.classList.add('ist-empfohlen');
        const score = el('span', 'karte-score', bewertung.score);
        if (bewertung.score >= 60) score.classList.add('ist-gut');
        else if (bewertung.score < 45) score.classList.add('ist-schwach');
        karte.appendChild(score);
      }

      if (persoenlich[b.slug] != null) {
        const punkt = el('span', 'karte-confidence');
        punkt.title = `Deine Sicherheit: ${persoenlich[b.slug]}/100`;
        punkt.style.opacity = String(0.25 + (persoenlich[b.slug] / 100) * 0.75);
        karte.appendChild(punkt);
      }

      karte.appendChild(bild(b, 'karte-bild'));
      karte.appendChild(el('span', 'karte-name', b.name));
      karte.appendChild(el('span', 'karte-rollen', b.rollen.slice(0, 2).join(' · ')));
      gitter.appendChild(karte);
    });

  if (!gitter.children.length) {
    gitter.appendChild(el('p', 'panel-leer', 'Kein Brawler passt zu diesem Filter.'));
  }
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

// ─── Empfehlungspanel ───────────────────────────────────────
export function zeichnePanel(antwort) {
  const panel = $('panel');
  panel.replaceChildren();

  if (antwort.ban_empfehlungen && antwort.ban_empfehlungen.length) {
    panel.appendChild(el('h2', null, 'Ban-Empfehlungen'));
    const kasten = el('div', 'bankarten');
    antwort.ban_empfehlungen.forEach((ban) => {
      const karte = el('button', 'bankarte');
      karte.type = 'button';
      karte.dataset.slug = ban.slug;
      karte.appendChild(bild(ban, 'vorschlag-bild'));
      const text = el('div', 'bankarte-text');
      text.appendChild(el('div', 'bankarte-name', `${ban.name} · ${ban.score}`));
      ban.gruende.forEach((g) => text.appendChild(el('div', 'bankarte-grund', g)));
      karte.appendChild(text);
      kasten.appendChild(karte);
    });
    panel.appendChild(kasten);
  }

  if (antwort.empfehlungen && antwort.empfehlungen.length) {
    panel.appendChild(el('h2', null, 'Empfehlungen'));
    antwort.empfehlungen.forEach((e, i) => {
      const karte = el('button', `vorschlag${i === 0 ? ' vorschlag--top' : ''}`);
      karte.type = 'button';
      karte.dataset.detail = e.slug;

      const kopf = el('div', 'vorschlag-kopf');
      kopf.appendChild(bild(e, 'vorschlag-bild'));
      const namen = el('div');
      namen.appendChild(el('div', 'vorschlag-name', e.name));
      namen.appendChild(el('div', 'vorschlag-rolle', e.rolle));
      kopf.appendChild(namen);
      const score = el('div', 'vorschlag-score', e.score);
      score.appendChild(el('div', 'vorschlag-wp', `~${e.win_probability}% Sieg`));
      kopf.appendChild(score);
      karte.appendChild(kopf);
      karte.appendChild(gruendeListe(e.pro, e.contra));
      panel.appendChild(karte);
    });
  }

  if (antwort.team_analyse) {
    const analyse = antwort.team_analyse;
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null,
      `Was unserem Team fehlt · Deckung ${analyse.deckungsgrad}%`));
    const luecken = el('div', 'luecken');
    (analyse.luecken || []).forEach((l) => {
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
    abschnitt.appendChild(el('h3', null, 'Hinweis'));
    antwort.hinweise.forEach((h) => abschnitt.appendChild(el('p', 'panel-leer', h)));
    panel.appendChild(abschnitt);
  }
}

export function zeichneSiegchance(siegchance) {
  const kasten = $('siegchance');
  kasten.replaceChildren();
  if (!siegchance) return;
  kasten.appendChild(el('div', 'siegchance-label', 'Geschätzte Draft-Stärke'));
  kasten.appendChild(el('div', 'siegchance-wert', `${Math.round(siegchance.prozent)}%`));
  kasten.appendChild(el('div', 'siegchance-fuss',
    `Confidence: ${siegchance.confidence_label}${siegchance.ist_heuristik ? ' · heuristisch' : ''}`));
}

// ─── Matchplan ──────────────────────────────────────────────
export function zeichneMatchplan(analyse) {
  const panel = $('panel');
  panel.replaceChildren();
  panel.appendChild(el('h2', null, 'Matchplan'));

  if (analyse.win_condition) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Win Condition'));
    abschnitt.appendChild(el('p', null, analyse.win_condition));
    panel.appendChild(abschnitt);
  }

  const plan = el('div', 'matchplan');
  analyse.team.forEach((spieler) => {
    const kasten = el('div', 'matchplan-spieler');
    kasten.style.borderLeftColor = spieler.farbe;
    const kopf = el('div', 'matchplan-kopf');
    kopf.appendChild(el('span', 'matchplan-name', spieler.name));
    kopf.appendChild(el('span', 'matchplan-rolle', spieler.rolle));
    kasten.appendChild(kopf);

    // Das bevorzugte Matchup steht oft schon als erste Aufgabe. Zweimal
    // derselbe Satz untereinander liest sich wie ein Fehler - also nur
    // anzeigen, wenn die Aufgabenliste ihn nicht ohnehin nennt.
    const gegnerName = spieler.bevorzugtes_matchup && spieler.bevorzugtes_matchup.gegner;
    const schonGenannt = gegnerName
      && spieler.aufgaben.some((a) => a.includes(gegnerName) && a.startsWith('Nimm dir'));
    if (gegnerName && !schonGenannt) {
      kasten.appendChild(el('div', 'bankarte-grund', `Nimm dir ${gegnerName} vor`));
    }
    const liste = el('ul', 'liste');
    spieler.aufgaben.forEach((a) => liste.appendChild(el('li', null, a)));
    kasten.appendChild(liste);

    if (spieler.vermeiden.length) {
      const warn = el('ul', 'liste liste--warnung');
      spieler.vermeiden.forEach((v) => warn.appendChild(el('li', null, v)));
      kasten.appendChild(warn);
    }
    if (spieler.build && spieler.build.gadget) {
      const teile = [spieler.build.gadget.name];
      if (spieler.build.star_power) teile.push(spieler.build.star_power.name);
      if ((spieler.build.gears || []).length) teile.push(spieler.build.gears.join(', '));
      kasten.appendChild(el('div', 'bankarte-grund', `Build: ${teile.join(' · ')}`));
    }
    plan.appendChild(kasten);
  });
  panel.appendChild(plan);

  if (analyse.matchups && analyse.matchups.length) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Matchup-Zuordnung'));
    analyse.matchups.forEach((m) => {
      const zeile = el('div', 'matchplan-paar');
      zeile.appendChild(el('span', null, `${m.unser} → ${m.gegner}`));
      zeile.appendChild(el('span', 'luecke-wert', m.vorteil > 0 ? `+${m.vorteil}` : `${m.vorteil}`));
      abschnitt.appendChild(zeile);
    });
    panel.appendChild(abschnitt);
  }

  if (analyse.lane_tausch && analyse.lane_tausch.length) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Wenn der Gegner tauscht'));
    const liste = el('ul', 'liste');
    analyse.lane_tausch.forEach((p) => liste.appendChild(el('li', null, `${p.wenn} → ${p.dann}`)));
    abschnitt.appendChild(liste);
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

  if (analyse.lanes && analyse.lanes.length) {
    const abschnitt = el('div', 'abschnitt');
    abschnitt.appendChild(el('h3', null, 'Startpositionen (Vorschlag)'));
    analyse.lanes.forEach((l) => {
      const zeile = el('div', 'matchplan-paar');
      zeile.appendChild(el('span', null, l.lane));
      zeile.appendChild(el('span', null, l.brawler));
      abschnitt.appendChild(zeile);
    });
    panel.appendChild(abschnitt);
  }
}

// ─── Modal ──────────────────────────────────────────────────
export function zeigeDetail(e) {
  const inhalt = $('modal-inhalt');
  inhalt.replaceChildren();

  const titel = el('h2', null, e.name);
  titel.id = 'modal-titel';
  inhalt.appendChild(titel);
  inhalt.appendChild(el('p', 'vorschlag-rolle',
    `${e.rolle} · Score ${e.score}/100 · ~${e.win_probability}% Siegchance · `
    + `Confidence: ${e.confidence_label}`));

  if (e.pro.length || e.contra.length) {
    inhalt.appendChild(el('h3', null, 'Warum dieser Pick'));
    inhalt.appendChild(gruendeListe(e.pro, e.contra));
  }

  if (e.komponenten) {
    inhalt.appendChild(el('h3', null, 'Woraus der Score entsteht'));
    const kasten = el('div', 'komponenten');
    const groesster = Math.max(...e.komponenten.map((k) => Math.abs(k.beitrag)), 1);
    e.komponenten.forEach((k) => {
      const zeile = el('div', 'komponente');
      zeile.appendChild(el('span', 'komponente-label', k.label));
      const balken = el('div', 'komponente-balken');
      const fuellung = el('div', `komponente-fuellung ${k.beitrag >= 0 ? 'ist-plus' : 'ist-minus'}`);
      fuellung.style.width = `${(Math.abs(k.beitrag) / groesster) * 50}%`;
      balken.appendChild(fuellung);
      zeile.appendChild(balken);
      zeile.appendChild(el('span', 'komponente-wert',
        `${k.beitrag > 0 ? '+' : ''}${k.beitrag.toFixed(1)}`));
      kasten.appendChild(zeile);
    });
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
}

export function schliesseModal() {
  $('modal').hidden = true;
}
