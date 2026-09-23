# Hideout diagnostic — D-017

Runtime diagnostic, not a quality evaluation or tuning target. Full measured
output: [HIDEOUT_DIAGNOSTIC.json](HIDEOUT_DIAGNOSTIC.json). The selected artifact
is byte-identical to D-016; no fit, holdout read or Legacy scoring modification.

## Identical Legacy inputs

Bounty mode ID 5 / Hideout map ID 33 / patch ID 2; own Mortis, Gene;
enemy Piper, Amber, Pearl; empty bans; enemy first; own turn 6 / Last Pick;
rank pool masters; anonymous session, zero personal preferences; gemessen
provider; 101 legal scored candidates. Both endpoints run within the same
read-only repeatable-read DB transaction. The JSON records the complete pool,
resolved serialized context, personal/configuration hashes and loaded scoring
inputs hash. This hash covers loaded aggregates, catalog, balance changes and
map/mode/patch, not the entire database or V2 training dataset.

Before this change, comparison used `empfehlungen(anzahl=200, mit_details=0)`;
normal API uses `DraftEngine(ctx).als_dict()` (default eight detailed results).
Both already produced the same first eight and all candidate scores locally:
Sandy, Belle, EMZ, Rico, Ziggy, Brock, Wendy, R-T. No different scorer, lost
context, ID mismatch or changed provider was observed. Changing first-pick side
alone still gives that Legacy top eight. Normal UI recommendation list preserves
server order; its separate brawler grid uses its own rounded-score/name sorting
and client filters. These are different display surfaces.

The reported Sprout/Carl/Gray/8-Bit/Max output is **not reproduced**. Its exact
request, session preferences, instance/data snapshot and display surface are
unavailable; the differing input is UNKNOWN. Do not claim a proven cause.
The comparison now calls the exact normal `als_dict()` path, returns its list
unchanged and exposes the full receipt plus a same-session normal-endpoint check.
This removes the response-depth/details inconsistency; no score adjustment.
No change to normal Legacy endpoint, UI or frozen engine.

## What actually ranks Wendy above Gus and Belle

| Candidate | Model P(win) | Individual logit | Bounty logit | Hideout logit | Team pairs logit |
|---|---:|---:|---:|---:|---:|
| Wendy | 47.249651% | 0.087026 | 0.032310 | 0.000845 | -0.002419 |
| Shade | 46.447750% | 0.076120 | 0.014038 | 0.005120 | -0.009720 |
| Gus | 46.237090% | 0.042177 | 0.027994 | 0.020941 | -0.014025 |
| Belle | 46.087852% | 0.044161 | 0.015339 | 0.005331 | 0.006250 |

These probabilities exactly reproduce the pre-change diagnostic. Logit terms
are joint learned associations, not independent tactical benefits or percentage
points. Shared fixed-draft background is -0.22788769 logit, so positive candidate
contributions do not imply a total probability above 50%.

Wendy versus Gus: +1.012561 percentage points, explained by +0.044849 individual,
+0.004317 mode, -0.020095 map and +0.011606 teammate logit differences.
The map term favors Gus. Wendy versus Belle: +1.161800 percentage points, with
+0.042865 individual, +0.016971 mode, -0.004486 map and -0.008669 teammate differences.
Map and teammate terms favor Belle. There is no validated statement that Wendy
is tactically superior to either candidate.

Enemy-specific candidate interactions are **inactive**. For this fixed Last Pick,
enemy terms change absolute probability but cancel from candidate logit differences
(apart from which candidates are legal). No future moves/search bonus exists.
Earlier picks instead expose the chosen hypothetical continuation and its different
background contribution, without treating search as a separately learned bonus.

Wendy has 929 training matches for her global term, 165 for Bounty, 29 for Hideout,
and 24/61 for her two teammate pairs. These are feature-support counts, not
independent composition observations, reliability percentages or confidence
intervals. The exact six-brawler composition's support and gap uncertainty are
not established. Mechanics, terrain, roles, equipped loadouts and current-patch
applicability are not supplied by these coefficients. No anti-tank/control/role
explanation is justified. Beyond additive learned terms, this model cannot explain
why Wendy beats Gus/Belle. The UI now says so explicitly.

The old largest-whole-composition terms obscured the rank explanation with shared
background effects. New diagnostics separate individual/mode/map/team/enemy terms,
compare each alternative to the leading candidate (leader to runner-up), display
feature support and UNKNOWN terms, and keep full-composition terms separately.
Removing a candidate is algebraic attribution only: no partial-team prediction.

## Reproduction and validation

Run from the isolated checkout, with the preserved D-016 local artifact:

```sh
DJANGO_SECRET_KEY=drafter-v2-isolated-test-only DJANGO_REGISTRATION_KEY=disabled \
docker compose -p drafter-v2-isolated run --rm --no-deps -T \
-e PYTHONDONTWRITEBYTECODE=1 -e 'PGOPTIONS=-c default_transaction_read_only=on' \
--entrypoint python django-dev manage.py shell < docs/drafter-v2/hideout_diagnostic.py
```

Focused suite: 52 passed (9.145 s), covering diagnostic reconciliation, UNKNOWN,
inactive enemy effects, hypothetical search background, concrete Hideout endpoint
parity, side/bans/personal/pool differences, existing Challenger/planning/API and
explanation contracts. Synthetic tests assert equality and invariants, never a
desired ranking. Real isolated diagnostic asserts complete recommendation objects,
all scores, resolved state and provider data equal. JavaScript parsed in V8;
local HTTP/CSRF/static/First/Mid/Last smoke passed. No automated rendered-browser
claim. Earlier full Drafter/Fitness runs remain D-016 evidence, not rerun here.

Next master-plan boundary remains independent future Ranked evidence for quality
claims/promotion. Working experimental Last/Mid/First and comparison remain usable;
no repeated mechanics research or retraining to manufacture progress.
