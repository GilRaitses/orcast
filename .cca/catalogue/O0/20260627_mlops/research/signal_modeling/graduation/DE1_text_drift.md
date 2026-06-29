# DE1 -- text dead-end drift register (methodology + charter prose)

Agent: DE1 (Wave DE, graduation waveset). Date: 2026-06-27 (America/New_York).
Scope: `docs/methodology/**`, `.cca/catalogue/**` prose (charters, dispatches, handoffs, READMEs,
STEP_LOGs), top-level modeling READMEs. Authority: SYN section 2 + S1/S2/M1/M2/M3 verdicts.
Mode: read-only audit; recommend only; no edit, no commit. Hawkes-as-GOF-diagnostic preserved (not
flagged). (Audit run by the DE1 subagent; landed to disk by the orchestrator because the read-only
explore agent cannot write files. Content is the subagent's verbatim register.)

Drift count (DE1 scope): 13 total -- 4 high, 5 med, 4 low. Cross-refs handed to DE3: 3.

## Drift-source register

| # | File (+ line/section) | Exact quote | Dead-end | Why drift (SYN/M verdict) | Recommended edit | Priority |
|---|------------------------|-------------|----------|---------------------------|------------------|----------|
| 1 | `research/signal_modeling/M2_nonlinear_physics.md` section 8 table, rank 2 | "Hierarchical LGCP backbone ... \| PROMISING AT OUR N (conditional) \| GO, coordinate with M1 \| Orchestrator-endorsed principled generalization of the current GLM" | GP-modulated intensity / spatial LGCP at current N | SYN section 2 dead-end: "GP-modulated intensity / spatial LGCP at current N (flexibility we cannot afford; revisit only after many more nodes)." M1 1.6-1.7: LGCP/GP NO-GO at 4 stations / ~300 effective onsets. M2 predates SYN and still reads as a live GO path. | Add a top banner: "Superseded by SYN section 2 (2026-06-27); LGCP is a dead-end at current N." Reclassify rank 2 to NO-GO (revisit post-node expansion); remove "PROMISING AT OUR N" / "GO". | High |
| 2 | Same file, section 9 "Promising-now" | "Hierarchical LGCP with partial pooling (rank 2): conditional on proving held-out gain over the GLM" | LGCP at current N | Same as #1. Section title "PROMISING AT OUR N" contradicts SYN dead-end set. | Move LGCP to section 9 "NEEDS FAR MORE DATA / dead-end"; keep only MMPP + shape priors under "promising-now". | High |
| 3 | Same file, Return summary | "Go/no-go: GO = HMM/MMPP (prototype), LGCP (conditional, coordinate with M1), physics shape priors" | LGCP at current N | Return summary is what skimmers cite; still lists LGCP as GO without SYN caveat. | Return summary: LGCP -> NO-GO at current N; point to SYN Tier A (hierarchical NB partial pooling) instead. | High |
| 4 | `wave_shape.yml` `signal_modeling_research.objectives.M1_sparse` (~L312) | "sparse/bursty count + point-process methods (LGCP, GP intensity, hierarchical Bayes, Hawkes, hurdle/NB, penalized GAM) that lift held-out skill at our N" | LGCP/GP; Hawkes-as-skill; NB->ZI/hurdle upgrade | Machine-readable charter still frames dead-ends as skill lifters at current N. SYN section 2 + M1: LGCP/GP NO-GO; Hawkes NO-GO as skill (diagnostic only); NB->ZI/hurdle upgrade NO-GO. | Replace with: "methods surveyed in W10; authoritative graduate/dead-end list is `SYNTHESIS_signal_modeling.md` sections 1-2 and `signal_modeling_graduation.dead_end_set`." Drop "lift held-out skill" for LGCP/GP/Hawkes/hurdle. | High |
| 5 | `.cca/catalogue/O0/20260627_wildlife-sources/WILDLIFE_SOURCES_REGISTER.md` Tier 1 table (~L44) | "NOAA satellite chl-a (CoastWatch/ERDDAP) + CUTI/BEUTI upwelling \| WL-PREYBASE \| indicator (productivity)" | CUTI/BEUTI upwelling (out of 31-47 N coverage) | S2 section 2 catalog + section 3 rank 7: product stops at 47 N; region ~48.5 N -> NO-GO / unsourceable (B.3). Register presents it as a Tier-1 strengthener with no coverage caveat. | Mark WITHHELD -- out of CUTI/BEUTI coverage (31-47 N); if upwelling is ever wanted, require a locally computed in-region index, not NOAA CUTI/BEUTI. | Med |
| 6 | `.cca/catalogue/O0/20260627_mlops/MLM_CHARTER.md` M-L3 row (~L55) | "add k_salmon ... and s_space (bathymetry + effort-corrected CAND sighting density) \| held-out skill beats recent-detection-density baseline" | Bathymetry/terrain credited on the temporal gate | S2 section 3 #6 + M3 Category E: static terrain is `s_space` / validation-only; at 4 clustered stations it cannot move the acoustic temporal CV gate toward +0.144. M-L3 gate reads as if bathymetry wiring moves held-out skill without that split. | Split gate: (a) temporal acoustic CV for `k_salmon`; (b) `s_space` quality for bathymetry (visual validation), explicitly NOT the +0.144 temporal acoustic bar. Cite SYN section 2 terrain dead-end. | Med |
| 7 | `docs/methodology/METHODOLOGY.md` section 7.2 L3 row (~L331) | "L3 Prey + space -> field ... bathymetry; sightings for space \| Held-out skill beats recent-detection-density baseline" | Bathymetry on temporal gate | Same as #6. Canonical methodology doc lacks post-SYN caveat that static bathymetry does not lift acoustic temporal CV at current geometry. | Add footnote: "At current 4-station cluster, bathymetry enters `s_space` only; it does not move the served acoustic temporal CV gate (SYN section 2; M3 section 0.2)." | Med |
| 8 | `docs/methodology/CALIBRATION_STUDIES.md` Level 3 (~L83-87) | "add k_salmon ... and s_space (point-process intensity with bathymetry/channel covariates ...) \| Fitness gate: held-out skill beats ... baseline" | Bathymetry on temporal gate | Same as #6-7. | Same footnote / gate split as #7. | Med |
| 9 | `wave_shape.yml` `M3_derived` objective (~L314) | "subtler covariates ... (tidal nonlinearities, current shear/fronts, terrain features, prey-lag, spatiotemporal terms)" | Terrain on temporal gate; HF-radar (via "current shear" ambiguity) | "Terrain features" with no B.2 role invites treating CUDEM slope/BPI as temporal skill levers. M3 section 3 #5: terrain GO for `s_space` only, NO-GO on gate. | Append: "terrain = `s_space`/validation-only per M3 E-family; subtidal currents = SalishSeaCast residual only (HF radar shadowed per S2)." | Med |
| 10 | `research/signal_modeling/M3_derived_covariates.md` section 0.3 (~L95-96) | "2D surface currents ... SalishSeaCast ROMS NEMO surface velocity, or HF-radar (limited Haro Strait coverage)" | HF-radar currents (in-region shadow) | S2 section 3 #8: inland archipelago radar-shadowed; SalishSeaCast supersedes. Listed as peer alternative without NO-GO. | Strike HF-radar as a candidate; "SalishSeaCast only; HF radar NO-GO in-region (S2 section 3 #8)." | Low |
| 11 | `.cca/catalogue/O0/20260627_mlops/RESEARCH_DISPATCH.md` Agent RD (~L107-108) | "self-exciting (Hawkes) / refractory / hurdle terms, and bin-level GOF ... as alternatives" | NB->ZI/hurdle count upgrade (hurdle terms) | M1 section 1.3: NO-GO as NB->ZI/hurdle upgrade; presence-hurdle reframe is Tier A, not a timing-rescaling "hurdle term" fix. RD dispatch can misroute builders toward count-process hurdle. | Clarify: "hurdle" here means onset dedup diagnostic only; no ZI/hurdle count upgrade (M1/SYN dead-end). Hawkes = GOF diagnostic only, not served intensity. | Low |
| 12 | `.cca/catalogue/O0/20260627_mlops/README.md` (~L17) | "burstiness/Hawkes timing fix" | Hawkes-as-skill (skim risk) | Full sentence is about L2/L3 research blockers; "Hawkes timing fix" can be read as putting Hawkes in the served model. Adjudicated path is bin-level timing gate + Hawkes diagnostic (L2_burstiness_timing, SYN A1 MMPP). | Reword: "burstiness / bin-level timing gate (Hawkes retained as event-level GOF diagnostic only)." | Low |
| 13 | `docs/README.md` (~L16, L66) | "ML Prediction Visualization - PINN and behavioral models on map" / "ML Pipeline (PINN + Behavioral Models)" | Full PINN | Hackathon-era marketing copy; contradicts SYN/M2 PINN dead-end and the honest kernel program. Low traffic for ML-ops but visible. | Archive or replace with kernel-forecast / LNP wording; if kept, label as legacy demo, not the modeling approach. | Low |

## Cross-references (DE3 lane -- egregious, not DE1-owned)

| File | Quote | Dead-end | Note |
|------|-------|----------|------|
| `.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` section 4 (~L72-75) | "I would move the backbone to a hierarchical Bayesian log-Gaussian Cox process (LGCP)" | LGCP at current N | DE3 primary; cited by M2 section 7a. mlops README points here as "Operator intent / PIML strategy" (L64). |
| Same, section 4 (~L82-83) | "For the sparse-count regime, a zero-inflated or hurdle model (or the LGCP) fits better than an NB GLM" | NB->ZI/hurdle upgrade | M1 section 1.3 NO-GO for ZI/hurdle upgrade; Tier A uses presence-reframe, not count ZI. |
| Same, section 6 (~L129-130) | "Prototype the LGCP backbone on the cached acoustic series" | LGCP at current N | Listed as "cheap, high information" experiment despite SYN dead-end. |

## Honest negatives (no drift found)

Read and clean (do NOT present adjudicated dead-ends as live without caveat):
`docs/methodology/FORECAST_KERNELS.md`, `docs/methodology/DATA_WIRING.md`,
`docs/methodology/KERNEL_FIT_STATUS.md`, `SYNTHESIS_signal_modeling.md`,
`GRADUATION_WAVESET_CHARTER.md`, `GRADUATION_DISPATCH.md`, `M1_sparse_data_methods.md`,
`S2_covariate_sources.md`, `research/L2_burstiness_timing.md`, `research/SYNTHESIS_L2_L3.md`,
`W4_BUILD_DISPATCH.md`, `SIGNAL_MODELING_DISPATCH.md` (historical W10 survey prompts),
`.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md`,
`.cca/catalogue/O0/20260627_terrain-bathymetry-twin/**`.

## Prioritized remediation list

1. Supersede M2 LGCP GO (rows #1-3): banner + reclassify rank 2 / return summary to SYN-aligned NO-GO at current N; keep MMPP rank 1 and shape priors rank 3.
2. Fix `wave_shape.yml` `signal_modeling_research` objectives (row #4): point to SYN section 2 / graduation `dead_end_set`; stop implying LGCP/GP/Hawkes/hurdle "lift skill at our N."
3. CUTI/BEUTI in wildlife register (row #5): WITHHELD + coverage note per S2 section 3 #7.
4. L3 gate split for bathymetry (rows #6-8): MLM charter + METHODOLOGY + CALIBRATION_STUDIES -- separate temporal acoustic CV from `s_space` quality.
5. Clarify M3_derived / M3 section 0.3 (rows #9-10): terrain role + SalishSeaCast-only currents.
6. DE3 pass on `ORCHESTRATOR_NOTES.md` (cross-ref): LGCP backbone, ZI/hurdle, LGCP prototype experiment -- add SYN dead-end caveats or "superseded by SYN 2026-06-27."
7. Low-priority copy (rows #11-13): RD dispatch hurdle wording, mlops README Hawkes phrasing, docs/README PINN legacy.

Nothing deployed, promoted, or committed; read-only audit only. Effective confidence stays 0.0.
