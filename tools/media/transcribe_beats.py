#!/usr/bin/env python3
"""Transcribe each beat voiceover with Whisper to verify the cloned voice is
intelligible and on-topic. Objective accuracy proxy: clean coherent transcript
matching the beat's topic means the clone is usable."""
import os
import sys
import glob
import whisper

NAR_DIR = sys.argv[1] if len(sys.argv) > 1 else "docs/devpost/figures/_demo-run/narration"

model = whisper.load_model("base")

files = sorted(
    f for f in glob.glob(os.path.join(NAR_DIR, "beat-*.mp3"))
    if "-cloned" not in os.path.basename(f)
)

for f in files:
    r = model.transcribe(f, language="en", fp16=False)
    text = " ".join(seg["text"].strip() for seg in r["segments"]).strip()
    nwords = len(text.split())
    # average no-speech prob across segments = rough confidence the model heard speech
    nsp = r["segments"]
    avg_nosp = sum(s.get("no_speech_prob", 0) for s in nsp) / max(len(nsp), 1)
    print(f"\n=== {os.path.basename(f)}  ({nwords} words, avg_no_speech={avg_nosp:.2f}) ===")
    print(text)
