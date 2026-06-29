# ACX — acoustic-heads-strengthen (waveset charter)

- Lane code: `ACX`  Family: `BSWR`  Owner: dispatched sub-orchestrator (answers to O0)
- Type: execution (offline python + box compute), serves via a static JSON contract
- Home: `.cca/catalogue/O0/20260629_bsw-followup-remediation/` ; dispatch `dispatch/ACX/`
- `repo_state_verified_against`: `61ba1d69ee36cf605f7ba741bdaa1defa8762834`
- Umbrella: `PROGRAM.md` ; honesty authority: `../20260629_bside-acoustic-behavior-workbench/SIGN_OFF.md`

## Intent

Strengthen the two acoustic heads the landed BAM eval flags as weak or
diagnostic-only, to the honest limit the data supports, and ship only what a
held-out eval supports. Do not revive any claim the data cannot carry.

## Grounding (real seams + verified root cause)

The landed model is `bam-dclde-salish-v1`, eval at
`infra/acoustic/eval_report_dclde_v1.json`, served as
`web/public/hydrophone/slice/classification.json`. Pipeline:
`modeling/acoustic/{features,train_eval,...}.py` (numpy/scipy/sklearn, 129-dim
log-mel silhouette). Corpus: DCLDE-2027 Salish subset, CC-BY-SA-4.0.

Verified state from the eval:
- `presence` head ships honestly (rf AUPRC 0.762, leave-station-day-out). Not in this lane's scope to change.
- `ecotype` head ships SRKW-dominated but TKW is weak: logreg TKW f1 0.434, rf TKW f1 0.277, on ~19:1 SRKW:TKW imbalance resting on few TKW station-days. This is the first strengthen target.
- `call_type_diagnostic` is DIAGNOSTIC ONLY, not shipped, not wired: pulsed_call vs whistle collapsed to the majority class (whistle recall 0.0, macro-f1 0.43). `to_strengthen`: a scoped relabel budget to a coarse CK/W/BP taxonomy across providers, OR an O0-costed learned embedding; the 129-dim silhouette is presence-oriented.
- `not_trained.single_vs_multiple`: BLOCKED, no source-count labels. Stays blocked.

Root cause: the presence-oriented hand feature plus class imbalance and sparse,
single-station coarse-call labels. The fix is a methodology decision (more
TKW/coarse-call station-days, a class-balanced or threshold-tuned head, or an
O0-costed learned audio embedding), not a code tweak.

## Locked decisions (do NOT reopen)

1. numpy + scipy + scikit-learn (+ joblib) is the default stack. torch / a
   learned embedding is an O0-costed recommendation the `ACX-Q` wave proposes,
   never a default and never self-approved.
2. Ecotype stays "estimate + confidence, SRKW-dominated (low-confidence TKW)"
   unless a measured held-out lift makes a stronger statement true. The HUD
   wording never exceeds the eval.
3. call_type ships ONLY if a held-out eval clears it at a coarse taxonomy
   (CK/W/BP or pulsed/whistle) with non-trivial minority recall (not a
   majority-class collapse). Otherwise it stays diagnostic and is not wired.
4. `single_vs_multiple` stays BLOCKED. No caller-count claim.
5. SRKW S1-S40 catalog call is never claimed.
6. Weights + corpora + raw audio to the box, gitignored; only the small
   inference JSON + eval + provenance ship in-repo with a re-fetch pointer.
7. Cross-station/cross-day held-out split only. No metric without its split and
   its confounds.

## Wave structure

- `ACX-R` (research + discovery, read-only). Parallel. Each owns one `dispatch/ACX/findings/ACX-<TOPIC>.md`:
  - R1 TKW lift: how many additional TKW station-days the DCLDE-2027 set holds; class-balancing / threshold-tuning / cost-sensitive options on the existing features.
  - R2 coarse call taxonomy: which providers carry a coarse CK/W/BP (or pulsed/whistle) label across more than one station; the honest relabel budget.
  - R3 learned-embedding option: a costed torch/embedding path (model, size, runtime, dep weight) versus the feature-only path; explicit trade-off.
  - R4 adversarial: overclaim audit, label-leakage and within-session-confound hunt, the failure mode where a minority head collapses to majority.
- `ACX-Q` (qualify methodology). GATED. Selects ONE path per head with justification and rejected alternatives; states the pass metric per head BEFORE training; flags any new dep / download / cost to O0. Returns to O0.
- `ACX-B` (implement). Extends `modeling/acoustic/*` for the selected method; reproducible offline. No schema change yet.
- `ACX-TRAIN` (box compute). GATED. Trains on the box; emits a new versioned eval report; extends `classification.json` only with eval-cleared fields. Weights to the box.
- `ACX-ADV` (adversarial review). Re-audits the trained heads for overclaim and collapse; loops back to `ACX-B`/`ACX-TRAIN` until zero open P0/P1.
- `ACX-ACCEPT` (accept). GATED. On the demo slice clip(s), the HUD wording matches measured performance exactly; verdict cites eval numbers.

`ACX-B`, `ACX-TRAIN`, and `ACX-ADV` repeat until the eval clears the lane's pass
metric or the lane returns "ships without this head" to O0.

## Acceptance criteria (hard, checkable)

- A new versioned eval report exists with per-class precision/recall/f1, confusion, AUPRC, the leave-station-day-out split, and stated confounds.
- TKW: a measured lift over `bam-dclde-salish-v1` (TKW f1 above 0.434 logreg / 0.277 rf) on the held-out split, OR an honest "no reliable lift; ecotype wording unchanged" return.
- call_type: shipped only if minority-class recall is non-trivial on a leave-station-out split at a coarse taxonomy; otherwise stays diagnostic.
- `classification.json` carries only eval-cleared fields; `single_vs_multiple` absent.
- No new dependency, download, or box run happened without an O0 gate.

## Escalation

Per PROGRAM.md. Pause and return to O0 on any new dep, download, box compute,
schema change widening a claim, or commit.
