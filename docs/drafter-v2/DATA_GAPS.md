# Drafter V2 Data Gaps

Initial status after repository orientation. No replacement values are introduced.

| Gap | Status | Legitimate next step |
|---|---|---|
| Actual historical DB counts in this isolated worktree | AVAILABLE via anonymized read-only snapshot | Re-run read-only audit; never connect evaluation to live DB |
| Rawpayload inventory and file provenance | PARTIAL; 866 linked metadata rows, raw JSON removed from snapshot | Raw JSON remains unavailable to V2; do not treat metadata as payload evidence |
| Official API capability matrix | PARTIAL, confirmed by bounded HTTP-200 audit plus fixture | Do not infer fields absent from observed responses |
| Valid player-skill control variable | UNKNOWN | Search observed API fields and provenance; do not use rank/trophies as skill without validation |
| Pick order / bans in official match history | UNKNOWN | Use observed payload fields only; current model comments indicate these are absent |
| Objective mechanics at patch level | PARTIAL | Use observed official sources or mark individual fields UNKNOWN with source provenance |
| Validated team-composition feature benefit | UNAVAILABLE | Needs train/validation/holdout match data; no hand-set anti-tank/team weights |
| Sufficient data for V2 promotion | PARTIAL | Dataset is sufficient for baseline/model experiments; promotion still requires sealed final comparison and Legacy result |
| Historical data transfer to isolated evaluation | RESOLVED safely | Snapshot was exported read-only into `/tmp`, anonymized/minimized, then imported only into the isolated DB |

Rules: UNKNOWN is not zero; no fabricated statistics, mechanics, samples, rankings or missing fields.
