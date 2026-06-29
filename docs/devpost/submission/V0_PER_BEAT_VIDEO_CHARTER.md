# V0 — Per-beat video charter

Date: 2026-06-24
Wave set: **V** (Video, per-beat)
Predecessor: Wave Set **A** complete (A5 a-gate PASS), Wave Set **W** complete (W6 PDF PASS)
Capstone: **H1** manual Devpost submit (depends on **V3** stitch PASS)

## Problem with the current approach

`demo:record` runs the whole 8-beat spec in one Playwright process and produces a single continuous webm (~134s). This means:
- One slow beat (planner API call, journal publish) stalls the whole recording
- A flake in beat 6 requires re-recording beats 1–5
- Pause lengths must be uniform across all beats
- Stitching different takes is impossible without re-recording everything

## Solution: one Playwright test per beat, one webm per beat, ffmpeg concat

Each beat runs as its own `test()` in a dedicated spec file with its own `video` output. Beat-specific pause times can be tuned independently. ffmpeg concatenates the 8 webms into the final 3-minute video.

## Beat spec

| Beat | File | URL / action | Target duration | Narration cue |
|------|------|-------------|-----------------|---------------|
| 1 | `beat-01-home` | `/` — map loads, confidence meter, hero | 20s | "Wildlife forecasts hide thin evidence..." |
| 2 | `beat-02-provenance` | `/?lat=48.5465&lng=-123.03&provenance=1` — modal + kernel rows | 25s | "Every cell traces back to data..." |
| 3 | `beat-03-gates` | `/gates` — integrity conditions + PSTH | 25s | "These are fitness gates on a negative-binomial fit..." |
| 4 | `beat-04-planner` | `/explore?planner=1` — click, wait for panels | 25s | "Central Casting plans which panels to open..." |
| 5 | `beat-05-ask` | `/ask` — Check sighting → reply | 20s | "Sighting check separates what the model knows..." |
| 6a | `beat-06-journal` | `/journal` — fill + Publish | 15s | "Field notes stay private until you publish..." |
| 6b | `beat-06-moderation` | `/moderation` — Approve | 10s | "Shore reports hit a moderation queue..." |
| 7 | `beat-07-dynamodb` | static slide | 20s | "DynamoDB is the backbone: nine tables..." |
| 8 | `beat-08-architecture` | static slide | 25s | "Vercel frontend, App Runner API, DynamoDB..." |

Total target: ~185s (~3:05) before stitching overhead.

## Wave breakdown

### V1 — Per-beat spec files

Create `web/e2e/beats/` containing one spec per beat (or beat-segment). Each spec:
- `test.beforeEach` installs agent auth
- Navigates to the beat URL, waits for content
- Records video with `DEMO_RECORD=1` using `BEAT_PAUSE_MS` env var for per-beat pause control
- Outputs webm to `docs/devpost/figures/_demo-run/beats/beat-NN-{slug}/`

Add npm scripts to `web/package.json`:
```json
"demo:beat": "DEMO_RECORD=1 playwright test --project=chromium-desktop",
"demo:beat-all": "DEMO_RECORD=1 playwright test beats/ --project=chromium-desktop"
```

### V2 — Per-beat gate

`tools/waves/gates/v-beat-check.sh` — for each expected beat webm, verify: file exists, size > 100KB, `ffprobe` duration within ±5s of target. Exit 0 only when all 9 webms pass.

Wire into `run-gate.sh` as `v-beat`.

### V3 — Stitch gate

`tools/waves/gates/v-stitch.sh`:
1. Calls `v-beat-check.sh` first
2. Writes `docs/devpost/figures/_demo-run/concat.txt` listing all beat webms in order
3. Runs: `ffmpeg -f concat -safe 0 -i concat.txt -c copy demo-final.webm`
4. Verifies `demo-final.webm` exists, size > 5MB, duration between 150s and 220s
5. Copies to `docs/devpost/figures/_demo-run/demo-final.webm`

Wire into `run-gate.sh` as `v-stitch`.

### V4 — Registry + H1 handoff

- Add V0–V3 to `waves.registry.yaml` with `next_wave_set: H1`
- Update `H1_MANUAL_SUBMIT.md` — replace `demo-walkthrough.webm` reference with `demo-final.webm`
- Update `DEMO_NO_CRED_STORYBOARD.md` — add per-beat recording commands

## Execution order

```
V0 charter → V1 specs → V2 beat gate → record beats → V3 stitch → demo-final.webm → H1
```

Beats can be re-recorded individually without affecting others. V2 gate catches duration regressions before stitching is attempted.

## Beat pause control

```bash
# Per-beat overrides:
BEAT_PAUSE_MS=20000 npm run demo:beat -- beat-01-home   # 20s pause on home
BEAT_PAUSE_MS=8000  npm run demo:beat -- beat-06-moderation  # tight on approve

# Default fallback: DEMO_RECORD=1 → 12s (existing behavior)
```

## Out of scope

- Audio/narration track (operator records narration in screen-capture software over demo-final.webm)
- Hackathon video editing beyond concat (trim handles, crossfades — use iMovie/DaVinci after stitch)
- Live AWS console beat (beat 7 stays static slide)
