# Challenger continuation protocol (D-012)

The user explicitly resumes autonomous product development, including experimental
V2 and Train/Validation-only improvements. This supersedes earlier blanket pauses
on experimental integration; default promotion still requires independent evidence.
Completed mechanics research is preserved and is not the critical path.

First implement a usable, explicitly experimental Last-Pick challenger using the
existing composition feature contract and previously selected training parameters
(300 epochs, L2 1.0). Do not use the historical evaluation/training commands.

The old temporary model/split files are absent. Recover membership only if ordered
historical eligibility metadata reproduces the committed freeze digest
`2bb8222b9025a5da7daadea8b9a252c39b16bcda8b07b9bc2df69315ea4dcf9e`
and 10,158 rows at/before `2026-09-18T15:04:42Z`. Read only fingerprints/times
and structural eligibility for that check, not held-out outcomes/features. Select
exactly the first 6,094 train and next 2,031 validation fingerprints. Only then
query their match outcomes/teams. Never load, predict, evaluate or select against
the remaining 2,033. Fail closed on digest/count disagreement. No new split.
Store per-partition fingerprints and canonical example digests in the local
artifact, metrics/counts/digests in the committed report. No player identifiers.

Train-only feature vocabulary, coefficients and support counts; validation only
metrics/selection. Runtime uses explicit catalog identity and context mappings,
returns UNKNOWN coverage/uncertainty honestly, and never treats probabilities as
validated current-patch or causal effects. No claimed improvement over Legacy.
No server rollout, live checkout/DB access or collector is needed.

Next bounded experiment: compare the existing model with jointly fitted directed
opponent interactions under an antisymmetric representation. Fixed grid L2
1/10/100 with 300 epochs, learning rate 0.05; include the existing model and B0.
Select lowest validation log loss, subject to Brier not worse than existing model;
if no candidate qualifies, keep existing. Report calibration and training/inference
cost; no new mechanics features. This is experimental selection, not promotion.

Then implement full-composition Mid/First planning with explicit draft order,
bounded deterministic search, measured latency, approximation limits and same V;
finally opt-in side-by-side Legacy output with separate score/probability labels.
Run regressions, document, commit and push each completed milestone and continue.
A real evidence blocker may prevent promotion without preventing usable software.
