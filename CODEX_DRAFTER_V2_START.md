# So startest du den Masterauftrag in Codex

Öffne das richtige Repository als Workspace und starte Codex im Git-Root.

Gib Codex dann diese Anweisung:

```text
Read `CODEX_DRAFTER_V2_MASTER_PROMPT.md` in full and treat it as the binding project specification.

First inspect all repository-level instructions (`AGENTS.md`, `CLAUDE.md`, README/docs) and the current Git state.

Create the persistent `docs/drafter-v2/` project memory required by the master prompt, then execute the master task autonomously milestone by milestone.

Do not stop after analysis or planning. Do not ask for approval between normal milestones. Run tests and validation, fix recoverable failures, update STATUS/DECISIONS/DATA_GAPS, and commit completed milestones.

Never fabricate missing data or statistics. If a required fact cannot be verified, use UNKNOWN and follow the blocker rules in the master prompt.

Begin with Phase 0 repository orientation.
```

Optional und empfohlen: Zuerst den Planmodus verwenden und nur einmal prüfen, ob Codex die Phasen und Schutzregeln korrekt verstanden hat. Danach den Plan freigeben und vollständig ausführen lassen.
