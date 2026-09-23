# Drafter V2 Data Gaps

Current status before the authorized tagged-frontier experiment (2026-09-23, D-008). No replacement values are introduced.

| Gap | Status | Legitimate next step |
|---|---|---|
| Actual historical DB counts in this isolated worktree | AVAILABLE via anonymized read-only snapshot | Re-run read-only audit; never connect evaluation to live DB |
| Rawpayload inventory and file provenance | PARTIAL; 866 linked metadata rows, raw JSON removed from snapshot | Raw JSON remains unavailable to V2; do not treat metadata as payload evidence |
| Official API capability matrix | PARTIAL, confirmed by bounded HTTP-200 audit plus fixture | Do not infer fields absent from observed responses |
| Valid player-skill control variable | UNKNOWN | Search observed API fields and provenance; do not use rank/trophies as skill without validation |
| Pick order / bans in official match history | UNKNOWN | Use observed payload fields only; current model comments indicate these are absent |
| Structured conditional mechanics and patch coverage | NOT ESTABLISHED | Execute PLAN 5A source/coverage inventory before schema/features; preserve raw/derived/validated layers, ability conditions, source/retrieval dates and historical UNKNOWN loadouts (D-006) |
| Validated team-composition feature benefit | UNAVAILABLE | Needs sourced mechanics and a new preregistered evaluation window; historical holdout is closed; no hand-set anti-tank/team weights |
| Isolated API credential | LOADED from independently supplied mode-600 file for run 4 | Presence succeeded; remote validity remains untested because run 4 made zero requests. Load only for bounded collection, never from live credentials |
| Tagged Ranked provenance for broad_high_rank | UNAVAILABLE | 61,146 historical Ranked player rows have blank tags; zero broad candidates despite due tracked players. Run the explicitly authorized independent official-ranking/tagged-frontier experiment (D-008); preserve source distinctions, never reconstruct historical identities |
| Sufficient data for V2 promotion | NOT MET | V2 remains unpromoted after the final sealed comparison; the bounded collector added no new soloRanked observations, so collect a newer Ranked window before reconsideration |
| New current soloRanked observations after 2026-09-18 | UNAVAILABLE | Run 4 selected zero players and fetched no battlelogs; post-run growth remains DATA_UNAVAILABLE. Earlier runs added no new Ranked evidence; do not create a new freeze |
| Historical data transfer to isolated evaluation | RESOLVED safely | Snapshot was exported read-only into `/tmp`, anonymized/minimized, then imported only into the isolated DB |

Rules: UNKNOWN is not zero; no fabricated statistics, mechanics, samples, rankings or missing fields.


D-008 resolves the missing *collection mechanism*, not missing real observations:
persistent source-backed seeds/discoveries, exact raw/run pointers, shared cooldowns
and strict HTTP budgets are now implemented. Until the separate bounded experiment
actually returns data, current credential acceptance, usable current ranking tags
and new eligible soloRanked observations remain unverified. No trophy/skill proxy
or historical player linkage is introduced. The old holdout remains sealed.
