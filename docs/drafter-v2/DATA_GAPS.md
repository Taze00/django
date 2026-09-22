# Drafter V2 Data Gaps

Current status after resume verification (2026-09-22). No replacement values are introduced.

| Gap | Status | Legitimate next step |
|---|---|---|
| Actual historical DB counts in this isolated worktree | AVAILABLE via anonymized read-only snapshot | Re-run read-only audit; never connect evaluation to live DB |
| Rawpayload inventory and file provenance | PARTIAL; 866 linked metadata rows, raw JSON removed from snapshot | Raw JSON remains unavailable to V2; do not treat metadata as payload evidence |
| Official API capability matrix | PARTIAL, confirmed by bounded HTTP-200 audit plus fixture | Do not infer fields absent from observed responses |
| Valid player-skill control variable | UNKNOWN | Search observed API fields and provenance; do not use rank/trophies as skill without validation |
| Pick order / bans in official match history | UNKNOWN | Use observed payload fields only; current model comments indicate these are absent |
| Objective mechanics at patch level | PARTIAL | Use observed official sources or mark individual fields UNKNOWN with source provenance |
| Validated team-composition feature benefit | UNAVAILABLE | Needs sourced mechanics and a new preregistered evaluation window; historical holdout is closed; no hand-set anti-tank/team weights |
| Isolated API credential | USER REPORTS CONFIGURED; not visible to command execution | Make `BRAWL_STARS_API_KEY` inheritable by this session's command processes and verify presence only. Login/non-login/escalated checks returned false; no API request attempted. Never read live credentials |
| Sufficient data for V2 promotion | NOT MET | V2 remains unpromoted after the final sealed comparison; the bounded collector added no new soloRanked observations, so collect a newer Ranked window before reconsideration |
| New current soloRanked observations after 2026-09-18 | UNAVAILABLE | Recent sampled battlelogs returned only already-known `ranked` trophy entries; do not create a new freeze until soloRanked rows advance the window |
| Historical data transfer to isolated evaluation | RESOLVED safely | Snapshot was exported read-only into `/tmp`, anonymized/minimized, then imported only into the isolated DB |

Rules: UNKNOWN is not zero; no fabricated statistics, mechanics, samples, rankings or missing fields.
