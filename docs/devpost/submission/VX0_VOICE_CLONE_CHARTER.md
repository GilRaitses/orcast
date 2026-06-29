# VX0 — Local voice clone charter

Date: 2026-06-24
Wave set: **VX** (Voice Clone)
Predecessor: Wave Set **V** complete (V3 stitch PASS, demo-final.webm)
Output: `docs/devpost/figures/_demo-run/demo-final-cloned.webm`

## Purpose

Replace the OpenAI-API-generated narration (Wave Set V) with a fully local voice clone
derived from the speaker reference in `pax/voice/voiceoversample.mp3`.
No external API. No GPU required. Uses Coqui XTTSv2 on the already-installed Python 3.11.

## Inputs

| File | Role |
|------|------|
| `pax/voice/voiceoversample.mp3` | Source speaker recording (192s stereo 44.1kHz) |
| `_demo-run/narration/voice_ref.wav` | Extracted 30s mono 22kHz reference for zero-shot cloning |
| `_demo-run/beats/beat-NN.webm` | Per-beat screen recordings (Wave Set V) |

## Wave breakdown

| ID | Deliverable | Gate |
|----|-------------|------|
| VX0 | This charter + registry entries | manual |
| VX1 | `.venv-tts` (python3.11 + Coqui TTS) | `python3 -c "from TTS.api import TTS"` |
| VX2 | `tools/testing/tts_clone.py`, `tools/waves/gates/vx-render.sh` | file check |
| VX3 | `demo-final-cloned.webm` (≥150s, ≥5MB, audio+video) | manual verify |

## Model

`tts_models/multilingual/multi-dataset/xtts_v2` — zero-shot voice cloning, downloads once to
`~/.local/share/tts/`. First run ~1.8 GB download. Subsequent runs from cache.

## Execution order

1. VX0 — this charter + registry
2. VX1 — create venv, pip install TTS
3. VX2 — write scripts
4. VX3 — run clone, render, stitch, verify
