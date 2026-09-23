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
        const row = element('p', `#${saved.id} · ${saved.chosen} · ${saved.model_version} · ${saved.at} `);
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
            content.append(list); row.append(content);
          } catch (error) { status.textContent = error.message; inspect.disabled = false; }
        });
        row.append(inspect); snapshots.append(row);
      }
    } catch (error) { snapshots.textContent = error.message; }
  };
  loadSnapshots();
  let requestVersion = 0;
  form.addEventListener('change', () => { requestVersion++; results.replaceChildren(); status.textContent = 'Draft geändert. Neu berechnen.'; });
  fetch(form.dataset.catalog).then(r => { if (!r.ok) throw Error('Katalog nicht verfügbar'); return r.json(); }).then(data => {
    for (const mode of data.modi) for (const map of mode.maps) maps.add(new Option(`${mode.name} · ${map.name}`, map.slug));
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
    submit.disabled = false; status.textContent = 'Wähle Map, Draftzustand und First-Pick-Seite.';
  }).catch(error => { status.textContent = error.message; });
  form.addEventListener('submit', async event => {
    event.preventDefault(); const version = ++requestVersion;
    submit.disabled = true; results.replaceChildren(); status.textContent = 'Berechne …';
    const picks = side => [...form.querySelectorAll(`[data-side="${side}"]`)].map(s => s.value).filter(Boolean);
    try {
      const response = await fetch(form.dataset.endpoint, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value},
        body: JSON.stringify({map: maps.value, own_picks: picks('own'), enemy_picks: picks('enemy'), bans: [...bans.selectedOptions].map(o => o.value), own_team_first_pick: document.getElementById('challenger-first').checked, compare_legacy: document.getElementById('challenger-compare').checked})});
      const data = await response.json(); if (!response.ok) throw Error(data.fehler || 'Anfrage fehlgeschlagen');
      if (version !== requestVersion) return;
      status.textContent = `${data.model_version} · ${data.recommendations.length} Kandidaten · ${data.elapsed_ms} ms · experimentell`;
      results.append(element('p', `Modellstand ${data.artifact_sha256}. Training: ${data.provenance.train.n} Matches bis ${data.provenance.train.last}.`));
      results.append(element('p', data.search.approximate ? `Begrenzte Minimax-Suche: ${data.search.evaluated_leaves} vollständige Kompositionen. Folgepicks aus einer Shortlist nach Trainingshäufigkeit; stärkere Antworten außerhalb bleiben möglich.` : 'Alle unterstützten legalen Kandidaten; vollständige Kompositionen.'));
      if (data.legacy) {
        results.append(element('h2', 'Experimenteller Vergleich'));
        results.append(element('p', 'V2: Modellschätzung. Legacy: heuristischer Score, keine Wahrscheinlichkeit. Gleicher Draft; Rangunterschiede belegen keine bessere Qualität.'));
        const table = document.createElement('table');
        const head = document.createElement('tr');
        for (const label of ['Rang', 'V2 · Modellschätzung', 'Legacy · Score']) head.append(element('th', label));
        table.append(head);
        for (let i = 0; i < Math.min(10, Math.max(data.recommendations.length, data.legacy.recommendations.length)); i++) {
          const v2 = data.recommendations[i], legacy = data.legacy.recommendations[i];
          const row = document.createElement('tr'); row.append(element('td', i + 1));
          row.append(element('td', v2 ? `${v2.name} · ${(v2.p_win * 100).toFixed(1)} %` : 'Keine Empfehlung'));
          row.append(element('td', legacy ? `${legacy.name} · ${legacy.score}` : 'Keine Empfehlung'));
          table.append(row);
        }
        results.append(table);
      }
      for (const item of data.recommendations) {
        const details = document.createElement('details');
        details.append(element('summary', `${item.name} · Modellschätzung ${(item.p_win * 100).toFixed(1)} %`));
        details.append(element('p', `Unsicherheit: UNKNOWN. Unbekannte Features: ${item.evidence.unknown_features.length}. Beiträge sind gelernte Zusammenhänge, keine kausalen Effekte.`));
        if (item.continuation.length) details.append(element('p', `Hypothetische Fortsetzung: ${item.continuation.map(p => `${p.side === 'own' ? 'Wir' : 'Gegner'}: ${p.slug}`).join(' → ')}. Beiträge beziehen sich auf diese vollständige Komposition.`));
        const list = document.createElement('ul');
        for (const fact of item.contributions) list.append(element('li', `${fact.feature}: ${fact.logit_contribution.toFixed(4)} Logit; ${item.evidence.feature_support[fact.feature]} Trainingsmatches`));
        details.append(list);
        if (data.snapshot_token) {
          const save = element('button', 'Diesen Pick als Entscheidung speichern'); save.type = 'button';
          save.addEventListener('click', async () => {
            save.disabled = true;
            try {
              const saved = await post(form.dataset.snapshots, {token: data.snapshot_token, chosen: item.slug});
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
