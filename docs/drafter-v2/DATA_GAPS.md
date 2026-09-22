# Drafter V2 Data Gaps

Initial status after repository orientation. No replacement values are introduced.

| Gap | Status | Legitimate next step |
|---|---|---|
| Actual historical DB counts in this isolated worktree | UNAVAILABLE (fresh DB: all audited counts 0) | Request/document read-only snapshot if holdout needs real history; never connect evaluation to live DB |
| Rawpayload inventory and file provenance | UNAVAILABLE in isolated DB; anonymized fixture available | Use only local anonymized fixture or a documented read-only isolated snapshot |
| Official API capability matrix | PARTIAL from one anonymized battlelog fixture | Bounded official read-only audit only if credentials and destination isolation are verified |
| Valid player-skill control variable | UNKNOWN | Search observed API fields and provenance; do not use rank/trophies as skill without validation |
| Pick order / bans in official match history | UNKNOWN | Use observed payload fields only; current model comments indicate these are absent |
| Objective mechanics at patch level | PARTIAL | Use observed official sources or mark individual fields UNKNOWN with source provenance |
| Validated team-composition feature benefit | UNAVAILABLE | Needs train/validation/holdout match data; no hand-set anti-tank/team weights |
| Sufficient data for V2 promotion | UNKNOWN | Frozen split and baseline evaluation required |

Rules: UNKNOWN is not zero; no fabricated statistics, mechanics, samples, rankings or missing fields.
