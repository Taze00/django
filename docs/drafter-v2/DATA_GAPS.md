# Drafter V2 Data Gaps

Current status after bounded source follow-up (2026-09-23, D-010); completed tagged-frontier run 5 remains unchanged. No replacement values are introduced.

| Gap | Status | Legitimate next step |
|---|---|---|
| Actual historical DB counts in this isolated worktree | AVAILABLE via anonymized read-only snapshot | Re-run read-only audit; never connect evaluation to live DB |
| Rawpayload inventory and file provenance | PARTIAL; 866 linked metadata rows, raw JSON removed from snapshot | Raw JSON remains unavailable to V2; do not treat metadata as payload evidence |
| Official API capability matrix | PARTIAL, confirmed by bounded HTTP-200 audit plus fixture | Do not infer fields absent from observed responses |
| Valid player-skill control variable | UNKNOWN | Search observed API fields and provenance; do not use rank/trophies as skill without validation |
| Pick order / bans in official match history | UNKNOWN | Use observed payload fields only; current model comments indicate these are absent |
| Structured conditional mechanics and patch coverage | PARTIAL; current explanations CONDITIONAL; computed current/historical gates NOT PASSED | D-010 separates current claim use from historical joins. Ten new dependency tables expose structure but not a complete effect specification; retain frozen 5A counts and Bolt quarantine |
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


## Follow-up disposition (D-010; supersedes “not yet body-verified” above)

| Item | Classification | Concrete remaining gap / legitimate next step |
|---|---|---|
| Explicit source reference graph | SUPPORTED structurally | Native continuation rows, AND links and named targets verified; persist unresolved leaves instead of evaluating opcodes |
| Current official gear explanations | CONDITIONAL, allowlisted | Four explicit claims; preserve source/as-of, loadout and mode caveats, revalidate against later relevant changes before reuse; no current scoring or history |
| Current numeric mechanics | PARTIAL | No verified post-September-16 baseline or broad unit/behavior rules; seek a new immutable source or a narrowly evidenced independent subset |
| Source folder versus fingerprint | CONFLICT | 69.230 versus 69.229.1; no observed authoritative equivalence/effective window |
| Bolt identity translation | SUPPORTED | Rock→BOLT and RocketGirl→BROCK explicit TID translations; this does not clear kit membership |
| Bolt public kit | CONFLICT | Wrong-target gadget IDs persist; two builds have stable distinct mappings; upstream assembly cause UNKNOWN, retain quarantine |
| Broad units/parameter semantics | PARTIAL | Milliseconds explicitly identified can divide by 1000; generic timings, ticks, distance/speed and power scaling remain UNKNOWN; no guessed conversions |
| Historical feature validity | UNAVAILABLE | UTC effective intervals, hotfix applicability and equipped loadouts absent; no historical join or new model experiment |
| Complete current snapshot availability | UNAVAILABLE in inspected sources | Latest mirror branch unchanged, fingerprint mismatch and stale cells; not a proof such a snapshot can never exist |
| Timestamp/prose-based automatic backfill | UNRELIABLE | Change events are not a complete current snapshot; calendar day/commit time is not server activation |
| Probe wire-request count | PARTIAL | 21 top-level fetches recorded, one redirected; redirect hops were not counted separately, exact wire exchanges UNKNOWN. No further request; future probes disable/count redirects |

The source-structure gap narrowed; effect semantics and deployment boundaries did
not become known. The limited current explanation pass is deliberately independent
of the historical gate. Nothing here authorizes a numeric team feature, collection,
Legacy change or sealed-holdout work. See MECHANICS_FOLLOWUP and evidence JSON.

## D-011 storage boundary

The archive preserves the four reviewed annotations, not publisher response bodies.
Body availability is NOT_CHECKED; current validity remains UNKNOWN. A pinned
annotation digest establishes review identity, not server currency. New revisions
require evidence review; persistent conflict resolution and current revalidation
are not implemented. All D-010 unit/loadout/temporal gaps remain unchanged.

## D-012 product integration

Temporary historical artifacts were unavailable. Original development membership
was recovered against its known aggregate digest without loading holdout examples.
This enables experimental Train/Validation work, not independent validation or
current-patch confidence. A fresh uninspected test window remains necessary for
promotion. No new mechanics or player/loadout facts were added.

D-013: no validation benefit from the tested opponent terms. Missing independent
future evidence still prevents a promotion claim; no fabricated mechanics added
to compensate for the negative result.

D-014: historical pick order remains unavailable. Search order comes from explicit
UI first-pick side and existing sequence, never reconstructed history. Training
appearance support is not opponent pick probability. Strong replies outside the
bounded shortlist can be missed; no search-quality improvement is asserted.

D-015 logs selected user decisions and self-reported outcomes only. Neither player
skill nor causal recommendation benefit nor verified battle linkage is obtained.
Do not treat the log as an unbiased test set or automatically feed it into V.

## D-016 remaining scientific blocker

Independent newer eligible Ranked evaluation data is still unavailable from the
completed evidence. Train/Validation-only iteration supports experimental selection,
not a new generalization claim. The tested opponent interaction extension did not
help. Stronger real-world search, current calibration and production promotion need
preregistered future outcome evidence; the closed holdout is not reusable.

No new collector was run, no mechanics facts fabricated, and no model promotion
was inferred from working UI/API or user snapshots. Browser DOM/visual automation
was unavailable; HTTP/static/CSRF and V8 syntax checks have narrower validation scope.


## D-017 Hideout diagnostic limitations
User-reported normal Sprout/Carl/Gray ranking cannot be reproduced on the isolated
instance; its exact request/session/provider snapshot is unavailable. Difference
UNKNOWN. New receipt and same-session check expose these inputs going forward.
Active V lacks candidate-enemy interactions, role/terrain/mechanics attribution,
composition-specific uncertainty and established current-patch applicability.
Feature support counts do not establish six-brawler composition support or causal
benefit. See HIDEOUT_DIAGNOSTIC.md; no data invented or newly collected.


D-018: shadow entries have no verified real-match identity, played-at time, outcome or selection probability. Recommendation exposure is recorded, display/attention is unverified. Repeated requests are not deduplicated matches. No causal or independent-test inference.
