/* Standalone opt-in surface; textContent keeps source/model facts out of HTML. */
(() => {
  const form = document.getElementById('challenger-form');
  const status = document.getElementById('challenger-status');
  const results = document.getElementById('challenger-results');
  const submit = document.getElementById('challenger-submit');
  const maps = document.getElementById('challenger-map');
  const bans = document.getElementById('challenger-bans');
  const element = (tag, text) => { const node = document.createElement(tag); node.textContent = text; return node; };
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
        body: JSON.stringify({map: maps.value, own_picks: picks('own'), enemy_picks: picks('enemy'), bans: [...bans.selectedOptions].map(o => o.value), own_team_first_pick: document.getElementById('challenger-first').checked})});
      const data = await response.json(); if (!response.ok) throw Error(data.fehler || 'Anfrage fehlgeschlagen');
      if (version !== requestVersion) return;
      status.textContent = `${data.model_version} · ${data.recommendations.length} Kandidaten · ${data.elapsed_ms} ms · experimentell`;
      results.append(element('p', `Modellstand ${data.artifact_sha256}. Training: ${data.provenance.train.n} Matches bis ${data.provenance.train.last}.`));
      results.append(element('p', data.search.approximate ? `Begrenzte Minimax-Suche: ${data.search.evaluated_leaves} vollständige Kompositionen. Folgepicks aus einer Shortlist nach Trainingshäufigkeit; stärkere Antworten außerhalb bleiben möglich.` : 'Alle unterstützten legalen Kandidaten; vollständige Kompositionen.'));
      for (const item of data.recommendations) {
        const details = document.createElement('details');
        details.append(element('summary', `${item.name} · Modellschätzung ${(item.p_win * 100).toFixed(1)} %`));
        details.append(element('p', `Unsicherheit: UNKNOWN. Unbekannte Features: ${item.evidence.unknown_features.length}. Beiträge sind gelernte Zusammenhänge, keine kausalen Effekte.`));
        if (item.continuation.length) details.append(element('p', `Hypothetische Fortsetzung: ${item.continuation.map(p => `${p.side === 'own' ? 'Wir' : 'Gegner'}: ${p.slug}`).join(' → ')}. Beiträge beziehen sich auf diese vollständige Komposition.`));
        const list = document.createElement('ul');
        for (const fact of item.contributions) list.append(element('li', `${fact.feature}: ${fact.logit_contribution.toFixed(4)} Logit; ${item.evidence.feature_support[fact.feature]} Trainingsmatches`));
        details.append(list); results.append(details);
      }
      if (data.unavailable_candidates.length) results.append(element('p', `Ohne eigene Trainingsevidenz: ${data.unavailable_candidates.join(', ')}`));
    } catch (error) { if (version === requestVersion) status.textContent = error.message; }
    finally { submit.disabled = false; }
  });
})();
