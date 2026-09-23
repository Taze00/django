/* Standalone opt-in surface; textContent keeps source/model facts out of HTML. */
(() => {
  const form = document.getElementById('challenger-form');
  const status = document.getElementById('challenger-status');
  const results = document.getElementById('challenger-results');
  const submit = document.getElementById('challenger-submit');
  const maps = document.getElementById('challenger-map');
  const bans = document.getElementById('challenger-bans');
  const element = (tag, text) => { const node = document.createElement(tag); node.textContent = text; return node; };
  const snapshots = document.getElementById('challenger-snapshots');
  const post = async (url, body) => {
    const response = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value}, body: JSON.stringify(body)});
    const data = await response.json(); if (!response.ok) throw Error(data.fehler || 'Speichern fehlgeschlagen'); return data;
  };
  const loadSnapshots = async () => {
    if (!snapshots) return;
    try {
      const response = await fetch(form.dataset.snapshots);
      if (!response.ok) throw Error('Gespeicherte Drafts nicht verfügbar');
      const data = await response.json(); snapshots.replaceChildren();
      for (const saved of data.snapshots) {
        const row = element('div', `#${saved.id} · ${saved.chosen || "Pick unbekannt"} · ${saved.model_version} · ${saved.at} `);
        const select = document.createElement('select'); select.setAttribute('aria-label', `Ergebnis für Draft ${saved.id}`);
        for (const [value, label] of [['unknown', 'Ergebnis unbekannt'], ['win', 'Sieg'], ['loss', 'Niederlage']]) select.add(new Option(label, value));
        select.value = saved.result;
        select.addEventListener('change', async () => {
          select.disabled = true;
          try { await post(`${form.dataset.snapshots}${saved.id}/result/`, {result: select.value}); status.textContent = `Ergebnis für #${saved.id} gespeichert (eigene Angabe).`; }
          catch (error) { status.textContent = error.message; }
          finally { select.disabled = false; }
        });
        row.append(select);
        const inspect = element('button', 'Snapshot ansehen'); inspect.type = 'button';
        inspect.addEventListener('click', async () => {
          inspect.disabled = true;
          try {
            const response = await fetch(`${form.dataset.snapshots}${saved.id}/result/`);
            const detail = await response.json(); if (!response.ok) throw Error(detail.fehler);
            const content = document.createElement('details'); content.open = true;
            content.append(element('summary', `Archivierter Modellstand ${detail.snapshot.artifact_sha256}`));
            content.append(element('p', `Eigene Picks: ${detail.draft.own.join(', ')} · Gegner: ${detail.draft.enemy.join(', ')} · Bans: ${detail.draft.bans.join(', ')}`));
            const list = document.createElement('ol');
            for (const item of detail.snapshot.recommendations) list.append(element('li', `${item.name}: ${(item.p_win * 100).toFixed(1)} % Modellschätzung`));
            content.append(list);
            const evidence = document.createElement('pre'); evidence.textContent = JSON.stringify({legacy: detail.snapshot.legacy, metadata: detail.metadata}, null, 2); content.append(evidence);
            const chosen = document.createElement('select'); chosen.setAttribute('aria-label', 'Tatsächlich gewählter Pick'); chosen.add(new Option('Pick angeben', ''));
            for (const slug of detail.snapshot.legacy?.receipt.candidate_pool || detail.snapshot.recommendations.map(r => r.slug)) chosen.add(new Option(slug, slug));
            const report = element('button', 'Pick melden'); report.type = 'button';
            report.addEventListener('click', async () => { try { await post(`${form.dataset.snapshots}${saved.id}/result/`, {chosen: chosen.value}); await loadSnapshots(); } catch (error) { status.textContent = error.message; } });
            content.append(chosen, report); row.append(content);
          } catch (error) { status.textContent = error.message; inspect.disabled = false; }
        });
        row.append(inspect); snapshots.append(row);
      }
    } catch (error) { snapshots.textContent = error.message; }
  };
  loadSnapshots();
  let requestVersion = 0;
  form.addEventListener('change', () => { requestVersion++; results.replaceChildren(); status.textContent = 'Draft geändert. Neu berechnen.'; });
  Promise.all([form.dataset.catalog, form.dataset.info].map(async url => {
    const response = await fetch(url); const data = await response.json();
    if (!response.ok) throw Error(data.fehler || 'Katalog nicht verfügbar'); return data;
  })).then(([data, info]) => {
    for (const mode of data.modi) for (const map of mode.maps) if (info.supported_maps.includes(map.slug)) maps.add(new Option(`${mode.name} · ${map.name}`, map.slug));
    const available = data.brawler.filter(b => b.ranked_verfuegbar);
    for (const [side, count] of [['own', 3], ['enemy', 3]]) {
      for (let i = 0; i < count; i++) {
        const label = element('label', `Pick ${i + 1} `);
        const select = document.createElement('select'); select.dataset.side = side;
        select.add(new Option('Noch offen', ''));
        for (const b of available) select.add(new Option(b.name, b.slug));
        label.append(select); document.getElementById(`challenger-${side}`).append(label);
      }
    }
    for (const b of available) bans.add(new Option(b.name, b.slug));
    submit.disabled = maps.options.length === 0; status.textContent = maps.options.length ? 'Wähle Map, Draftzustand und First-Pick-Seite. Angezeigt werden Maps mit bekanntem Modellkontext.' : 'Keine aktuell wählbare Map hat einen bekannten Modellkontext.';
  }).catch(error => { status.textContent = error.message; });
  form.addEventListener('submit', async event => {
    event.preventDefault(); const version = ++requestVersion;
    submit.disabled = true; results.replaceChildren(); status.textContent = 'Berechne …';
    const picks = side => [...form.querySelectorAll(`[data-side="${side}"]`)].map(s => s.value).filter(Boolean);
    try {
      const response = await fetch(form.dataset.endpoint, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value},
        body: JSON.stringify({map: maps.value, own_picks: picks('own'), enemy_picks: picks('enemy'), bans: [...bans.selectedOptions].map(o => o.value), own_team_first_pick: document.getElementById('challenger-first').checked, compare_legacy: document.getElementById('challenger-compare').checked, shadow_capture: document.getElementById('challenger-shadow')?.checked || false})});
      const data = await response.json(); if (!response.ok) throw Error(data.fehler || 'Anfrage fehlgeschlagen');
      if (version !== requestVersion) return;
      status.textContent = `${data.model_version} · ${data.recommendations.length} Kandidaten · ${data.elapsed_ms} ms · experimentell`;
      results.append(element('p', `Modellstand ${data.artifact_sha256}. Training: ${data.provenance.train.n} Matches bis ${data.provenance.train.last}.`));
      results.append(element('p', data.search.approximate ? `Begrenzte Minimax-Suche: ${data.search.evaluated_leaves} vollständige Kompositionen. Folgepicks aus einer Shortlist nach Trainingshäufigkeit; stärkere Antworten außerhalb bleiben möglich.` : 'Alle unterstützten legalen Kandidaten; vollständige Kompositionen.'));
      if (data.legacy) {
        results.append(element('h2', 'Experimenteller Vergleich'));
        results.append(element('p', 'V2: Modellschätzung. Legacy: heuristischer Score, keine Wahrscheinlichkeit. Gleicher Draft; Rangunterschiede belegen keine bessere Qualität.'));
        const receipt = data.legacy.receipt, state = receipt.draft_state;
        results.append(element('p', `Legacy-Kontext auf ${window.location.origin}: ${state.mode} / ${state.map}; eigene Picks ${state.own_picks.join(', ')}; Gegner ${state.enemy_picks.join(', ')}; Bans ${state.bans.join(', ') || 'keine'}; First Pick ${state.own_team_first_pick ? 'wir' : 'Gegner'}; Pick ${state.pick_nummer}, Phase ${state.phase}, am Zug ${state.am_zug}; Rangpool ${state.rank_pool}; Provider ${receipt.provider}; ${receipt.candidate_pool.length} bewertbare Kandidaten; ${receipt.personal_preferences_count} persönliche Einstellungen.`));
        results.append(element('p', 'Der Vergleich gilt für diese Instanz und Sitzung. Eine andere Datenbank, persönliche Einstellungen oder die Sortierung des Brawler-Gitters können abweichen. Verglichen wird die normale Legacy-Empfehlungsliste.'));
        const receiptDetails = document.createElement('details');
        receiptDetails.append(element('summary', 'Vergleichseingaben und Datenbeleg'));
        receiptDetails.append(element('pre', JSON.stringify(receipt, null, 2))); results.append(receiptDetails);
        const verify = element('button', 'Normalen Legacy-Endpunkt mit diesem Zustand prüfen'); verify.type = 'button';
        verify.addEventListener('click', async () => {
          verify.disabled = true;
          try {
            const normal = await post(form.dataset.legacy, state);
            const ranks = entries => entries.map(e => [e.slug, e.score, e.score_roh]);
            const identical = JSON.stringify(ranks(normal.empfehlungen)) === JSON.stringify(ranks(data.legacy.recommendations));
            verify.textContent = identical ? 'Identische Legacy-Rangfolge bestätigt' : 'Abweichung: Sitzung/Daten/Zustand erneut prüfen';
          } catch (error) { verify.textContent = error.message; }
          finally { verify.disabled = false; }
        });
        results.append(verify);
        const table = document.createElement('table');
        const head = document.createElement('tr');
        for (const label of ['Rang', 'V2 · Modellschätzung', 'Legacy · Score']) head.append(element('th', label));
        table.append(head);
        for (let i = 0; i < Math.min(10, Math.max(data.recommendations.length, data.legacy.recommendations.length)); i++) {
          const v2 = data.recommendations[i], legacy = data.legacy.recommendations[i];
          const row = document.createElement('tr'); row.append(element('td', i + 1));
          row.append(element('td', v2 ? `${v2.name} · ${(v2.p_win * 100).toFixed(1)} %` : 'Keine Empfehlung'));
          row.append(element('td', legacy ? `${legacy.name} · ${legacy.score}` : 'Außerhalb der Legacy-Topliste'));
          table.append(row);
        }
        results.append(table);
      }
      if (data.snapshot_id) { results.append(element('p', `Shadow-Snapshot #${data.snapshot_id} gespeichert; Pick und Ergebnis noch unbekannt.`)); await loadSnapshots(); }
      for (const item of data.recommendations) {
        const details = document.createElement('details');
        details.append(element('summary', `${item.name} · Modellschätzung ${(item.p_win * 100).toFixed(1)} %`));
        details.append(element('p', `Unsicherheit: UNKNOWN. Unbekannte Features: ${item.evidence.unknown_features.length}. Beiträge sind gelernte Zusammenhänge, keine kausalen Effekte.`));
        if (item.continuation.length) details.append(element('p', `Hypothetische Fortsetzung: ${item.continuation.map(p => `${p.side === 'own' ? 'Wir' : 'Gegner'}: ${p.slug}`).join(' → ')}. Beiträge beziehen sich auf diese vollständige Komposition.`));
        const diagnostic = item.diagnostic, comparison = diagnostic.comparison;
        details.append(element('p', diagnostic.ranking_limit));
        details.append(element('p', 'Evidenz für genau diese Sechser-Komposition: UNKNOWN. Trainingszahlen gelten für einzelne Features; sie sind keine Konfidenzintervalle. Mechanik-, Terrain- und Rollenmerkmale sind nicht aktiv; Übertragbarkeit auf den aktuellen Patch: UNKNOWN.'));
        if (comparison) details.append(element('p', `Gegenüber ${comparison.reference_name}: ${comparison.probability_difference_pp >= 0 ? '+' : ''}${comparison.probability_difference_pp.toFixed(2)} Prozentpunkte Modellschätzung. Sicherheit dieses Abstandes: UNKNOWN.`));
        details.append(element('p', 'Die folgenden Logit-Beiträge sind additive Modellwerte, keine Prozentpunkte. Positive Unterschiede sprechen im Modell für diesen Pick; einzelne Terme sind nicht separat als taktischer Nutzen validiert.'));
        const breakdown = document.createElement('table');
        const headings = document.createElement('tr');
        for (const title of ['Anteil', 'Dieser Pick', comparison ? `Differenz zu ${comparison.reference_name}` : 'Differenz', 'Evidenz']) headings.append(element('th', title));
        breakdown.append(headings);
        for (const [family, group] of Object.entries(diagnostic.families)) {
          const row = document.createElement('tr');
          row.append(element('td', group.label));
          row.append(element('td', group.active ? group.modeled_logit.toFixed(4) : 'Nicht aktiv'));
          const delta = comparison?.candidate_family_logit_differences[family];
          row.append(element('td', delta == null ? '—' : `${delta >= 0 ? '+' : ''}${delta.toFixed(4)}`));
          row.append(element('td', group.active ? `${group.status}; ${group.unknown_terms} unbelegte Terme` : 'Keine entsprechende Modellfunktion'));
          breakdown.append(row);
        }
        details.append(breakdown);
        details.append(element('p', diagnostic.search.active ? 'Search: hypothetische Fortsetzung aktiv; gemeinsame Hintergrundterme können deshalb zwischen Kandidaten abweichen. Kein zusätzlicher Search-Bonus.' : `Search: Last Pick, keine Folgezüge. Gemeinsamer fester Draftbeitrag: ${diagnostic.background_logit.toFixed(4)} Logit; erklärt nicht den Rangunterschied.`));
        if (comparison && diagnostic.search.active) details.append(element('p', `Unterschied der übrigen hypothetischen Komposition: ${comparison.background_logit_difference.toFixed(4)} Logit.`));
        const rootEvidence = document.createElement('ul');
        for (const group of Object.values(diagnostic.families)) for (const term of group.terms) rootEvidence.append(element('li', `${group.label} · ${term.subjects.join(' / ')}: ${term.logit_contribution == null ? 'UNKNOWN, im Modell ausgelassen' : term.logit_contribution.toFixed(4) + ' Logit'}; Trainingsmatches: ${term.training_matches ?? 'UNKNOWN'}`));
        details.append(rootEvidence);
        const totalDetails = document.createElement('details'); totalDetails.append(element('summary', 'Größte Beiträge der gesamten fertigen Komposition (nicht nur dieses Picks)'));
        const list = document.createElement('ul');
        for (const fact of item.contributions) list.append(element('li', `${fact.label || fact.feature}: ${fact.logit_contribution.toFixed(4)} Logit; ${item.evidence.feature_support[fact.feature]} Trainingsmatches`));
        totalDetails.append(list); details.append(totalDetails);
        if (data.snapshot_token) {
          const save = element('button', 'Diesen Pick als Entscheidung speichern'); save.type = 'button';
          save.addEventListener('click', async () => {
            save.disabled = true;
            try {
              const saved = data.snapshot_id ? await post(`${form.dataset.snapshots}${data.snapshot_id}/result/`, {chosen: item.slug}) : await post(form.dataset.snapshots, {token: data.snapshot_token, chosen: item.slug});
              status.textContent = `Draft #${saved.id} gespeichert. Ergebnis kann später ergänzt werden.`;
              await loadSnapshots();
            } catch (error) { status.textContent = error.message; save.disabled = false; }
          });
          details.append(save);
        }
        results.append(details);
      }
      if (data.unavailable_candidates.length) results.append(element('p', `Ohne eigene Trainingsevidenz: ${data.unavailable_candidates.join(', ')}`));
    } catch (error) { if (version === requestVersion) status.textContent = error.message; }
    finally { submit.disabled = false; }
  });
})();
