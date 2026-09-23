# Drafter V2 Data Gaps

Current status after Phase 5A mechanics source inventory (2026-09-23, D-009); completed tagged-frontier run 5 remains unchanged. No replacement values are introduced.

| Gap | Status | Legitimate next step |
|---|---|---|
| Actual historical DB counts in this isolated worktree | AVAILABLE via anonymized read-only snapshot | Re-run read-only audit; never connect evaluation to live DB |
| Rawpayload inventory and file provenance | PARTIAL; 866 linked metadata rows, raw JSON removed from snapshot | Raw JSON remains unavailable to V2; do not treat metadata as payload evidence |
| Official API capability matrix | PARTIAL, confirmed by bounded HTTP-200 audit plus fixture | Do not infer fields absent from observed responses |
| Valid player-skill control variable | UNKNOWN | Search observed API fields and provenance; do not use rank/trophies as skill without validation |
| Pick order / bans in official match history | UNKNOWN | Use observed payload fields only; current model comments indicate these are absent |
| Structured conditional mechanics and patch coverage | PARTIAL raw inventory; Phase 5B gate NOT PASSED | Phase 5A audited 108 Brawlers and 47 categories; 107 corroborated identities, Bolt conflict. Pinned raw values demonstrably predate September 16 changes. See MECHANICS_SOURCES/COVERAGE and D-009; no current/historical feature import |
| Validated team-composition feature benefit | UNAVAILABLE | Needs sourced mechanics and a new preregistered evaluation window; historical holdout is closed; no hand-set anti-tank/team weights |
| Isolated API credential | VERIFIED for run 5: four HTTP 200 responses | Independent mode-600 file loaded only for bounded collection; no live credentials. Future validity and hourly quota remain UNKNOWN |
| Tagged Ranked provenance for broad_high_rank | UNAVAILABLE | All 61,146 historical Ranked player rows remain blank; bootstrap returned trophy matches only. Never reconstruct identities or relabel trophy neighbors as Ranked |
| Independently sourced persistent tagged frontier | AVAILABLE, three seeds / six provenance observations | Official ranking supplied 200 usable tag strings; three admitted and queried. Preserve cooldowns; actual soloRanked graph expansion still needs new eligible responses |
| Sufficient data for V2 promotion | NOT MET | V2 remains unpromoted after the final sealed comparison; the bounded collector added no new soloRanked observations, so collect a newer Ranked window before reconsideration |
| New current soloRanked observations after 2026-09-18 | UNAVAILABLE | Run 5 fetched three battlelogs: 75 trophy entries, 50 newer unique trophy matches, zero eligible soloRanked. Growth remains DATA_UNAVAILABLE; do not create a new freeze |
| Historical data transfer to isolated evaluation | RESOLVED safely | Snapshot was exported read-only into `/tmp`, anonymized/minimized, then imported only into the isolated DB |

Rules: UNKNOWN is not zero; no fabricated statistics, mechanics, samples, rankings or missing fields.


D-008 resolved the missing independent bootstrap mechanism and empirically verified
current ranking tags, credential acceptance, persistent provenance and bounded
battlelog fetching. It did not produce newer Ranked observations: all 75 returned
entries were trophy matches. Seed/trophy convenience-sample bias and skill remain
unquantified; no sampling correction is invented. The 393 distinct raw team tags
are preserved but not treated as eligible Ranked neighbors. Historical tag linkage
remains irrecoverable. Model work is still data-blocked; independent Phase 5A
source/coverage inventory may continue. See committed bootstrap JSON and DATA_AUDIT.


## Phase 5A unresolved evidence (D-009)

- Current numeric mechanics: UNKNOWN under the full source/unit/condition/patch
  contract. Four raw values match the pre-September-16 values in official notes.
  Retrieval date, asset version and Git timestamp cannot establish effective patch.
- Historic timestamp join: UNAVAILABLE. Archive builds preserve some old values,
  but complete regional hotfix histories and exact validity intervals are absent.
- Bolt kit identity: CONFLICT. Public gadget IDs target a different raw character.
  Excluded from all fragment numerators, retained in denominator 108; no repair.
- Missing-cell semantics: public raw JSON converts native empty CSV cells to
  zero/false. Native CSV blanks remain UNKNOWN; no negative capability inference.
- Conditional execution: PARTIAL. Explicit scopes/references exist, but opaque
  status/component/buddy/deck/opcode dependencies, units, target rules and mode
  conditions prevent a complete model. Limited uses, repeatability and root are
  not established by this probe; absence of a fragment is not absence in the game.
- Official current mechanics API schema: UNVERIFIED. Public documentation shell
  injects authenticated schema URL; no retained isolated brawler response exists.
  This phase loaded no credential and made no authenticated API request.
- Gear/status/component/buddy/deck tables are indexed public candidates, not yet
  body-verified in this bounded probe. A future bounded follow-up can test them;
  do not assume they resolve completeness/currentness or mode availability.
- Stable source archiving and broader redistribution terms: PARTIAL. Immutable
  CSV URLs/digests support replay; mutable release notes may change, and a digest
  alone does not preserve a lost page. No blanket game-data license established.

These are data/semantics gaps, not reasons to fabricate mechanics or weaken gates.
The smallest proposed contract and exact evidence are in MECHANICS_SOURCES.md.
New Ranked evidence is still DATA_UNAVAILABLE; no collection/model task was run.
