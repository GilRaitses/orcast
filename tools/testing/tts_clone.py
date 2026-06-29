#!/usr/bin/env python3
"""Generate per-beat narration audio via Coqui XTTSv2 zero-shot voice cloning.

Requires .venv-tts (python3.11 + TTS). Run from repo root:
    source .venv-tts/bin/activate
    python3 tools/testing/tts_clone.py
    python3 tools/testing/tts_clone.py --beat beat-04
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BEATS_DIR = REPO_ROOT / "docs/devpost/figures/_demo-run/beats"
NAR_DIR   = REPO_ROOT / "docs/devpost/figures/_demo-run/narration"
VOICE_SAMPLE = Path("/Users/gilraitses/pax/voice/voiceoversample.mp3")
VOICE_REF    = NAR_DIR / "voice_ref.wav"

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

# Canonical claim-gated narration (matches the shipped audio). Hard technical
# nouns are spelled phonetically so XTTS pronounces them correctly: a 2026-06-26
# Whisper transcription of the prior take heard "DynamoDB" as "dynamite",
# "negative binomial" as "benignomy", "phase-shuffle" as "face shuffle", and
# garbled the comma-list of stack names in beat-08. Spellings below fix those.
NARRATION: dict[str, str] = {
    "beat-01": (
        "Wildlife forecasts usually show a confident map that hides how thin the evidence is. "
        "For endangered orcas watched from shore and kayak, that's misleading. "
        "Orcast always shows the forecast — but only the confidence its gates have earned."
    ),
    "beat-02": (
        "Every cell traces back to the kernels, gate verdicts, and detections that earned it. "
        "Each claim is tied down to its evidence. No number floats free. "
        "Outside the pilot region, it says so honestly."
    ),
    "beat-03": (
        "These are fitness gates on a negative binomial model: "
        "a phase shuffled null test, held-out skill, and calibration. "
        "When skill is negative, the displayed confidence is zero. "
        "That's the honest answer, not a broken system."
    ),
    "beat-04": (
        "Central Casting plans which panels to open before narration — "
        "the same prepare-then-narrate pattern, keyed to the surface planner. "
        "The orchestrator dispatches only allow-listed, verified skills. "
        "Every claim is bound to its producing skill and artifact."
    ),
    "beat-05": (
        "Sighting check separates what the temporal model knows "
        "from whether your dorsal fin was an orca. "
        "It's grounded in the same gates — not a yes-or-no oracle."
    ),
    "beat-06-journal": (
        "Field notes stay private in a per-user journal in Dynamo D B until you publish. "
        "Shore reports hit a moderation queue. "
        "Signed-in reviewers approve before low-weight attribution."
    ),
    "beat-06-moderation": (
        "One click. The decision record is immutable. "
        "That approval lives in Dynamo D B, alongside every gate verdict."
    ),
    "beat-07": (
        "Dynamo D B is the backbone — nine on-demand tables, "
        "including the managed-agent registry. The approval I just made lives here."
    ),
    # Natural prose, not a terse proper-noun list: the list form made XTTS
    # hallucinate (doubled the closing word, inserted filler). Framework names
    # are generalized to ones XTTS pronounces cleanly; the diagram carries detail.
    "beat-08": (
        "The whole stack is auditable end to end. "
        "A web frontend on Vercel. A Python service on App Runner. "
        "Dynamo D B is the system of record. "
        "Step Functions orchestrates the agents, and Bedrock narrates sighting triage. "
        "Orcast is a forecast you can use in the field, and defend in public."
    ),
}

BEAT_ORDER = [
    "beat-01", "beat-02", "beat-03", "beat-04", "beat-05",
    "beat-06-journal", "beat-06-moderation", "beat-07", "beat-08",
]


def ensure_voice_ref() -> None:
    NAR_DIR.mkdir(parents=True, exist_ok=True)
    if VOICE_REF.exists():
        return
    if not VOICE_SAMPLE.exists():
        print(f"ERROR: voice sample not found at {VOICE_SAMPLE}", file=sys.stderr)
        sys.exit(1)
    print("Extracting 30s mono voice reference clip...")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(VOICE_SAMPLE),
         "-ss", "5", "-t", "30", "-ar", "22050", "-ac", "1",
         str(VOICE_REF)],
        capture_output=True, check=True,
    )
    print(f"  voice_ref.wav ready ({VOICE_REF.stat().st_size // 1024}KB)")


def get_beat_duration(slug: str) -> float:
    webm = BEATS_DIR / f"{slug}.webm"
    if not webm.exists():
        return 20.0
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(webm)],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip() or "20")


def pad_to_duration(src: Path, dest: Path, target_dur: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-af", f"apad=whole_dur={target_dur}",
         "-t", str(target_dur), str(dest)],
        capture_output=True, check=True,
    )


def generate_beat(tts, slug: str) -> None:
    text = NARRATION.get(slug, "")
    if not text:
        print(f"  {slug}: no narration text — skip")
        return

    dur = get_beat_duration(slug)
    print(f"  {slug}: {dur:.0f}s  synthesising...", flush=True)

    raw_wav = NAR_DIR / f"{slug}-cloned-raw.wav"
    final_mp3 = NAR_DIR / f"{slug}-cloned.mp3"

    tts.tts_to_file(
        text=text,
        speaker_wav=str(VOICE_REF),
        language="en",
        file_path=str(raw_wav),
    )

    pad_to_duration(raw_wav, final_mp3, dur)
    raw_wav.unlink(missing_ok=True)
    print(f"  {slug}: OK ({final_mp3.stat().st_size // 1024}KB, padded to {dur:.0f}s)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--beat", help="Single beat slug")
    args = parser.parse_args()

    try:
        from TTS.api import TTS as CoquiTTS
    except ImportError:
        print("ERROR: TTS not installed. Run: source .venv-tts/bin/activate", file=sys.stderr)
        return 1

    ensure_voice_ref()

    print(f"Loading {MODEL} (downloads ~1.8GB on first run)...")
    # Suppress the Coqui license prompt for automated runs
    import os
    os.environ.setdefault("COQUI_TOS_AGREED", "1")
    tts = CoquiTTS(MODEL, progress_bar=True)

    beats = [args.beat] if args.beat else BEAT_ORDER
    print(f"\nGenerating {len(beats)} beat narrations (your voice)...")
    for slug in beats:
        generate_beat(tts, slug)

    print(f"\nCloned narrations → {NAR_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
