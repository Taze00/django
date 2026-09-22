RESUME FROM: Phase 12 / resolve API credential inheritance into this session's command-execution environment; require a successful presence-only check, then run the still-pending five-battlelog collection under COLLECTION_RUNBOOK.md. Do not rerun the sealed evaluation.

# Drafter V2 Status

Overall:
- Active/default engine: frozen Legacy `3a565bd`; no runtime/API/UI switch.
- Completed safe milestone: interrupted collector notes preserved; isolated inventory verified; read-only post-freeze growth command and collection runbook implemented and validated.
- Current phase: Phase 12 collection preflight blocked by credential visibility; V2 promotion/integration remains gated.
- External blocker: user reports the isolated API credential is configured, but `BRAWL_STARS_API_KEY` is not inherited by this session's command processes. Login, non-login, and escalated host presence-only checks returned false, including a final recheck. No collector was started; no authentication request failed. Live credentials remain out of scope.
- Data blocker: zero eligible API Ranked matches played after `2026-09-18T15:04:42Z`. No new experiment or promotion is justified from current growth.
- Working root: `/home/alex/alex-django-drafter-v2`, branch `feature/drafter-v2`.

Latest validation:
- Resume inventory (PostgreSQL read-only): 18,322 matches, 112,776 match players, 877 payload rows, 205 tracked players, three collector runs and 98 maps.
- Ranked: 10,191 total / 10,162 countable; zero conflicts and zero reconstructed-fingerprint duplicates.
- Growth (API-only, exclusive played-at cutoff): 76 newer matches, comprising 75 `ranked` and one `friendly`; zero newer `soloRanked`, zero eligible new Ranked observations. Latest API Ranked timestamp unchanged.
- Existing runs 1/2/3 verified: 0/5/5 players queried, 0/100/0 new matches, 0/25/125 duplicate observations; all new rows in run 2 are trophy matches. No collector rerun during this resume.
- Current focused regressions: 66 V2/collector/API-client/Praxisfall tests passed, zero failures, 9.190 s test runtime, normal Django settings; system check clean. Initial read-only assertion corrected for PostgreSQL SELECT cursors; no production behavior change.
- Historical full suites (previous agent): 692 Drafter tests, four skipped, zero failures; 253 Fitness tests, zero failures. Not represented as newly rerun.
- Latest credential-resume audit paths: `/tmp/drafter-v2-credential-resume-audit.json`, `/tmp/drafter-v2-credential-resume-growth.json`; both executed with PostgreSQL read-only protection. Counts remain unchanged and growth status is DATA_UNAVAILABLE. No new run beyond IDs 1/2/3.
- This documentation-only checkpoint changes no code: prior 66-test regression remains applicable and was not rerun; fresh read-only audits provide validation for the updated inventory.
- Credential visibility last verified at: 2026-09-22T18:08:52.563568+00:00.

Sealed evaluation (final, unchanged):
- Manifest `v2-dataset-freeze-1`, digest `2bb8222b9025a5da7daadea8b9a252c39b16bcda8b07b9bc2df69315ea4dcf9e`.
- 10,158 eligible historical examples: train 6,094 / validation 2,031 / holdout 2,033.
- Final shared subset n=1,956: Legacy LogLoss/Brier 0.689749/0.248301; V2 0.692600/0.249725.
- Full V2 holdout n=2,033: 0.692603/0.249727; 77 duplicate-Brawler rows are ineligible for unchanged Legacy.
- No historical training, re-evaluation, new split, feature tuning or ranking adjustment during this resume.
- Provenance limitation: Legacy benchmark uses stored aggregates without enforcing train-only input. See EVALUATION.md; final numbers retained, not treated as proof of leakage-free generalization.

Data integrity:
- No invented observations, mechanics or API fields; missing provenance is UNKNOWN.
- No live database queries, live credential reads, API requests, imports, aggregation, schema changes, data deletion or service restarts during this resume.
- Existing uncommitted DATA_AUDIT/DATA_GAPS/DECISIONS content preserved and incorporated.
- Pick order, bans, builds, combat stats and validated skill control remain UNKNOWN; objective patch mechanics remain insufficiently sourced.

Next:
1. Once a presence-only check confirms the isolated API credential is visible to the command-execution process, verify the documented mounts/network and run at most five battlelogs with depth 1 and six-hour refresh spacing. Do not read live credentials or reset queue timestamps.
2. Run `drafter_v2_growth --after 2026-09-18T15:04:42Z --format json` with DB read-only protection. Zero new eligible rows remains DATA_UNAVAILABLE, not a reason to fabricate data or retry the same population indefinitely.
3. Before any future model experiment, preregister immutable new split membership, source/patch eligibility and training-only statistics/priors. Keep the old freeze and shared subset closed.
4. V2 search/explanations remain offline prototypes; active integration awaits evidence. No promotion or Legacy edits.
