# Bounded mechanics source follow-up after 33c570c

Protocol recorded before new requests, 2026-09-23. Phase 5A is complete; its
catalog, inventory JSON and source hashes remain frozen. This follow-up addresses
current-patch evidence, unit rules, unresolved dependency tables and Bolt identity.
No DB/API credential, match collection, model, Legacy or holdout operation.

Budget: at most 24 direct public HTTP GET attempts, no retries, 3 MB per body,
12 MB total retained responses, timeout 25 seconds, minimum 0.3 s spacing.
At most 8 web-search queries and 8 targeted page opens for primary documentation;
these discovery calls are tracked separately from direct probe HTTP counts.
Reuse already retained baseline CSVs/release pages after digest verification;
do not rerun the 26-request Phase-5A inventory or its roster coverage analysis.

Planned direct probes: latest archive commit/version evidence; missing pinned
status/component/buddy/roguelite/trait/gear/global tables; one fingerprint and
localization index/file if small enough; narrow Bolt public metadata and historical
card identity evidence. Unused budget is not permission for a larger crawl.
Stop on size/count limits, auth/rate refusal or a source requiring access bypass.
Do not execute downloaded code or treat mirrored game data as official hosting.

Gate A (current use) will be judged per explicit field/scope/as-of evidence, not
blocked merely by absent historical reconstruction. Gate B (historical training)
requires separate match-time validity and loadout evidence. Neither gate implies
model promotion. This task produces evidence and design, not mechanics features.

## Result and separate gates (D-010)

**A — current-state use: CONDITIONAL, limited pass for four source-attributed
gear explanations only.** The official current support page supplies explicit
HP/seconds/tiles or an activation phrase, independently of historical mechanics.
The allowlist is [MECHANICS_CURRENT_CLAIMS_2026-09-23.json](MECHANICS_CURRENT_CLAIMS_2026-09-23.json):
Shield gear capacity, its documented full-health regeneration duration, Speed
gear's bush/movement condition, and Gene's gear range increment. These may support
conditional factual explanations under the exact stated requirements. Unknown
loadout must produce “if equipped”, not an assertion that the team has the effect.
Unknown mode overrides remain explicit. No numeric damage simulation, current
roster completion, team scoring, recommendation ranking or inferred rate/stacking
is licensed by this limited pass. No implementation or runtime consumer added.

**A — computed current mechanics/composition features: NOT PASSED (PARTIAL).**
A current baseline, broad units and full behavior semantics are still missing.
This result does not depend on historic intervals. A smaller field set can pass
independently when its own current evidence is sufficient; it need not wait for
all Brawlers, all mechanics or historical reconstruction.

**B — historical training mechanics: NOT PASSED (UNAVAILABLE).** No new temporal
validity boundaries or equipped-loadout observations were obtained. Current
support statements and explicit maintenance-day changes cannot fill those gaps.
The historical holdout remains sealed. The limited A explanation pass does not
feed training or establish predictive benefit.

The allowlist is an evidence annotation, not a completed Phase 5B schema. Its
snapshot/observed-at label must remain visible. Before later reuse, revalidate the
same official source against relevant newer official changes; quarantine changed,
missing, ambiguous or contradictory claims. A newer announcement invalidates an
affected claim until resolved. Do not invent a permanent validity window or silently
reuse this September 23 observation indefinitely. Store source attribution and
scope even when historical `valid_from` is null. No blanket history requirement
is imposed on current explanations.

## Actual probe and source currency

21 top-level public fetches: 20 final HTTP 200, one 404, zero retries, 3,542,689 response
bytes. One 200 was a redirect to generic support, so it supplied no progression
rule. The helper counted urllib calls, not redirect hops: the exact wire HTTP
exchange count is UNKNOWN (one redirected fetch observed). This limits the
attempt-level budget accounting; no further requests were made. Future probes
must disable or explicitly count redirects. Eight search queries/eight targeted page opens were separate discovery
operations. No further requests are required for this completed experiment.
Metadata: [MECHANICS_FOLLOWUP_PROBE_2026-09-23.json](MECHANICS_FOLLOWUP_PROBE_2026-09-23.json).
The previous 26-request inventory was not repeated. Retained baseline bodies were
hash-checked and reused, not fetched or imported again. No database was opened.

| Question | Evidence | Classification / consequence |
|---|---|---|
| New immutable mirror build? | Latest commit and branch list still show only master at `cc307ffd36678ac463cc2ca9373a08b0a2d2b0b7`. Previously captured tree at that same commit ends at global 69.230. | UNAVAILABLE in inspected sources. This is not a proof that no newer source exists anywhere. |
| Alternative archive? | [BrawlCDN owner notice](https://github.com/DEV-DIBSTER/BrawlCDN) explicitly discontinues updates; it is not a new balance snapshot. The [App Store version history](https://apps.apple.com/gb/app/brawl-stars/id1229016807) returned a July client version in this capture. | UNRELIABLE for asserting September mechanics currency. Store release dates are client publication evidence, not server configuration intervals. |
| Build identity? | Directory says 69.230; its pinned `fingerprint.json` says **69.229.1**, fingerprint SHA claim `aae658958962a2d46c263bb823df63b7484184f3`. | CONFLICT / unexplained label mismatch. Preserve both labels; neither overrides the other. They may use different version namespaces; this is not proof of corrupt data. No inferred equivalence or deployment window. |
| Public structured freshness? | Small `/v2/raw/csv_logic/conditions` response has `generatedAt=2026-09-01T14:57:21.186Z`; same named predicate/array as pinned CSV. | PARTIAL; generation time is not effective patch time. |
| Later official evidence? | [News index](https://supercell.com/en/games/brawlstars/blog/) still points to the August release page; that page includes September 16 maintenance. No later comprehensive balance snapshot found in this bounded review. | PARTIAL; absence from a bounded index is not proof of no hotfixes. |
| Can the September update be reconstructed from notes? | Selected exact old/new statements, relative-only changes and behavior fixes coexist. Four prior raw mismatches remain relevant evidence. | SUPPORTED as discrete publisher change events; PARTIAL as complete current state. No prose-applied source patch. |
| Are complete current mechanics fundamentally impossible? | No observed complete post-maintenance snapshot or complete deployment/hotfix sequence. `ServerOnly` flags occur in mirrored definitions, but do not themselves prove missing server values. | UNAVAILABLE from this evidence, not proven impossible. A verified later snapshot or scoped authoritative current statements can resolve subsets. |

Archive/fingerprint sources are exact immutable URLs in the manifest. The public
raw endpoint is [BrawlAPI conditions](https://api.brawlapi.com/v2/raw/csv_logic/conditions).
HTTP retrieval date, generation time, source publication date, folder version,
fingerprint version and actual server activation remain separate claims.

## Units and normalization

Only explicit units or transformations are admissible. No conversion below is
implemented as a game mechanic; the table distinguishes mathematical unit
conversion from identifying the unit of an arbitrary raw field.

| Requested dimension | Observed evidence / deterministic rule | Result |
|---|---|---|
| HP / power level | Official support explicitly states Shield gear's 900 HP. Native localization exposes `scaleToLevel`/`scaleStatToLevel` and describes HP/damage upgrading, but supplies no general formula here. A guessed 2023 official URL returned 404; generic progression URL redirected. | SUPPORTED for the specific documented gear quantity; raw Brawler base HP level convention remains UNKNOWN / PARTIAL. No assumed Power-1 base or Power-11 multiplier. |
| Damage scale | `ScaleWithUpgrades`, `ScaleWithBuffs` and distinct weapon/stat scaling placeholders exist. | PARTIAL; no universal factor, rounding rule or power-level conversion verified. Fixed, percentage, healing and summon values stay separate. |
| Range | Official support gives Gene's gear increment in tiles. Pinned `gear_boosts/SuperRange/ModifierValue=3` targets HookDude, with an explicit InfoTID. | SUPPORTED for the directly documented one-tile increment; PARTIAL cross-check only for raw 3. A single pair does not establish general `/3` conversion for every range/radius/behavior field. |
| Movement speed | `characters.Speed`, percentage/absolute status speed fields; globals `GENERAL_MOVESPEED=12`. | PARTIAL; base distance/time unit UNKNOWN. A global name/value is not a conversion formula. |
| Reload / cooldown | Official notes give some gadget cooldowns in seconds. Source headers include explicit `Ms`/`MS`; localization calls `msAsSeconds` and separately `ticksAsSeconds`. | SUPPORTED: where milliseconds are explicitly identified, seconds = ms / 1000. Directly published seconds need no conversion. `RechargeTime`, generic `Cooldown`, and tick frequency remain UNKNOWN; do not apply `/1000` or `/20` indiscriminately. |
| Projectile speed | Raw `Speed`, globals `GENERAL_PROJECTILESPEED=6`, patch numbers without unit definitions. | PARTIAL; normalized distance/second UNKNOWN. |
| Radius / area | `Radius`/`InnerRadius` and mixed area/skill dimensions. | PARTIAL; tiles, diameter vs radius interactions and world-unit scale not verified. No borrowing the gear-range example. |
| Charge / dash speed | `ChargeSpeed`, `ChargeType`, source-specific movement components. | PARTIAL; physical units, subtype semantics and collision behavior UNKNOWN. |
| Percentage damage denominator | Status field `DamageBoostTargetCurrentHealthPercent` explicitly names current health; Colette's generic `PercentDamage` does not. | CONDITIONAL named-field evidence; Colette's full current/max-HP/minimum/target-exception function remains UNKNOWN. No inferred common denominator. |
| Projectile count vs damage instances | Separate `NumBulletsInOneAttack`, `ActiveTime`, `MsBetweenAttacks`, `ExecuteFirstAttackImmediately`, spawn/chaining and DoT slots. | PARTIAL; no verified general emission/count formula, collision cardinality or burst/DPS derivation. |

Unit sources: the exact CSV header/cell and `localization/texts.csv` placeholders
in the pinned [archive tree](https://github.com/tailsjs/brawl-stars-assets/tree/cc307ffd36678ac463cc2ca9373a08b0a2d2b0b7/69.230),
and [official gear documentation](https://support.supercell.com/brawl-stars/en/articles/gears-8.html).
`msAsSeconds` plus the definition of a millisecond supports `/1000`; a named
`ticksAsSeconds` operation supplies no tick rate. No engine implementation was
reverse-engineered or guessed to supply that missing constant. Ratio fits between
old patch numbers and raw cells are candidate evidence, not a deterministic rule.

The gear support page does not certify all game data. Some availability prose is
coarse and raw gear tables contain per-Hero deprecation arrays. Only the four
explicit allowlisted statements qualify; eligibility/ownership is not inferred
from a raw row or from broad support-page counts.

## Conditional dependency structure

Native CSV continuation rows are material evidence: blank Name continues an
ordered record rather than introducing an unnamed character or a default value.
BrawlAPI v2 independently represents `MenderFacingDirectionUlti.Values` as the
ordered array `[270,90]`, matching two CSV records. The focused reader preserves
physical CSV record ordinals for every cell (not text line numbers when a cell embeds a newline); it never zips compressed arrays by
index after dropping blanks. This matters for gear Hero/deprecation columns.

| New table | Named records | Physical rows | Continuations |
|---|---:|---:|---:|
| status_effects_logic | 410 | 410 | 0 |
| components_logic | 57 | 168 | 111 |
| buddies | 135 | 138 | 3 |
| roguelite_cards | 654 | 654 | 0 |
| roguelite_decks | 208 | 208 | 0 |
| traits | 1276 | 1276 | 0 |
| gear_boosts | 19 | 41 | 22 |
| globals | 52 | 52 | 0 |
| actions | 17 | 24 | 7 |
| conditions | 1 | 2 | 1 |

These are source table counts, not new Brawler coverage or effective-kit counts.
Twelve deliberately narrow roots exercise all requested dependency families.
Their exact nodes, cell positions and edges are committed in
[MECHANICS_FOLLOWUP_EVIDENCE_2026-09-23.json](MECHANICS_FOLLOWUP_EVIDENCE_2026-09-23.json).
Maximum traversal is six edges and 400 nodes per root. Zero unresolved followed
references in this sample does **not** establish full behavior closure: the
whitelist does not interpret every possible field or script expression.

| Family | Verified structural path / limitation | Classification |
|---|---|---|
| Gadget | Shelly card → named Accessory → named Skill → projectile/status references | SUPPORTED structure; CONDITIONAL on equipment/activation; complete effect PARTIAL |
| Star Power | Shelly card → status/trait references | SUPPORTED structure; selection and execution semantics CONDITIONAL |
| Hypercharge | Separate card/root and explicitly overcharged reference edges | SUPPORTED structural requirement; charge/activation/history UNKNOWN |
| Buffies | Card.Buddies → named Buddy → Accessory/Traits; Star-Power and Hypercharge Buddy roots stay separate | SUPPORTED structure; CONDITIONAL upgrade plus underlying ability; not a permanent passive union |
| NanoPower/decks | Card.RogueliteDeck → deck's numbered cards → named Traits | SUPPORTED structure; choice/fusion/mode rules CONDITIONAL; all deck cards must not be assumed simultaneously active |
| Summons | Jessie Super → MechanicTurret → its WeaponSkill | SUPPORTED source links; summon context never becomes the caster's base attack |
| Transformations | Meg ChangeCharacter Super → MechaDudeBig → form skills | SUPPORTED source links; form state/return transition require conditions |
| Status effects | Named slow/shield/stun/silence/immunity/duration/stacking/cancel columns | PARTIAL semantics; blanks remain UNKNOWN; tick duration cannot yet be normalized |
| Components | Named Type plus ordered Values and typed reference columns | PARTIAL; only **1/57** named components has ValueNames. Other positional parameters cannot be decoded by intuition |
| Traits | Named Type and explicit references plus Value strings (including compound values) | PARTIAL; readable opcode names are not a full specification |
| Actions/conditions | `MenderUltiFearAction` explicitly uses And and references a named facing predicate; Values `[270,90]` remain ordered | SUPPORTED Boolean connective/reference structure; angle convention/predicate evaluation PARTIAL |
| Relevant gear | ForestSpeed → GearSpeedBoostInBush; separate LogicType=0 and modifier fields | CONDITIONAL; official documentation supplies bush/movement requirement, numeric LogicType is not decoded |

A provenance graph with unresolved leaves is feasible. A universal effect
interpreter is not justified. Requirements need conjunctions/alternatives,
selected gear/gadget/SP/Buffy/Nano, target class, transformation/summon ownership,
activation/expiration, map/mode rules and source-defined state. Graph reachability
only proves a source link, never active capability, uses, repeatability or strength.
No role/strategy score or default false capability is derived.

## Bolt investigation

**SUPPORTED identity links:** pinned character.TID → localization EN gives
Rock → TID_ROCK → BOLT and RocketGirl → TID_ROCKET_GIRL → BROCK. This is explicit
source linkage, not a spelling/similarity repair. The historical 68.250 and 69.230
character row-ID claims are stable: 16000106 Rock, 16000003 RocketGirl.

| Source row-ID claim | Both inspected builds: card / target |
|---|---|
| 23000245 | RocketGirl_Jump / RocketGirl |
| 23000316 | RocketGirl_MegaRocket / RocketGirl |
| 23001281 | Rock_gadget / Rock |
| 23001282 | Rock_gadget_1 / Rock |

The independent narrow [public Bolt endpoint](https://api.brawlapi.com/v1/brawlers/16000106)
still includes all four gadget IDs. It agrees with the earlier public list's
conflict. “Independent” here means a separate investigation of older assets,
localization and endpoint consistency, not that two endpoints are independent
publishers. The two inspected builds do not show changed/shared IDs or a
Rock/RocketGirl rename. Entire historical ID uniqueness is UNAVAILABLE; two
snapshots cannot prove it. The mirror's synthetic row-ID convention also remains
a source claim rather than official identity certification.

**CONFLICT:** erroneous or stale public kit assembly is a supported diagnosis
category; its exact upstream cause and repair are UNKNOWN. No selection among
convenient gadgets, historical reconstruction, guessed rename or automatic
unquarantine. Bolt remains excluded from mechanic imports and the frozen 5A
numerators; the explicit Rock/Bolt translation can be recorded without clearing
the separate kit conflict.

## Patch-change contract proposal (design only)

Six reviewed examples in [MECHANICS_PATCH_EVENTS_2026-09-23.json](MECHANICS_PATCH_EVENTS_2026-09-23.json)
retain explicit replacements and one relative-only change. The existing official
page snapshot/hash is reused. No CSV value is changed. The source is the
[September 16 maintenance section](https://supercell.com/en/games/brawlstars/blog/release-notes/release-notes-august-2026/).
Examples include HP/damage values whose power convention is unspecified, an
unlabelled reload quantity, a cooldown explicitly in seconds and a relative
charge-time change with unknown absolute baseline. These differences must survive
serialization; the examples are reviewed annotations, not an automated prose parser.

| Concept | Minimum fields and invariants |
|---|---|
| SourceSnapshot | Stable content digest, URL, provider/authority, retrieval time, publication date if explicit, region, folder/build/fingerprint claims separately, provenance of minimized projection, usage terms. Preserve conflicting version labels. |
| RawScopedObservation | Snapshot ID, exact table/row/field or document section, raw value/native type, nullable known unit/power level/target semantics, subject/ability/form/summon IDs, ordered physical-cell positions. Normalized value requires a cited deterministic conversion rule; no defaults. |
| Dependency / requirement | Source node/field/target edges; root scope; AND/OR groups only when explicit, selected kit and activated state, target/form/owner/mode conditions. Opaque predicate/type/value tuples remain unresolved. Preserve path requirements, not merely a union of reachable nodes. |
| PatchChangeEvent | Source snapshot + exact dated section; subject/property/scope; operation `replace`, `relative`, or behavior change; stated old/new/delta values and explicit units; applicability and unresolved baseline. Statement classification separate from effect validity. A relative event with unknown baseline keeps unknown absolute result. |
| Temporal claim | Announced effective day, source timezone/precision, nullable UTC valid_from/valid_to, explicit known-open-ended marker if actually justified, observed_as_of and verification scope. Null end means unknown, not infinity. Midnight UTC is not invented from a calendar date. |
| Conflict / quarantine | Competing observations and source lineage, reason, affected fields/kit, resolution evidence. Record explicit identity facts independently from quarantined kit membership. Source priority alone cannot silently reconcile different units/scopes. |
| Eligibility for use | Separate flags for source-attributed current explanation, computed current mechanic and historical feature. The first can qualify without historical intervals; the latter two have their own evidence requirements. No model-promotion implication. |

A deterministic patch **event** can be recorded when the subject, property,
operation, values and scope are explicit. A deterministic patch **application**
additionally needs verified identity, compatible units/power/target context,
matching old baseline, complete ordering/applicability and adequate temporal
validity for the intended use. A disagreement yields CONFLICT; a missing premise
yields UNKNOWN. Behavior reworks must not be forced into scalar replacements.
The publisher's stated maintenance day is retained even when exact UTC activation
is unknown. A current source-labelled statement need not be assigned a fake
validity interval to be useful as an explanation.

Historical joins require a proven relevant time interval and scope/loadout;
unknown boundaries or missing loadout prohibit the join. No lookup “latest row
before match” is permitted using retrieval/commit/publication time. Historical
training and sealed evaluation are absent from this design/probe. A future new
model experiment needs its separate data and evaluation authorization/protocol.

Future contract acceptance cases: null versus explicit zero/false, ordered
continuations with blanks, unknown AND/OR operands, conditional path inheritance,
relative events with unknown baselines, old-value conflicts, source revision
changes, unknown UTC boundaries and forbidden historical joins. This milestone
implements only the offline source-structure audit and its tests, not that schema,
patch applicator, effect interpreter, feature extractor or live UI.

## Reproduction, validation and next evidence

The command below reads local files and prints JSON only. It imports no Django,
client, secrets or model code. It does not rerun the Phase 5A inventory:

```bash
cd /home/alex/alex-django-drafter-v2
PYTHONDONTWRITEBYTECODE=1 python3 -m drafter.services.v2_mechanics_followup \
  --new-dir /tmp/drafter-v2-mechanics-followup \
  --old-dir /tmp/drafter-v2-mechanics-probe \
  --manifest docs/drafter-v2/MECHANICS_FOLLOWUP_PROBE_2026-09-23.json \
  --baseline docs/drafter-v2/MECHANICS_PROBE_2026-09-23.json \
  > /tmp/mechanics-followup-reproduced.json
cmp /tmp/mechanics-followup-reproduced.json \
  docs/drafter-v2/MECHANICS_FOLLOWUP_EVIDENCE_2026-09-23.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  drafter.tests.test_v2_mechanics_followup drafter.tests.test_v2_mechanics_audit -v
```

The committed metadata projection contains only exact latest SHA/branch fields,
Bolt's ID/name/gadget IDs and the small conditions response; its digest is bound
in the probe manifest to the parent response digests. Thus replay does not depend
on mutable public metadata remaining unchanged. The six old CSVs plus older
characters, ten new dependency CSVs, previous cards, localization and fingerprint
are immutable URL/digest inputs. No complete source archive or localization text
is committed. If temporary bodies disappear, an explicit recovery may fetch only
those required immutable files with hash/size checks; it is not a new inventory.
Preserve source failure if an immutable URL becomes unavailable; do not substitute
newer data under these source hashes. All selected evidence and decisions survive
in Git independently of `/tmp`.

Current explanations: next safe implementation scope can be only source snapshots,
reviewed allowlisted claims and visible conditions/as-of attribution, following a
separate implementation request. Current numeric mechanics need a verified updated
source or a precisely evidenced smaller subset, explicit units and adequate
execution/condition semantics. Historical features additionally need temporal
boundaries and loadouts. Do not repeat this completed probe, retry the obsolete
2023 URL, collect matches or force Phase 5B by guessing. Normal future source/code
failures can be fixed autonomously within their bounded scope; true missing source
or temporal facts remain documented rather than manufactured.
