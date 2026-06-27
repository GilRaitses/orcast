#!/usr/bin/env python3
"""Generate per-beat narration audio.

Mode A (default): OpenAI TTS-1 with voice cloning from pax/voice/voiceoversample.mp3
Mode B (--edge):  Microsoft Edge TTS (AriaNeural), no key needed

Usage:
    python3 tools/testing/tts_narrate.py               # OpenAI voice clone
    python3 tools/testing/tts_narrate.py --edge        # Edge TTS fallback
    python3 tools/testing/tts_narrate.py --beat beat-01
    python3 tools/testing/tts_narrate.py --list-voices
"""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BEATS_DIR = REPO_ROOT / "docs/devpost/figures/_demo-run/beats"
NAR_DIR   = REPO_ROOT / "docs/devpost/figures/_demo-run/narration"
VOICE_SAMPLE = Path("/Users/gilraitses/orcast/voice/voice sample.mp3")
VOICE_REF    = NAR_DIR / "voice_ref.wav"   # 30s mono reference for cloning
CREDS        = REPO_ROOT / ".agent-credentials.env"

NARRATION: dict[str, str] = {
    "beat-01": (
        "Wildlife forecasts usually show a confident map that hides how thin the evidence is. "
        "For endangered orcas watched from shore and kayak, that's misleading. "
        "orcast always shows the forecast, but only the confidence its gates have earned."
    ),
    "beat-02": (
        "Every cell traces back to the kernels, gate verdicts, and detections that earned it. "
        "Each claim is bound to its evidence. No number floats free. "
        "Outside the pilot region it says so honestly."
    ),
    "beat-03": (
        "These are fitness gates on a negative-binomial fit. "
        "Phase-shuffled null tests, held-out skill, calibration. "
        "When skill is negative, displayed confidence is zero. "
        "That's the honest answer, not a broken system."
    ),
    "beat-04": (
        "Central Casting plans which panels to open before narration. "
        "Same prepare-then-narrate pattern, keyed surface planner. "
        "The orchestrator dispatches only allow-listed, tier-verified skills. "
        "Every claim is bound to its producing skill and artifact."
    ),
    "beat-05": (
        "Sighting check separates what the temporal model knows "
        "from whether your dorsal fin was an orca. "
        "It's grounded in the same gates, not a yes-or-no oracle."
    ),
    "beat-06-journal": (
        "Field notes stay private in a per-user journal in DynamoDB until you publish. "
        "Shore reports hit a moderation queue. "
        "Signed-in reviewers approve before low-weight attribution."
    ),
    "beat-06-moderation": (
        "One click. The decision record is immutable. "
        "That approval lives in DynamoDB alongside every gate verdict."
    ),
    "beat-07": (
        "DynamoDB is the backbone. Nine on-demand tables including managed agent configs. "
        "The approval I just made lives here."
    ),
    "beat-08": (
        "Vercel frontend, App Runner API, DynamoDB system of record, "
        "Central Casting interactions, Step Functions orchestrator, "
        "Bedrock for sighting narration. "
        "orcast is a forecast you can use in the field and defend in public."
    ),
}

BEAT_ORDER = [
    "beat-01","beat-02","beat-03","beat-04","beat-05",
    "beat-06-journal","beat-06-moderation","beat-07","beat-08",
]


def load_creds() -> dict[str, str]:
    out: dict[str, str] = {}
    if CREDS.exists():
        for line in CREDS.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


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


def extract_voice_ref() -> None:
    """Extract a clean 30s mono 22kHz reference clip for voice cloning."""
    VOICE_REF.parent.mkdir(parents=True, exist_ok=True)
    if VOICE_REF.exists():
        return
    print("  Extracting voice reference clip...")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(VOICE_SAMPLE),
         "-ss", "5", "-t", "30", "-ar", "22050", "-ac", "1",
         str(VOICE_REF)],
        capture_output=True, check=True,
    )
    print(f"  voice_ref.wav ready ({VOICE_REF.stat().st_size//1024}KB)")


def pad_to_duration(src: Path, dest: Path, target_dur: float) -> None:
    """Pad audio with silence or trim to target_dur seconds."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-af", f"apad=whole_dur={target_dur}",
         "-t", str(target_dur),
         str(dest)],
        capture_output=True, check=True,
    )


# ── OpenAI path ────────────────────────────────────────────────────────────

def openai_tts(text: str, out_mp3: Path, api_key: str) -> None:
    """Call OpenAI audio/speech with alloy voice (closest to neutral male)."""
    import urllib.request, json
    body = json.dumps({
        "model": "tts-1-hd",
        "input": text,
        "voice": "alloy",
        "response_format": "mp3",
        "speed": 0.95,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        out_mp3.write_bytes(resp.read())


def process_beat_openai(slug: str, api_key: str) -> None:
    text = NARRATION.get(slug, "")
    if not text:
        print(f"  {slug}: no narration, skip")
        return
    dur = get_beat_duration(slug)
    print(f"  {slug}: {dur:.0f}s  generating via OpenAI TTS-1-HD...", flush=True)
    raw = NAR_DIR / f"{slug}-raw.mp3"
    final = NAR_DIR / f"{slug}.mp3"
    openai_tts(text, raw, api_key)
    pad_to_duration(raw, final, dur)
    raw.unlink(missing_ok=True)
    print(f"  {slug}: OK ({final.stat().st_size//1024}KB)")


# ── Edge TTS path ───────────────────────────────────────────────────────────

async def edge_tts_generate(text: str, out: Path, voice: str, rate: str) -> None:
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(str(out))


async def process_beat_edge(slug: str, voice: str, rate: str) -> None:
    text = NARRATION.get(slug, "")
    if not text:
        print(f"  {slug}: no narration, skip")
        return
    dur = get_beat_duration(slug)
    print(f"  {slug}: {dur:.0f}s  generating via Edge TTS...", flush=True)
    raw = NAR_DIR / f"{slug}-raw.mp3"
    final = NAR_DIR / f"{slug}.mp3"
    await edge_tts_generate(text, raw, voice, rate)
    pad_to_duration(raw, final, dur)
    raw.unlink(missing_ok=True)
    print(f"  {slug}: OK ({final.stat().st_size//1024}KB)")


# ── Coqui XTTS-v2 path (local voice clone, no API key) ──────────────────────

XTTS_CLI = REPO_ROOT / ".venv-tts/bin/tts"
XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def coqui_xtts(text: str, out_wav: Path, ref_wav: Path) -> None:
    """Synthesize text with a cloned voice via the local Coqui XTTS-v2 CLI."""
    env = {**os.environ, "COQUI_TOS_AGREED": "1"}
    subprocess.run(
        [str(XTTS_CLI), "--model_name", XTTS_MODEL,
         "--text", text,
         "--speaker_wav", str(ref_wav),
         "--language_idx", "en",
         "--out_path", str(out_wav)],
        capture_output=True, check=True, env=env,
    )


def process_beat_xtts(slug: str) -> None:
    text = NARRATION.get(slug, "")
    if not text:
        print(f"  {slug}: no narration, skip")
        return
    dur = get_beat_duration(slug)
    print(f"  {slug}: {dur:.0f}s  generating via Coqui XTTS-v2 (cloned)...", flush=True)
    raw = NAR_DIR / f"{slug}-raw.wav"
    final = NAR_DIR / f"{slug}.mp3"
    coqui_xtts(text, raw, VOICE_REF)
    pad_to_duration(raw, final, dur)
    raw.unlink(missing_ok=True)
    print(f"  {slug}: OK ({final.stat().st_size//1024}KB)")


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xtts", action="store_true",
                        help="Use local Coqui XTTS-v2 voice clone (default; no API key)")
    parser.add_argument("--openai", action="store_true",
                        help="Use OpenAI TTS-1-HD (requires OPENAI_API_KEY)")
    parser.add_argument("--edge", action="store_true",
                        help="Use Edge TTS (no API key needed)")
    parser.add_argument("--voice", default="en-US-AriaNeural",
                        help="Edge TTS voice (--edge mode only)")
    parser.add_argument("--rate", default="+0%",
                        help="Speaking rate e.g. +10%%")
    parser.add_argument("--beat", help="Generate a single beat slug only")
    parser.add_argument("--list-voices", action="store_true")
    args = parser.parse_args()

    if args.list_voices:
        import edge_tts
        voices = asyncio.run(edge_tts.list_voices())
        for v in voices:
            if "en-US" in v["ShortName"]:
                print(v["ShortName"], v["Gender"])
        return 0

    NAR_DIR.mkdir(parents=True, exist_ok=True)
    beats = [args.beat] if args.beat else BEAT_ORDER

    if args.edge:
        print(f"Edge TTS mode ({args.voice})")
        async def run_all():
            for slug in beats:
                await process_beat_edge(slug, args.voice, args.rate)
        asyncio.run(run_all())
    elif args.openai:
        creds = load_creds()
        api_key = os.environ.get("OPENAI_API_KEY") or creds.get("OPENAI_API_KEY", "")
        if not api_key:
            print("ERROR: OPENAI_API_KEY not set. Run: bash tools/testing/set_openai_key.sh", file=sys.stderr)
            return 1
        print("OpenAI TTS-1-HD mode (alloy voice, natural neutral)")
        for slug in beats:
            process_beat_openai(slug, api_key)
    else:
        # Default: local Coqui XTTS-v2 voice clone
        if not XTTS_CLI.exists():
            print(f"ERROR: Coqui CLI not found at {XTTS_CLI}", file=sys.stderr)
            return 1
        if not VOICE_SAMPLE.exists():
            print(f"ERROR: voice sample not found at {VOICE_SAMPLE}", file=sys.stderr)
            return 1
        extract_voice_ref()
        print(f"Coqui XTTS-v2 mode (cloned from {VOICE_SAMPLE.name})")
        for slug in beats:
            process_beat_xtts(slug)

    print(f"\nNarration files → {NAR_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
