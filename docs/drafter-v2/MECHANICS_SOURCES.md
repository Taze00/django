# Phase 5A: mechanics sources and decision gate

Audit date: 2026-09-23. Started from clean `a0242b9`, following completed
`8661c29` implementation and bootstrap run 5. **Phase 5A inventory complete;
Phase 5B implementation gate NOT PASSED.** This is an evidence inventory,
not an import, mechanics schema, current balance database or model experiment.

## Scope and evidence

The read-only isolated catalog contains **108 Brawlers, 106 Ranked-available**.
All 108 remain in the denominator, including inactive Legacy profiles and source
conflicts. `is_active` is a curated Legacy flag, not the current roster boundary.
The public metadata response contains 109 entries; its documentation says 107.
Neither count silently replaces the local catalog. Identity matching uses local
external ID plus normalized public display name, a source-provided character ID,
and gadget/Star-Power ID-to-card Target corroboration. No guessed internal aliases.

107 identities pass these source checks. Bolt's metadata includes gadget IDs
23000245 and 23000316, whose raw card Target is RocketGirl, alongside Rock kit
references. The entire Bolt row is quarantined from coverage counts; its ID,
conflict and denominator membership remain visible. This corroborates a source
claim, not an independently certified official ID namespace: BrawlAPI synthesizes
raw IDs using a file ID and row position. Numeric IDs alone are insufficient.

The bounded public probe made 26 unauthenticated HTTP GETs, no retries, each
capped at 3 MB. Exact URL, retrieval time, response status, size and SHA-256 are
in [MECHANICS_PROBE_2026-09-23.json](MECHANICS_PROBE_2026-09-23.json).
It inspected six mechanics tables in JSON and pinned CSV, one older character
CSV, metadata/indexes, three official release pages and public developer-doc
assets. No repository clone, broad wiki crawl, executable asset, game client,
player endpoint, credential, DB write or collector run. Raw public probe bodies
remain temporary; committed evidence is minimized identities, hashes, field
locators, aggregate coverage and this small factual verification sample.

## Source register

| Source | Access / readability / cadence | Version and coverage | Authority, usage, reproducibility and failure modes |
|---|---|---|---|
| Official Brawl Stars API / developer portal | API client exists; requires credential. Public portal and Swagger HTML return 200, but schema URL/token are injected from authenticated cookies. No login or authenticated request in this task. | Existing repository catalog integration reads ID/name and leaves equipment metadata raw. No retained isolated `brawlstars.brawlers.raw` body was found. Current comprehensive mechanics fields and API schema therefore UNVERIFIED, not claimed nonexistent. | Primary for responses actually observed. Current mechanics coverage UNAVAILABLE in this audit. Public HTML bundle timestamp is not game patch provenance. No publicly accessible official full mechanics data export was verified. [Portal](https://developer.brawlstars.com/), [Swagger shell](https://developer.brawlstars.com/api-docs/index.html). |
| Official Supercell release notes | Public HTML, structured headings and prose, manually reviewable; event-driven updates, no fixed cadence established. | Explicit old/new changes and conditional ability descriptions for selected fields; incomplete roster coverage. Mutable pages contain multiple maintenance dates. Publication, effective maintenance day and HTTP Last-Modified differ; exact deployment time usually UNKNOWN. | Primary change evidence, SUPPORTED for explicit change statements only. PARTIAL for complete current/historical state. URL + section date + response digest required. No assumption that unmentioned values are unchanged. [September maintenance on August page](https://supercell.com/en/games/brawlstars/blog/release-notes/release-notes-august-2026/), [June page](https://supercell.com/en/games/brawlstars/blog/release-notes/release-notes-june-2026/), [February page](https://supercell.com/en/games/brawlstars/blog/release-notes/release-notes-february-2026/). |
| BrawlAPI public metadata and raw JSON | Public JSON, no auth. `/v1/brawlers`, `/game`, `/game/{path}` returned 200. Static publication, no quantitative refresh guarantee found. | 109 metadata entries; six raw tables with 456 characters, 713 skills, 759 projectiles, 842 areas, 1,474 cards, 276 accessories. `version:1` on metadata is not a balance patch. Raw file IDs are synthetic; descriptions contain unresolved placeholders. | PARTIAL discovery/identity source. Cross-check raw names/targets and original cells. Blank CSV booleans/numbers become false/0 in this JSON representation: UNRELIABLE as negative capability evidence. No blanket data redistribution license established. [Provider documentation](https://brawlapi.com/). |
| tailsjs/brawl-stars-assets, global build 69.230 | Public GitHub raw CSV; header plus type row, machine-readable. Only six relevant CSVs and one older character CSV probed; no bulk archive download. | Immutable revision `cc307ffd36678ac463cc2ca9373a08b0a2d2b0b7`; latest listed global build 69.230, commit 2026-09-01. Historical directories exist, but completeness, deployment intervals and hotfix inclusion are unverified. Global/CN builds must remain distinct. | Third-party game-asset mirror, not official distribution. PARTIAL raw facts with good byte reproducibility, no trusted complete engine semantics. GitHub license field null; README references fan-content policy, not a permissive data license. Raw files contain placeholders, obsolete entries and script opcodes. [Repository](https://github.com/tailsjs/brawl-stars-assets), [pinned CSV tree](https://github.com/tailsjs/brawl-stars-assets/tree/cc307ffd36678ac463cc2ca9373a08b0a2d2b0b7/69.230/csv_logic). |
| Community reference: Brawl Stars Wiki | Search-index excerpt visible; page access blocked by robots in this audit. No bypass or full crawl. | Editorial per-Brawler prose/history, no captured revision or reproducible current patch snapshot here. | UNAVAILABLE for accepted coverage, potential cross-check only after lawful revision-pinned access. No wiki value entered as truth. [Colette reference](https://brawlstars.fandom.com/wiki/Colette). |
| Null's Brawl data API | Public repository documentation reviewed; no data imported. | README describes a private server and its own balance/content. | UNRELIABLE for official game mechanics irrespective of code license or API convenience. [Repository](https://github.com/treyder17/nulls-brawl-api). |
| Existing Drafter attributes / `Brawler.mechanik` | Locally readable hand-maintained JSON/Legacy services. | No established source/patch/condition lineage for requested objective fields. | UNRELIABLE as V2 source of truth; unchanged, not counted or converted into facts. |

Supercell's [fan-content policy](https://supercell.com/en/fan-content-policy/)
permits qualifying fan content subject to its conditions; it is not an unrestricted
license to redistribute complete game archives. This milestone retains small
factual extracts and references, no graphics or whole source tables. A later bulk
import/export must establish the relevant source's usage terms and attribution.

## What coverage means

[MECHANICS_COVERAGE.md](MECHANICS_COVERAGE.md) gives all 47 requested mechanic/
condition categories and every catalog Brawler. The accompanying JSON preserves
exact `scope|table|row Name|field` witnesses and explicit unobserved lists.

A **raw fragment** means a nonempty native CSV cell, a recognized textual
behavior label, or an explicit kit reference reached through a bounded graph.
It is not a complete, normalized, presently effective mechanic. Literal `0`
and `false` count as observed cells; blank does not. No fragment means UNKNOWN,
not that a Brawler lacks that capability. Accordingly the eight Brawlers with a
wallbreak-related field do not mean eight wallbreak-capable Brawlers: even an
explicit false `DestroysEnvironment` cell contributes source coverage.

Concrete coercion witnesses: native `skills/ShotgunGirlWeapon/PercentDamage` is
blank while public JSON contains 0; native `characters/ShotgunGirl/Disabled` is
blank while public JSON contains false. Both response digests are in the manifest.

For every mechanic the report records raw count/percentage, no-fragment count,
conditional count, source distribution and patch quality. All accepted fragment
witnesses come from pinned archive 69.230, corroborated through public identity
metadata. **Qualified current-patch coverage is 0/108 for every category** under
this audit's full identity/unit/condition/validity contract. This is a conservative
qualification result, not a claim that no individual numeric fact is knowable.
Explicit official change events are recorded separately below and are not promoted
to a complete current value function or historical validity interval.

Graph roots distinguish base, base attack, Super, equipped gadget/Star Power
candidates, Hypercharge, Buffy and NanoPower. References preserve additional
Hypercharge, transformation, summon and form-attack scopes. Gadget roots use only
metadata-listed IDs; old extra raw Star Powers are not counted as available kit.
The dataset-specific card grouping cross-checks observed MetaType families with
row names/types: 6 overcharge; 13/15/16 buddy Gadget/SP/Hypercharge families;
19 `nano_*` roguelite decks; 9 trait and 12 other event decks. This is an inventory
labeling convention, not a general engine-opcode interpreter.
Hypercharge/Buffy/NanoPower cards are raw candidate references, not equipped,
unlocked, currently released or Ranked-effective claims. Other trait/event-deck
rows remain `other/*`; archived mutation/collaboration rows are not treated as
current Ranked mechanics. Actual historical equipment and mode modifiers stay UNKNOWN.

Traversal follows only explicit whitelisted references, at most four edges.
`StatusEffect*`, `Actions*`, `Traits`, `Components`, `Buddies`, `RogueliteDeck`,
`CustomValue*` and numeric behavior opcodes are not interpreted. Public indexes
list status-effect, component, buddy, roguelite and gear tables, but their bodies
were outside this bounded probe. They are candidate follow-ups, not verified
complete definitions or evidence that those mechanics are unavailable globally.
Reported unresolved counts cover followed missing/depth-limited edges only;
a zero count does not mean these opaque dependencies were decoded.

Timing/radius/charge fields are partial parameter slots. Accessory `Cooldown`,
skill `Cooldown`, `Ticks`, milliseconds and generic `Range` are not silently
converted to a common unit. `Value=-1` is an undecoded sentinel, not unlimited
uses. `MaxCharge` alone cannot establish repeatability. Charge behavior does not
fully specify dash/jump collision rules. A `Damage` field may parameterize healing;
projectiles per emission do not determine total damage instances or DPS. No power
level, distance unit, HP denominator, wall geometry or scaling formula is invented.

## Small verification sample

Selection was by representation, in ascending catalog ID within each criterion,
not by draft outcome. These are source-pipeline checks, not model acceptance tests.
Each locator names the pinned CSV table/row/field; numbers are **raw source strings**.

| Representation / selection criterion | Brawler and reproducible source path | Finding |
|---|---|---|
| First direct projectile weapon with one projectile per emission | Colt: skills/GunslingerWeapon/{Damage,NumBulletsInOneAttack,ActiveTime,MsBetweenAttacks} = 360,1,650,100 | Per-emission count and timing do not prove burst count or DPS. |
| First nonempty attack PercentDamage | Colette: skills/PercenterWeapon/{PercentDamage,Damage} = 39,1100 | Percentage slot plus numeric damage; target denominator, minimum/exception logic and power scaling remain unresolved. |
| First Super projectile exposing HealOwnPercent | Poco: projectiles/DeadMariachiUltiProjectile/HealOwnPercent = 100; skills/DeadMariachiUlti/Damage = 2100 | Damage-named slot cannot safely be classified as damage dealt. Ally/self targeting needs full semantics. |
| First reached positive area destruction flag | Brock: areas/RocketGirlGadgetSkillMegaRocketEndExplosion/DestroysEnvironment = true | Conditional gadget path; never permanent base wallbreak. Bull's earlier field is explicitly false and fails this positive sample criterion. |
| First Super Charge label | Bull: skills/BullDudeUlti/{BehaviorType,ChargeType,ChargeSpeed} = Charge,1,2000 | Mobility behavior visible; numeric charge subtype and speed units not decoded. |
| First direct Super StunLengthMS | Frank: projectiles/HammerDudeUltiProjectile/StunLengthMS = 2000 | Typed name provides a candidate duration; targeting, exceptions and patch validity still require validation. |
| First matched gadget/SP/Hypercharge/Buffy/Nano card family | Shelly: cards/ShotgunGirl_Buddy_Gadgets/{MetaType,Type}=13,buddy and cards/nano_shelly_deck/{MetaType,Type,RogueliteDeck}=19,roguelite,nano_shelly_deck | Explicit separate references; opaque buddy/deck contents and mode conditions cannot be flattened. |
| First ChangeCharacter Super | Meg: skills/MechaDudeUlti/{BehaviorType,SummonedCharacters}=ChangeCharacter,MechaDudeBig | Transformation even though field is named SummonedCharacters; alternate attack path remains conditional. |
| First ordinary Super SummonedCharacters reference | Jessie: skills/MechanicUlti/SummonedCharacters=MechanicTurret | Separate summon identity and attack context; never substituted for base attack. |
| First conflicting public kit target (negative control) | Bolt: public gadget IDs 23000245/23000316 → cards Target RocketGirl instead of Rock | Fail closed; no manual removal of inconvenient IDs or alias repair to improve coverage. |

Official notes independently establish that NanoPower/Fusion behavior depends on
mode/selection and that ability changes can be conditional. Their prose is not a
complete machine-readable dependency graph. No source in this probe supplies
verified equipped/activated conditions for historical training rows.

## Patch checks and temporal join

The September 16 section of the official [August release page](https://supercell.com/en/games/brawlstars/blog/release-notes/release-notes-august-2026/)
explicitly changes the following values. These four deliberately narrow checks
compare the published old/new pair against exact pinned raw cells:

| Brawler / field | Archive locator | Observed raw | Official old → new |
|---|---|---:|---:|
| Wendy HP | characters/FutureGirl/Hitpoints | 2000 | 2000 → 2500 |
| Willow HP | characters/Puppeteer/Hitpoints | 3300 | 3300 → 3600 |
| Willow reload | skills/PuppeteerWeapon/RechargeTime | 2000 | 2000 → 1800 |
| Belle attack damage | skills/ElectroSniperWeapon/Damage | 1040 | 1040 → 1140 |

All four raw cells match the old value. Thus this snapshot cannot be accepted as
current merely because it was retrieved September 23. The notes give a maintenance
day, not an exact UTC deployment interval or universal power-level convention.
Those change statements are SUPPORTED; a complete current/historical function is not.

The pinned older 68.250 character file has Shelly Speed 770, versus 800 in 69.230.
This proves two archived values exist, not when each became effective on a server.
HTTP Last-Modified, Git commit time, archive build label, source publication date
and retrieval date remain separate. No match-timestamp-to-mechanics join is valid
until the relevant regional baseline, hotfix sequence, precise validity boundaries
and loadout context are known. No modern value is backfilled into old matches.

## Mechanic/source decision matrix

Codes: S=SUPPORTED for a narrowly explicit statement; P=PARTIAL raw fragments;
C=CONDITIONAL reference or statement; U=UNAVAILABLE in this bounded audit;
R=UNRELIABLE for use as official/current truth. They do not assert global absence.
`Notes` marks reviewed selected examples only, not full-roster coverage. Archive
classifications correspond to the quantitative coverage report. Public JSON is
never accepted as evidence of absence because of missing-cell coercion. Official
API coverage is U because current authenticated schema/response evidence is absent.
The Wiki is U here; private-server data is R for every mechanic.

| Mechanic | Official API | Official notes | Public JSON | Pinned CSV | Wiki | Private server |
|---|---|---|---|---|---|---|
| base.hp | U | P | P | P | U | R |
| base.movement_speed | U | U | P | P | U | R |
| attack.damage | U | P | P | P | U | R |
| attack.projectile_count | U | U | P | P | U | R |
| attack.damage_instances | U | U | P | P | U | R |
| attack.reload | U | P | P | P | U | R |
| attack.ammo | U | U | P | P | U | R |
| attack.range | U | P | P | P | U | R |
| attack.projectile_speed | U | P | P | P | U | R |
| attack.pierce | U | U | R | P | U | R |
| attack.splash_aoe | U | U | P | P | U | R |
| attack.bounce | U | U | R | P | U | R |
| attack.percentage_hp_damage | U | U | P | P | U | R |
| attack.scaling | U | U | P | P | U | R |
| attack.shoots_over_walls | U | C | R | P | U | R |
| attack.wall_penetration | U | C | R | P | U | R |
| ability.damage | U | U | P | P | U | R |
| ability.healing | U | P | P | P | U | R |
| ability.shield | U | P | P | P | U | R |
| ability.damage_reduction | U | P | P | P | U | R |
| ability.slow | U | U | P | P | U | R |
| ability.stun | U | U | P | P | U | R |
| ability.knockback | U | C | P | P | U | R |
| ability.pull | U | U | P | P | U | R |
| ability.silence | U | U | P | P | U | R |
| ability.root | U | U | U | U | U | R |
| ability.dash | U | U | P | P | U | R |
| ability.jump | U | C | P | P | U | R |
| ability.teleport | U | U | P | P | U | R |
| ability.wallbreak | U | U | R | P | U | R |
| ability.wall_creation | U | U | P | P | U | R |
| ability.bush_destruction | U | U | R | P | U | R |
| ability.summons | U | U | P | P | U | R |
| ability.transformations | U | U | P | P | U | R |
| kit.gadgets | U | C | C | C | U | R |
| kit.star_powers | U | C | C | C | U | R |
| kit.hypercharge | U | C | C | C | U | R |
| kit.nanopower | U | C | C | C | U | R |
| kit.buffy | U | C | C | C | U | R |
| kit.other | U | C | C | C | U | R |
| condition.limited_uses | U | U | U | U | U | R |
| condition.cooldown | U | C | C | C | U | R |
| condition.activation | U | C | C | C | U | R |
| condition.duration | U | C | C | C | U | R |
| condition.radius_area | U | U | C | C | U | R |
| condition.charges | U | U | C | C | U | R |
| condition.repeatability | U | U | U | U | U | R |

S is deliberately reserved for the four explicit old/new change statements
above, not assigned to any complete field/source combination. P/C counts do not
upgrade them to SUPPORTED current mechanics. The JSON flag cells marked R still
have useful positive raw observations, but absence cannot be trusted without CSV.

## Reproduction and retained provenance

Committed inputs/output:

- `MECHANICS_CATALOG_2026-09-23.json`: fixed read-only catalog snapshot, timestamp,
  counts and empty retained official-brawler-payload inventory; no player rows.
- `MECHANICS_PROBE_2026-09-23.json`: full public request/digest manifest plus
  hashes of the catalog and minimized identity projection.
- `MECHANICS_IDENTITIES_2026-09-23.json`: projection of the three public JSON
  responses to catalog-matching IDs/names, kit IDs and card Targets only. Extraction
  is exact key selection: public `{id,name,gadgets:[{id}],starPowers:[{id}]}`;
  character `{id,Name}` by local external ID; card `{id,Name,Target}` by referenced
  ability ID. No names-to-internal-alias inference or manual Bolt repair.
- `MECHANICS_INVENTORY_2026-09-23.json` and `MECHANICS_COVERAGE.md`: deterministic
  report, per-mechanic counts, all Brawlers, scopes, conflicts and cell witnesses.

The six CSV inputs are immutable public URLs recorded in the manifest. A bounded
replay needs only those files (about 1.62 MB total), not a fresh metadata request
or the large game archive. For an existing probe directory, **offline** regeneration:

```bash
cd /home/alex/alex-django-drafter-v2
PYTHONDONTWRITEBYTECODE=1 python3 -m drafter.services.v2_mechanics_audit \
  --input-dir /tmp/drafter-v2-mechanics-probe \
  --manifest docs/drafter-v2/MECHANICS_PROBE_2026-09-23.json \
  --catalog docs/drafter-v2/MECHANICS_CATALOG_2026-09-23.json \
  > /tmp/mechanics-inventory-reproduced.json
cmp /tmp/mechanics-inventory-reproduced.json \
  docs/drafter-v2/MECHANICS_INVENTORY_2026-09-23.json
```

Add `--format markdown` for the coverage document. The utility imports neither
Django nor a client, reads files only and writes stdout. It rejects modified input
hashes, duplicate identities, malformed CSV widths/headers and ambiguous targets.
It neither repairs source data nor recomputes the catalog from a changing database.

If `/tmp` is lost, these exact public inputs can be recovered into a new temporary
directory with this explicit six-request, no-retry, per-file 3 MB limit. No API
credential is needed or loaded; no environment/settings file is accessed:

```python
import hashlib, json, tempfile, urllib.request
from pathlib import Path
manifest = json.loads(Path('docs/drafter-v2/MECHANICS_PROBE_2026-09-23.json').read_text())
allowed = {'archive-' + name + '.csv' for name in
           ('characters', 'skills', 'projectiles', 'areas', 'cards', 'accessories')}
records = [r for r in manifest['requests'] if r['name'] in allowed]
assert len(records) == 6 and {r['name'] for r in records} == allowed
prefix = ('https://raw.githubusercontent.com/tailsjs/brawl-stars-assets/'
          'cc307ffd36678ac463cc2ca9373a08b0a2d2b0b7/69.230/csv_logic/')
destination = Path(tempfile.mkdtemp(prefix='drafter-v2-mechanics-replay-'))
for record in records:
    assert record['url'].startswith(prefix)
    with urllib.request.urlopen(record['url'], timeout=25) as response:
        body = response.read(3000001)
    assert len(body) <= 3000000
    assert hashlib.sha256(body).hexdigest() == record['sha256']
    (destination / record['name']).write_bytes(body)
print(destination)
```

If an upstream immutable file disappears or changes, stop replay with that
concrete failure; do not substitute a newer build under the original hash/report.
All decisions/counts/locators remain committed even if the raw upstream is lost.
The official-page and older-build comparisons are separately reproducible via
manifest URLs/digests; mutable pages may fail historical digest replay. A digest
alone cannot recover a vanished page, which is an explicit archival limitation.

Catalog query used in the isolated Django shell under
`PGOPTIONS='-c default_transaction_read_only=on'`:

```python
list(Brawler.objects.order_by('external_id', 'slug').values(
    'external_id', 'name', 'slug', 'ranked_verfuegbar', 'is_active'))
RawPayload.objects.filter(format='brawlstars.brawlers.raw').count()  # 0
```

The original isolated counts were 18,372 matches, 881 payload rows, five collector
runs. These queries read catalog/provenance only; no match labels or holdout rows
were evaluated. Docker mount/network were checked against the isolated worktree.

## Smallest defensible Phase 5B proposal — not implemented

A future contract should initially store observations, not assert normalized
mechanics. Minimum concepts supported by this evidence:

1. **Source snapshot:** provider, exact locator, SHA-256, response/retrieval time,
   source publication time, claimed region/build, immutable upstream revision,
   access/usage metadata. Every date nullable and distinct; no derived patch date.
2. **Identity/ability link:** local Brawler ID, source character/card identity,
   corroborating references, conflicting candidates and status. Conflict preserves
   evidence and prevents automatic use; no fuzzy internal-name reconstruction.
3. **Scoped observation:** raw field locator/value, source-native type/unit if
   explicit, base/attack/Super/gadget/SP/Hypercharge/Buffy/Nano/form/summon path,
   unresolved dependencies, completeness/conflict status. Normalized value/unit
   remain nullable until conversion semantics are independently verified.
4. **Conditional and temporal claim:** explicit requirements (including conjunctions,
   alternatives, mode, target, equipped/activated state), evidence for uses,
   cooldown, duration, area, charges and repeatability. UNKNOWN requirements cannot
   be dropped. Separate patch change event from `valid_from`/`valid_to`; unknown
   boundaries prohibit timestamp joins. Unknown historical loadout remains unknown.

The smallest safe first implementation, after a renewed gate, would be source
snapshots plus quarantined scoped observations with nullable validity, not a
complete effect interpreter or strategic rating table. No migrations or production
consumers are added now. HP/reload/projectile slots suggest potential ingredients;
DPS, burst, effective HP, sustain, CC reliability and access remain blocked by
units, target semantics, conditional availability and temporal completeness.
No anti_tank, thrower_counter, safe_pick, flexibility, control, lane_pressure or
objective_pressure values were assigned.

Gate requirements still open: reconcile current values/hotfix coverage; validate
identity conflicts; bound and inspect needed status/component/buddy/gear/deck
references; establish units and conditional execution semantics; establish source
usage and stable archiving appropriate to the next scope. Historical features
additionally require defensible match-time validity and observed loadouts.
A new independently preregistered dataset would still be required for model work.
The sealed holdout and final shared-subset comparison remain closed.
