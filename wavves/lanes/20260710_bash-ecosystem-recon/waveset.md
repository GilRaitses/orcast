# BREC waveset

One wave, one subagent, no parallelism needed (transcription + one synthesis
pass is inherently sequential). This lane is scoped to *recon only*: it
produces a findings doc, not code, not a port of `HUNT` onto Bash.tv.

## Wave BREC-W1 — transcribe + capability recon

**Owner:** one `generalPurpose` subagent, run in background (media
processing + a web-search pass will take several minutes).

**Steps, in order:**

1. Install a local speech-to-text tool. `whisper-cpp` is available via
   Homebrew (bottled, confirmed present in the formula index) but requires a
   separately downloaded GGML model file. Use the `base.en` model (good
   speed/accuracy tradeoff for English tech narration, ~148MB) from
   `https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin`.
   If `whisper-cpp` install or model download fails for any reason (network,
   disk, brew), fall back to `pip3 install -U openai-whisper` (note: repo
   Python is 3.14, this may hit a torch wheel incompatibility; if so, try
   `pip3 install -U faster-whisper` next). Record whichever path actually
   worked in the findings doc's methodology note. Do not silently give up on
   transcription; if every local option fails, say so explicitly in the
   findings doc rather than fabricating video content from the filename
   alone.
2. Extract mono 16kHz WAV audio from both videos via `ffmpeg` (already
   confirmed installed at `/opt/homebrew/bin/ffmpeg`):
   - `/Users/gilraitses/pax/bash/Bash Walkthrough.mov` (228s)
   - `/Users/gilraitses/pax/bash/Bash-Stream Clip.mov` (736s)
3. Run the transcription tool on both extracted WAVs. Write raw transcripts
   to `wavves/lanes/20260710_bash-ecosystem-recon/transcripts/walkthrough.txt`
   and `stream-clip.txt`.
4. Read `/Users/gilraitses/pax/bash/Bash_Hackathon_Guide.pdf` in full (the
   `Read` tool converts PDF text automatically).
5. Do 2-4 targeted web searches on the live Bash.tv product (e.g. "Bash.tv
   hackathon platform capabilities", "Bash.tv agent orchestration",
   "Bash.tv import github repo") to catch anything the video/PDF gloss over
   or that has changed since they were recorded. Prefer the transcripts and
   PDF as primary sources; use web search only to fill gaps or resolve
   ambiguity, and say explicitly in the findings doc when a claim comes from
   web search rather than the primary sources.
6. Cross-read all sources and write the single deliverable,
   `findings/BREC-capabilities.md`, structured as:
   - **Execution model**: single agent in one chat loop vs. multi-agent /
     background / parallel subagent support. State plainly whether anything
     like this repo's `wavves` orchestration (parallel Task subagents,
     background dispatch, a registry of concurrent lanes) is possible on
     Bash.tv, or whether every build step must be a single sequential prompt
     to one agent. Cite the transcript timestamp or PDF page/section for
     every claim.
   - **Code import**: can an existing repo (or a zip/set of files) be
     brought into a Bash.tv workspace pre-written, or must everything be
     generated fresh by prompting the in-VM agent? If import is possible,
     state the exact mechanism (git clone command available in-VM? file
     upload UI? paste-into-chat only?) and any size/file-count/dependency
     constraints mentioned.
   - **Runtime/stack constraints**: language/framework the Bash.tv VM
     supports, whether npm/pip packages can be installed, whether WebGL/
     Three.js-class 3D rendering is supported and performant, internet
     access from inside the VM, persistence between sessions.
   - **Import plan for THIS repo's HUNT deliverable**: a concrete list of
     what from `web/lib/scene/{orcaPilot,boats,sonar}/`,
     `web/lib/scene/orca/`, `web/lib/geo/gazetteer.ts`, and the tileset/
     bathymetry stack (`web/lib/scene/tiles/useTilesLayer.ts`) is realistically
     importable as-is vs. must be re-specified as prose in the existing
     `docs/devpost` or hackathon build-prompt package for a fresh in-VM
     build. Do not assume; base this section only on what Steps 1-5
     actually established.
   - **Open questions**: anything the transcripts/PDF/web search left
     genuinely unresolved, flagged for the operator, not guessed at.

**Acceptance for this wave:** `findings/BREC-capabilities.md` exists, every
factual claim in it cites a transcript timestamp, PDF location, or is marked
`[web search]`, and the "Open questions" section is non-empty only if real
ambiguity remains (an empty section claiming full certainty on a brand-new
platform would itself be a red flag).

## Out of scope for BREC

- No decision-making about whether/how to actually port `HUNT` to Bash.tv.
  That is a follow-on `/mod-decide` or `/charter` once this recon lands.
- No code changes anywhere in `orcast`.
- No modification of the source videos/PDF.
