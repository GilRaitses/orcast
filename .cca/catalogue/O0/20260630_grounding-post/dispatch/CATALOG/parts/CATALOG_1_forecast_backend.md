## Forecasting, modeling, backend, API

Shard 1 of 4. Area: forecasting and modeling plus backend and API. Every
resulting-code cell cites a real path and at least one commit, or says nothing
landed. Rows keyed by the registry family or wave where code landed, anchored to
the catalogued program dir. Cells avoid parentheses to pass the prose gate.

### Forecasting and modeling

| id / family | charter path | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| CAND, C-GAP/C-BUILD/C-VERIFY | .cca/catalogue/O0/20260627_forecast-candidates/CANDIDATE_CHARTER.md | Build a confirmed-sighting candidate set reachable from the four in-region hydrophones | .cca/catalogue/O0/20260627_forecast-candidates/candidates.targets.json plus orcahello caches, commit e30d0ab | done | C-VERIFY passed | 200 candidates, 166 tier-A, validation and adversarial checks PASS |
| MLM, M-L0..M-L3 | .cca/catalogue/O0/20260627_mlops/MLM_CHARTER.md | Leveled covariate-modeling go/no-go ladder L0 detector, L1 diel, L2 joint, L3 prey-space | modeling/studies/level0_detector.py through level3_prey_space.py, commits e30d0ab, d4e6b06, 70526ee, 484580f | L0/L1 done, L2/L3 frontier | mlops-gate, L gates | L0 ROC AUC 0.879 PASS, L1 diel PSTH 1.79 PASS p=0.0005, L2 FAIL at 0% with multi-station held-out skill flipped to +0.078, L3 withheld on presence-days |
| MLO, MLO-FEAT..MLO-CI | .cca/catalogue/O0/20260627_mlops/MLO_CHARTER.md | Production ML-ops platform: feature store, registry, scheduler, monitor, CI | nothing landed as product code, platform chartered only, EventBridge and Step Functions deploy operator-gated | planned, chartered | mlops-gate waiting | Not shipped. Build and deploy gated on AWS approval |
| WILDLIFE, WL-PREY/SRKW/ACOUSTIC/PREYBASE/SYNTH | .cca/catalogue/O0/20260627_wildlife-sources/WILDLIFE_SOURCES_CHARTER.md | Research real Chinook, SRKW, PAM, and prey-base sources to replace climatology placeholders | research register WILDLIFE_SOURCES_REGISTER.md and WL-*.md, commit ca5fd6a, no served code | done, research | none | 34 sources ranked by gate impact with P0/P1/P2 acquisition order, nothing promoted to confidence |
| OS, OS1..OS5 open-science-integration | .cca/catalogue/O0/20260627_open-science-integration/WAVESET_CHARTER.md | Open-science effort and detectability cross-checks, detection-range calculator, OrcaSound DSP | charter and findings docs landed, commit ca5fd6a, validated physics and DSP not committed as served code | done, measured NO-GO | OS1 served-skill | Detectability offset does not improve held-out CV skill at any scale, measured NO-GO, physics banked, confidence 0.0 |
| integrate-promote-launch-handoff | .cca/catalogue/O0/20260627_integrate-promote-launch-handoff/HANDOFF_CHARTER.md | Judge served vs baseline forecast skill, count presence-days | verdict docs TA2_TA3, TA5_SERVED, TB2_TB5, TB4_PRESENCE_DAY_COUNT, commit ca5fd6a, no product code | done, verdicts | none | Served refit verdicts and presence-day counts recorded, no promotion |

### Backend and API

| id / family | charter path | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| R-Alpha, R-Beta | docs/devpost/waves.registry.yaml R family | Auth plus community and partner API channels and the Vercel-to-backend proxy | src/aws_backend/auth.py, routers/community.py, routers/partner.py, web/app/api/be, web/app/api/v1, commits a6797a8, 1e4a6df, 8e5c6ee | done | R-echo verify | Reviewer auth and community and partner routers shipped |
| R-Gamma | docs/devpost/waves.registry.yaml R family | Kernel fit plus Step Functions forecast orchestrator | modeling/fit_kernels.py, infra/aws/stepfunctions/forecast_orchestrator.asl.json, commit 97b6397 | done | none | Kernel fit and ASL state machine committed |
| AT-0..AT-4 | docs/devpost/waves.registry.yaml AT family | FastAPI app, routers, and deploy | src/aws_backend/main.py, src/aws_backend/routers, commits 5a7e2e8, e30d0ab | done | AT-1 and AT-4 passed | Backend app and routers shipped, deploy and angular-build gates passed |
| E, E0..E5 | docs/devpost/waves.registry.yaml E family | Exploration backend, explore route, and /explore surface | src/aws_backend/exploration, routers/explore.py, commits 9b59e12, 87ff466, 7116caf | done | e2 and e-gate passed | Exploration surface shipped. Frontend half overlaps shard 3 |
| M, M0..M4 | docs/devpost/waves.registry.yaml M family | Central Casting managed-agents backend | src/aws_backend/casting, routers/managed_agents.py, routers/interactions.py, commits a6797a8, 5415b8c | done | m and m-gate passed | Managed agents and casting backend shipped |
| IC, IC0..IC7 and J0..J2 | docs/devpost/waves.registry.yaml IC family | Interactions concierge, skills manifest, keyed /plan planner | src/aws_backend/casting concierge.py, manifest.py, planner.py, panels.py, web/app/api/interactions, commits 874f830, fd50929, 7116caf | done | ic, ic4, ic6 passed | Interactions and planner backend shipped. Console UI half overlaps shard 3 |
| A1 | docs/devpost/waves.registry.yaml A family | Agent auth plus keyed API for the no-cred demo | web/lib/agentAuth.ts, web/app/api/be, web/app/api/interactions/plan, commit 8e5c6ee | done | a-gate passed | Agent auth shipped. Rest of A family is demo, shard 7 |
| Q1b, Q1c | docs/devpost/waves.registry.yaml Q family | API and backend plus DynamoDB schema scrutiny | tools/waves/gates/q1b-api-schema.sh, tools/waves/gates/q1c-ddb-schema.sh | done | passed | API and DynamoDB scrutiny passed, gaps Q1e-01 and Q1f-07 closed |
| U1 uploads family | docs/devpost/submission/U0_UPLOADS_AND_PACKAGING_CHARTER.md | Backend evidence upload route plus S3 storage | nothing landed yet | in progress | none | Not shipped. Uploads and packaging, overlaps shard 8 |

### Backend hosting and deploy

| id / family | charter path | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| WS-COLDSTART, CS1..CS5 | .cca/catalogue/O0/20260628_apprunner-coldstart/WAVESET_CHARTER.md | Drive the App Runner cold-start and recycle gap to zero user-visible impact | infra/aws warm pool config plus web/app/api/be proxy edge-blip retry, commits b9e2e13, 27e8a97 | done | CS4 acceptance | Measured max gap 0, 100 percent 2xx and 8 of 8 session-creates through rollover, warm pool MinSize 2 at about 10 dollars per month |
| SELFHOST, selfhost-cutover | .cca/catalogue/O0/20260626_orcast-selfhost-cutover/SELFHOST_CUTOVER_WAVESET_CHARTER.md | Cut production over to a self-hosted backend | infra self-host kit and .ddb baseline ledger, commit d97f798 | superseded | none | Shipped then retired by the hosting consolidation 1190fe7 and decommission 09a43ea onto Vercel plus App Runner |
| SD lane, sd-deploy-handoff | .cca/catalogue/O0/20260626_sd-deploy-handoff/HANDOFF_CHARTER.md | Fix the red Vercel deploy and write the Standing Decisions Register | web/vercel.json and .cca/STANDING_DECISIONS_REGISTER.md, commits 09684bf, 7a49961 | done | GP preflight | Verified-green deploy, root cause was the web app not tracked in git, register wired above CLAIM_BOUNDARIES.md |
| Rotation packets | .cca/catalogue/O0/20260627_mlops-handoff, signal-modeling-launch-handoff, os1-launch-handoff, orcast-handoff | Self-replacement orchestration packets for the forecast and modeling lanes | docs only, commit ca5fd6a, no product code | done, process docs | none | Rotation and hydration packets, no code landed from these dirs |

### Notes and overlaps

- Two distinct registry families share the letter R. The early R channels Alpha
  through Echo and R-backlog are this shard's backend and modeling work. The
  later R0 through R5 are whitepaper research and belong to the documentation
  shard.
- R-Foxtrot and R-Delta sit in the R family but scope to infra/aws and
  docs/devpost, so they belong to the infra-and-hosting and
  documentation shards.
- The casting and interactions families E, M, IC, A split across backend and
  console. The backend halves are traced here. The web UI halves belong to the
  frontend-and-console shard.
- BSW-BAM and BSWR-ACX scope to modeling/acoustic and infra/acoustic, and
  BSWR-STU scopes to src/aws_backend/routers. These touch this shard's code
  areas but belong to the B-side acoustic and behavior workbench shard. Commits
  b983976, 61ba1d6, 5bebddc.
