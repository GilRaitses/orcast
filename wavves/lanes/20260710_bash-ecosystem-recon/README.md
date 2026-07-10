# BREC: bash-ecosystem-recon

Single-wave recon lane. Goal: transcribe the two local Bash.tv videos, cross-read
them against `Bash_Hackathon_Guide.pdf`, and confirm or refute the operator's
working hypotheses about the Bash.tv build environment before any porting
decision is made:

- Is execution on Bash.tv a single agent operating straight out of a chat
  playbook, or does it support parallel subagents / deep orchestration
  (i.e. can the `wavves` model used in this repo run there at all)?
- Can an existing GitHub repo (or parts of one, e.g. this `orcast` tree) be
  imported into a Bash.tv workspace, and if so how (git clone in-VM? file
  upload? none of the above)?
- What are the concrete capability/limitation boundaries (language/runtime,
  internet access, persistent storage, external npm packages, 3D/WebGL
  support) that determine what of `HUNT`'s delivered code can actually ship
  on that platform vs. what must be rebuilt as a from-scratch prompt.

Inputs (read-only, not modified by this lane):

- `/Users/gilraitses/pax/bash/Bash Walkthrough.mov` (228s)
- `/Users/gilraitses/pax/bash/Bash-Stream Clip.mov` (736s, likely contains the
  Q&A the operator referenced)
- `/Users/gilraitses/pax/bash/Bash_Hackathon_Guide.pdf`

Files:

- `waveset.md` - the lane's authority doc.
- `dispatch.md` - the fenced paste block for the dispatched subagent.
- `transcripts/` - raw transcription output per video.
- `findings/BREC-capabilities.md` - the reconciled capability/limitation
  matrix and import plan (the actual deliverable).

Status: chartered, dispatching now. See `wavves/registry.yml` (code `BREC`).
