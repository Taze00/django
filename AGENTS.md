# AGENTS.md — Drafter V2 Regeln (zum Einfügen/Abgleichen)

> Falls bereits eine `AGENTS.md` existiert, NICHT blind überschreiben. Diese Regeln integrieren.

## Scope
- Multi-App Django repository.
- `drafter/**` is the primary scope for Drafter V2.
- Treat unrelated apps as protected unless a shared-file change is strictly required.
- Never change unrelated apps just to make Drafter tests pass.

## Data safety
- NEVER recursively chmod/chown `/code/data`.
- NEVER alter ownership of `/code/data/data/db`.
- NEVER delete/reset the database to fix an application bug.
- NEVER delete raw Brawl Stars API payloads to make tests/imports pass.
- Prefer additive/reversible migrations.
- Preserve historical Praxisfall/model snapshots.

## Data integrity
- Never fabricate statistics, sample counts, mechanics, matchup values, or missing API fields.
- Missing/unverified data = `UNKNOWN`.
- Do not use LLM knowledge as a database fact.
- Important numbers must be reproducible from repository data/query or documented source.
- Never print or commit API tokens/secrets.

## Model governance
- Current scorer is a frozen legacy baseline unless explicitly stated otherwise.
- Do not tune rankings to individual example drafts.
- New features must be evaluated on held-out data before becoming active.
- Unknown is not zero.

## Long-running work
Maintain:
- `docs/drafter-v2/PLAN.md`
- `docs/drafter-v2/STATUS.md`
- `docs/drafter-v2/DECISIONS.md`
- `docs/drafter-v2/DATA_GAPS.md`
- `docs/drafter-v2/REPO_MAP.md`
- `docs/drafter-v2/EVALUATION.md`
- `docs/drafter-v2/MODEL_CARD.md`

After each milestone:
- run validation/tests
- fix failures
- update docs/status
- commit completed work
- continue

Do not discard user changes or reset a dirty worktree.

## Failure policy
Recoverable code/test failure: diagnose, fix, retry, continue.
Missing data: mark unknown, document, never invent.
Unsafe/destructive action: do not execute; document and request approval.
External blocker/usage limit: leave consistent state, update exact resume point, commit only completed safe work.
