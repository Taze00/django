# Drafter V2 Data Gaps

Current status after bounded tagged-frontier run 5 (2026-09-23, D-008). No replacement values are introduced.

| Gap | Status | Legitimate next step |
|---|---|---|
| Actual historical DB counts in this isolated worktree | AVAILABLE via anonymized read-only snapshot | Re-run read-only audit; never connect evaluation to live DB |
| Rawpayload inventory and file provenance | PARTIAL; 866 linked metadata rows, raw JSON removed from snapshot | Raw JSON remains unavailable to V2; do not treat metadata as payload evidence |
| Official API capability matrix | PARTIAL, confirmed by bounded HTTP-200 audit plus fixture | Do not infer fields absent from observed responses |
| Valid player-skill control variable | UNKNOWN | Search observed API fields and provenance; do not use rank/trophies as skill without validation |
| Pick order / bans in official match history | UNKNOWN | Use observed payload fields only; current model comments indicate these are absent |
| Structured conditional mechanics and patch coverage | NOT ESTABLISHED | Execute PLAN 5A source/coverage inventory before schema/features; preserve raw/derived/validated layers, ability conditions, source/retrieval dates and historical UNKNOWN loadouts (D-006) |
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
