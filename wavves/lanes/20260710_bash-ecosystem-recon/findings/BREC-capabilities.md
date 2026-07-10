# BREC capabilities recon: Bash.tv execution model, code import, and HUNT portability

Sources: `transcripts/walkthrough.vtt` (228s, cited as `mm:ss` from video start),
`transcripts/stream-clip.vtt` (736s, cited as `mm:ss` from video start),
`Bash_Hackathon_Guide.pdf` (13 slides, cited as `p.N`), and four targeted web
searches, each marked `[web search: "<query>"]`.

## Methodology

The primary transcription path worked on the first attempt. `brew install
whisper-cpp` installed version 1.9.1 with its CLI binary at `whisper-cli`
(the formula does not install a binary literally named `whisper-cpp` or
`main`). The `ggml-base.en.bin` model downloaded from the Hugging Face URL
given in the dispatch at 147,964,211 bytes, matching the expected ~148MB.
`ffmpeg -i <input> -ar 16000 -ac 1 -c:a pcm_s16le <output.wav>` extracted mono
16kHz WAV audio from both `.mov` files without error. `whisper-cli -m
models/ggml-base.en.bin -f <wav> -otxt -ovtt` produced a full transcript for
each file in under thirty seconds of processing time, with timestamped
segments in the `.vtt` output. No fallback to `openai-whisper` or
`faster-whisper` was needed. Both raw transcripts are stored as plain text
(`transcripts/walkthrough.txt`, `transcripts/stream-clip.txt`) and as
timestamped VTT (`transcripts/walkthrough.vtt`, `transcripts/stream-clip.vtt`);
this findings doc cites the VTT timestamps.

## Update — operator-provided primary source (Discord Q&A, Sup Team, live stream)

After this lane's initial synthesis, the operator supplied a direct transcript
of a Bash.tv FAQ doc plus a live-stream Q&A with the Sup Team (the platform's
own builders) that this lane's video/web-search recon did not have access to.
This is a higher-confidence primary source than either video or a web search
(it is the platform team answering platform questions directly, unfiltered by
third-party search-index gaps) and it resolves several items the sections
below originally left open. Where it contradicts or resolves a claim made
from the video/PDF/web-search evidence, the resolution below **supersedes**
the earlier claim; the earlier claim is left in place further down for the
audit trail, marked accordingly.

- **Code import — RESOLVED, contradicts the earlier "not confirmed or
  denied" answer.** Sup Team, verbatim: "is it the same with importing code?
  or is it all vibe coding? — you can do that too or if its a public github
  link you can give it the link and it can reference it." This confirms two
  distinct import paths: (1) attaching code files directly (not just images —
  contradicts this lane's earlier inference from the stream clip, which only
  showed image/art attachment and left non-image files unconfirmed), and (2)
  giving the agent a **public GitHub repo URL** for it to reference directly,
  with no attachment step at all. **`orcast` is itself a public GitHub repo**
  (`https://github.com/GilRaitses/orcast`, confirmed via `gh repo view`), so
  this second path is directly usable for the HUNT deliverable: the Bash.tv
  build prompt can simply give the agent the repo URL and name exact paths
  (`web/lib/geo/gazetteer.ts`, `web/public/orca/orca.glb`, etc.) instead of
  re-describing everything from scratch in prose. Whether the agent treats a
  referenced GitHub link as literal source it copies or as read-only context
  it reads and reimplements from is still not stated explicitly by the FAQ
  text, so treat "reference" as reading/informing generation, not a
  guaranteed verbatim import, and keep a described-from-prose fallback for
  anything load-bearing.
- **File contribution beyond images — RESOLVED.** Sup Team, verbatim: "how do
  we contribute art to these projects? does everything need to be generated?
  — you can add files to the agent and it can add them to the app." This is
  broader than "attach an image for debugging" (the only use shown in the
  stream clip): general files can be added and incorporated into the running
  app, not just referenced for visual debugging context.
- **Code export — NEW, not covered by video/PDF/web search at all.** The FAQ
  doc states plainly: "I want to download the project. — 'Create a zip of
  the project and give me a link to download it.' This packages the current
  project files into a downloadable archive." Confirms a way to get a
  finished Bash.tv build's code back out, relevant if the operator wants the
  Bash.tv-built version reintegrated into `orcast` afterward.
- **Execution model — REFINED, does not overturn the "serial queue, one
  agent per space" finding, but adds a real parallelism option this lane
  missed.** Direct Q&A: "with it being multiplayer can people run parallel
  runs working on different parts of the app? — It runs in queue but you can
  experiment with working from two bashes at once." This confirms: within
  ONE space/bash, prompts still process one at a time in a queue (matching
  this lane's original finding below), but an operator can open a SECOND,
  independent bash (space) and work in both concurrently. This is manual,
  operator-driven parallelism across separate VMs/spaces, not anything
  resembling in-space multi-agent orchestration or this repo's own `wavves`
  model of one supervisor dispatching many concurrent subagents in one
  workspace. Still no mechanism exists for a single space's agent to fan out
  work to helper agents on its own.
- **Version control — NEW.** FAQ: "'Initialize a Git repository and commit
  after every round of changes.' This creates a checkpoint after every
  iteration, making it easy to review changes or roll back." A prompt-level
  instruction, not an automatic default; must be requested explicitly in the
  first prompt to get commit checkpoints.
- **Reusable Skills — NEW, partially resolves the earlier "what does Skills
  actually do" open question.** FAQ: "'Create an agent Skill for this
  workflow.' The agent can generate reusable skill instructions instead of
  you having to set them up manually." This describes Skills as agent-
  generated reusable prompt/instruction templates, not a code or plugin
  injection point — though this is the FAQ's framing of authoring a Skill,
  not confirmation of what an *uploaded* Skill file's internal format is,
  so the PDF's separate "upload Skills" (`p.8`) mechanism is still not fully
  specified.
- **Internet-context links — NEW.** FAQ: "'Use the following links as
  reference material for this project:' Then include documentation, GitHub
  repositories, articles, or videos." Confirms the agent can be pointed at
  arbitrary external URLs (not just GitHub) as reference material, e.g. the
  bathymetry tileset's own documentation could be linked this way if useful.
- **OpenRouter model/image access — NEW.** FAQ confirms an OpenRouter key can
  be supplied for (a) image generation with a named model, or (b) broader
  AI-feature/model access beyond Bash.tv's built-in 260+ model list. Relevant
  only if higher-fidelity generated art (boat textures, splash sprites) is
  wanted beyond default code-driven placeholder geometry; not required for
  HUNT's core mechanics.
- **Model/thinking-level switching — NEW, direct credit-discipline lever.**
  FAQ confirms the model AND the reasoning/thinking level can both be changed
  per-prompt within one session, and that mixing tiers across a build (not
  using one config start-to-finish) can be both cheaper and better.
- **Docs/getting-started page — RESOLVED (does not exist yet).** Q&A: "Is
  there a bash.tv/docs or getting started page? — We are working on it! In
  the meantime, you can ask any questions in the ❓-questions forum or tag
  @Sup Team." Confirms this lane's own finding that Bash.tv has almost no
  independent public documentation is not a search-gap artifact — the
  platform team confirms no docs page exists yet.
- **Platform logistics (not build-relevant, recorded for completeness):**
  fully web-based, a Chromebook is sufficient; access opens Friday (today);
  access does not lapse after the event and comes with invites to share;
  losing/keeping projects is not addressed but a feed/browse page exists to
  see other public builds; four example builds were shared:
  `https://bash.tv/p/iyq5qttx7jeoyr1mzv4ii/3000?__preview=1`,
  `https://bash.tv/p/iayog7la368hwr23ao2pi/8123?__preview=1`,
  `https://bash.tv/p/isznrtke2gc5woazl1eqv/3000?__preview=1`,
  `https://bash.tv/p/ix9oqa3u1dasl30xo5wve/3000?__preview=2`.

## Execution model

The video and PDF sources describe a single agent per space, driven by a
serial prompt queue, with no support shown or described for background,
parallel, or multi-agent orchestration inside one space.

Every reference to the builder in the PDF is singular. The Agent Prompt Box
is called "the primary interface for giving instructions to the AI agent"
(`p.9`), and the Create a New Space feature sets "permissions for who can
interact with the agent" (`p.6`), not agents. Advanced Settings exposes one
agent's message detail level, one History, and one set of Metrics such as
CPU and memory usage (`p.8`), consistent with one VM and one agent process
per space rather than a pool of coordinated workers.

The walkthrough shows the queue mechanism directly. After the presenter
submits a build prompt, he narrates: "if someone gets another idea, they can
just type it in here and their prompt enters a queue" (`02:56-03:07`,
`walkthrough.vtt`). This describes multiple humans submitting prompts to one
agent, which processes them one after another, not multiple agents working
different prompts at once. The same segment shows the agent finishing one
full build (a 3D zoo-enclosure game) before the preview updates
(`03:01-03:07`).

The stream clip adds VM-lifecycle detail but no orchestration detail. The
host says, of a different space's agent taking a moment to respond: "they're
running in like their own little machine, their own little virtual machine,
if they haven't been started in a while, they take a second, but when they
are active, they just come on right away" (`04:21-04:38`,
`stream-clip.vtt`). This confirms one VM per space with idle/wake behavior,
not multiple concurrent agents inside a single space's VM.

No claim in any of the three sources describes background task dispatch, a
supervisor delegating to specialist workers, or anything resembling this
repo's `wavves` registry of concurrently running Task subagents.
`[web search: "Bash.tv agent orchestration parallel agents multi-agent"]`
returned no Bash.tv-specific results at all; the results were generic
third-party tmux-based multi-agent orchestration tooling (TACO, CAO,
agentorchestr) unrelated to Bash.tv, which is itself evidence that no public
documentation ties Bash.tv to any multi-agent execution model.

**Plain answer:** every build step is a single sequential prompt to one
agent in one queue, per space. There is no evidence in any source, including
web search, of parallel or background subagent support *within* a space. See
"Update — operator-provided primary source" above: an operator can run two
independent spaces ("bashes") concurrently, but that is manual cross-space
parallelism, not in-space multi-agent orchestration.

## Code import

None of the three sources describe a git-clone-in-VM mechanism or a
pre-written-repo import feature. What all three sources do establish is a
file/asset attachment path into the running agent chat, with concrete size
limits, that is demonstrated for images rather than for a source tree.

The walkthrough shows an "attached file icon where you can attach files" in
the Agent Prompt Box (`01:47-01:52`, `walkthrough.vtt`), matching the PDF's
"you can attach files" under Feature #7 (`p.9`).

The stream clip shows this mechanism used twice, both times for images, not
code. First, when the host hit a rendering bug in a small game: "I was
running into some issues where it was rendering strangely. So I dropped at
some images and I had it work out those issues for me" (`05:37-05:45`,
`stream-clip.vtt`, transcript verbatim, likely a mis-transcription of
"dropped in"). Second, for original art assets, the host calls this "kind
of the most powerful flow there is" (`06:55-07:00`, `stream-clip.vtt`):
someone "drew all these kind of sprites herself... and then would copy them
in and then was loading them into the kind of editor" (`07:02-07:13`,
`stream-clip.vtt`).

A direct audience question establishes the size ceiling: "Is there a size
limitation right now? ... you can do 10 files at once ... I think we let you
upload one gigabyte per like batch but the space itself won't be limited...
practically I think it might tap out like a hundred gigs or something"
(`10:30-10:50`, `stream-clip.vtt`). This is the only quantitative constraint
found in any source: ten files per upload batch, one gigabyte per batch, and
an informal total-space ceiling the speaker estimates near a hundred
gigabytes.

Nothing in the PDF, either transcript, or web search states whether an
attached non-image file, such as a `.ts` source file or a `.zip` of a
repository, is treated as literal file-tree content the agent writes into
its own build versus a reference image or document the agent reads for
context only. `[web search: "\"bash.tv\" AI app builder import GitHub repo
code upload files"]` returned no Bash.tv-specific result addressing code or
repo import; the closest hits were a third-party tool (Dyad) with an
unrelated GitHub-import feature and a generic git-push tutorial, neither of
which describes Bash.tv.

**Plain answer, as originally established from video/PDF/web-search alone:**
file attachment into an active agent chat is confirmed with stated size and
count limits, and is demonstrated for images and art assets. A git-clone or
pre-written-repo import mechanism is not confirmed or denied by any source
consulted, including web search. **This is superseded by the operator-
provided primary source above:** the Sup Team directly confirms both
non-image file attachment ("you can add files to the agent and it can add
them to the app") and a public-GitHub-link reference path ("if its a public
github link you can give it the link and it can reference it"), the latter
being directly usable here since `orcast` is itself a public GitHub repo.

## Runtime and stack constraints

The walkthrough demonstrates a real-time, camera-controllable 3D preview
built entirely from one natural-language prompt: "I'm having it build me a
3D game set in a zoo enclosure where players are able to get their picture
taken and the game then turns them into animals that inhabit the space"
(`02:35-02:47`, `walkthrough.vtt`), followed by "we can also drag our mouse
to spin the camera around" (`03:07-03:15`) and first-person movement inside
the built scene through `03:43`. This confirms interactive 3D rendering
exists and is responsive in the browser preview, but no source names the
underlying rendering library. The word "WebGL" and the phrase "Three.js" do
not appear in the PDF or either transcript, and no web search targeted this
specifically.

Model choice is per-prompt, not simultaneous: the model selector holds "264
models to build whatever your mind can think of" (`01:57-02:04`,
`walkthrough.vtt`), matching the PDF's "260+ AI models (such as GPT-4 or
Claude)" (`p.9`). Credit consumption scales with the chosen model, and Opus
is called out as expensive (`02:09-02:23`, `walkthrough.vtt`).

The stream clip confirms a second credit-metered capability, image
generation, that draws from the same pool the agent uses: "I integrated it
with the same token pool, or credit pool, that the agent uses. So you can
create images and it'll draw down the credit balance" (`08:42-08:57`,
`stream-clip.vtt`). It also states that most generated projects rely on
code-driven placeholder art rather than image models by default, and that
image generation requires explicitly asking for it (`09:59-10:06`).

Spaces can be public or private, and can move between the two: "you can
make these public or private... maybe like start private, once it feels
good, you can like make it public" (`03:48-04:05`, `stream-clip.vtt`). The
idle/wake VM behavior already cited under Execution model
(`04:21-04:38`) implies a space's build state survives at least a
sleep/wake cycle, since the host describes agents "coming on right away"
once active rather than rebuilding from nothing, though no source states
this in explicit persistence terms.

No source addresses npm or pip package installation directly, and no source
addresses outbound internet access from inside the agent's VM directly.
`[web search: "bash.tv hackathon platform capabilities vibe coding agent"]`
and `[web search: "bash.tv build games apps together real time site review
what is it"]` both returned no additional capability detail; the second
search mostly surfaced an unrelated company of the same name, "BASH TV," a
live fight and event streaming production business at watchbashtv.com, with
no connection to the AI build platform.

## Import plan for this repo's HUNT deliverable

This section is descriptive only, per the lane's scope. It states what
Steps 1 through 5 actually established, not a recommendation to port
anything.

`web/lib/scene/orcaPilot/`, `web/lib/scene/boats/`, `web/lib/scene/sonar/`,
and `web/lib/scene/orca/` total 1,335 lines across eighteen top-level
TypeScript and TSX files, per `wc -l`, not counting the further
`eyes/`, `materials/`, `motion/`, `mouth/`, and `physics/` subdirectories
under `orca/`. All four directories are written against
`@react-three/fiber` and `three`, per `web/package.json`.
None of the three sources confirms a mechanism for carrying an existing
multi-file TypeScript module, with its import graph and npm dependency
list, into a Bash.tv space intact. The only confirmed inbound-file path is
attaching individual files to an agent chat, demonstrated for images and
capped at ten files and one gigabyte per batch (`10:30-10:50`,
`stream-clip.vtt`), and the walkthrough's own build demo was generated from
a text prompt with no uploaded starter code at all (`02:35-02:47`,
`walkthrough.vtt`). Given that, none of these four directories is
established as importable as-is. What is established is that their
behavior, such as the boat spawn and ram-collision rules already documented
in `web/lib/scene/boats/WIRING.md`, could be re-described as prose in a
fresh build prompt for the in-VM agent to regenerate, matching the pattern
the walkthrough itself demonstrates for building a 3D scene from a text
description.

`web/lib/geo/gazetteer.ts` is 700 lines of dependency-free, deterministic
TypeScript, a lookup table and an offline resolver function with no import
of `three` or `react-three-fiber`. It is the most structurally portable of
the five targets named in the waveset in the narrow sense that it does not
require the specific rendering stack. It is still not established as
importable as a file, because no source confirms that an attached non-image
file is written into the build verbatim rather than treated as reference
context.

`web/lib/scene/tiles/useTilesLayer.ts` is 224 lines and is the least
portable of the five. It imports `3d-tiles-renderer`, its plugin classes,
and a Meshopt decoder from `three/addons`, and it fetches a tileset URL over
the network at runtime, per its own header comment describing it as
production wiring for "a real-meters tileset." No source states whether
Bash.tv permits installing an arbitrary npm dependency such as
`3d-tiles-renderer`, or whether its VM can make outbound network requests to
a third-party or Google-hosted tileset endpoint. Absent that confirmation,
this file is not established as portable in any form, verbatim or
re-specified, without first resolving those two open questions.

Across all five targets, the single fact pattern that recurs in every
source is that Bash.tv's demonstrated build flow is prompt-to-generation,
not upload-to-integration. The walkthrough's own zoo-game demo is the clearest
evidence for this: a single natural-language prompt produced a full
playable 3D scene with no code input at all (`02:35-03:19`,
`walkthrough.vtt`).

## Open questions

**Resolved by the operator-provided Discord Q&A (see Update section above),
no longer open:**

- ~~Whether an attached non-image file... is written into the agent's build
  as literal content or is treated as reference-only context.~~ Resolved:
  general file attachment is confirmed to work ("you can add files to the
  agent and it can add them to the app"), and a public GitHub link can
  separately be given for the agent to reference directly.
- ~~Whether a git-clone or GitHub-repo-import mechanism exists.~~ Resolved:
  no git-clone-in-VM specifically, but a public GitHub URL given in the
  prompt/reference-links field is a confirmed, directly usable path for this
  repo (`orcast` is public).
- ~~What the "Skills" feature actually does.~~ Partially resolved: the FAQ
  describes agent-*generated* Skills as reusable instruction/prompt
  templates. The PDF's separate "upload Skills" mechanism (`p.8`) is still
  not fully specified (upload format/effect unconfirmed).

**Still open, not addressed by any source including the new Q&A:**

- Whether npm or pip package installation is exposed to the user or to the
  in-VM agent, or whether the build stack is fixed and sandboxed. Directly
  relevant to `web/lib/scene/tiles/useTilesLayer.ts`'s `3d-tiles-renderer`
  dependency.
- Whether generated code and file state persist verbatim across a space's
  sleep and wake cycle, or whether "waking up" resumes a chat session
  against a freshly reprovisioned VM that regenerates state from the chat
  history. The idle/wake behavior is described (`04:21-04:38`,
  `stream-clip.vtt`) but not its underlying persistence mechanism.
- Whether outbound internet access from inside a space's VM is permitted,
  and if so under what constraints (relevant to fetching the bathymetry
  tileset over the network at runtime).
- What rendering library Bash.tv's generated builds actually use for 3D
  scenes. Interactive 3D rendering is demonstrated (`02:35-03:19`,
  `walkthrough.vtt`) but the underlying library is never named in the PDF,
  either transcript, or the four web searches performed.
- Whether a referenced (not attached) public GitHub link is read literally
  file-by-file, or summarized/sampled by the agent before generation; the
  FAQ confirms the path exists but not its fidelity.
- Bash.tv, the AI build platform from the company Sup, has close to no
  independent public documentation. Three of four web searches surfaced an
  unrelated same-named company, "BASH TV" at watchbashtv.com, a live event
  and fight streaming production business with no connection to the AI
  platform. A direct fetch of `https://bash.tv` timed out. Absent the
  operator-provided Q&A, the PDF and the two supplied videos would be the
  only substantive documentation available for this platform.
