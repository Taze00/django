# Drafter V2 Data Gaps

Initial status after repository orientation. No replacement values are introduced.

| Gap | Status | Legitimate next step |
|---|---|---|
| Actual historical DB counts in this isolated worktree | UNKNOWN | Run read-only audit against isolated DB only; request/document read-only snapshot if holdout needs real history |
| Rawpayload inventory and file provenance | UNKNOWN | Inspect only isolated `data/brawl_api_raw/`; never copy live raw data |
| Official API capability matrix | UNKNOWN | Inspect anonymized fixture and, only if authorized and isolated, bounded official read-only audit |
| Valid player-skill control variable | UNKNOWN | Search observed API fields and provenance; do not use rank/trophies as skill without validation |
| Pick order / bans in official match history | UNKNOWN | Use observed payload fields only; current model comments indicate these are absent |
| Objective mechanics at patch level | PARTIAL | Use observed official sources or mark individual fields UNKNOWN with source provenance |
| Sufficient data for V2 promotion | UNKNOWN | Frozen split and baseline evaluation required |

Rules: UNKNOWN is not zero; no fabricated statistics, mechanics, samples, rankings or missing fields.
