# BST-ACCEPT verdict, station equipment + POV on the live homepage

Verdict: **PASS**.

## Capture channel

Real GPU on the sanctioned isolated host, not SwiftShader.

- Host: `aimez-gpu-capture` EC2 `i-0e66ac03c729ebe02`, us-east-1 (Tesla T4).
- Driver: `infra/render_host/render.sh` over SSM + S3, `ORCAST_GL=gpu`.
- Renderer string on every frame: `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL ES 3.2)`.
- `canvas: true`, `errorCount: 4` on each frame. The 4 errors are backend `500`s from
  the same-origin proxy because the host dev server has no `ORCAST_API_BASE`. The scene
  falls back to the baked `STATION_CATALOG`, so the captures use the real station data.

## Frames (in this folder)

1. `01_orcasound_lab_cabled.png` route `/?station=48.5583362,-123.1735774,Orcasound%20Lab`
2. `02_north_sjc_mooring.png` route `/?station=48.591294,-123.058779,North%20San%20Juan%20Channel`
3. `03_andrews_bay_cabled.png` route `/?station=48.5500299,-123.1666492,Andrews%20Bay`
4. `04_orcasound_lab_topdown_pov.png` route `/?station=48.5583362,-123.1735774,Orcasound%20Lab&view=topdown`

## Capture-param note

The dispatch listed North SJC and Andrews Bay coordinate-only. The `?station` parser
defaults a nameless hook to the legend name "Orcasound Lab", which would mislabel the
legend for those two nodes. I appended the correct node name to each so the captured
legend is honest. The audio binding and node class resolve from the nearest catalog
coordinates either way, so this changed only the displayed name, not the resolved node.

## Read-examination findings

1. Correct modeled equipment variant per node, on the seabed at the right spot. CONFIRMED.
   - Orcasound Lab (frame 1) legend reads `modeled: cabled equipment mesh · acoustic
     inference · 3D placement`; a gold cabled surface float and its tether are visible in
     the water at the station.
   - North SJC (frame 2) legend reads `modeled: mooring equipment mesh · 3D placement`.
   - Andrews Bay (frame 3) legend reads `modeled: cabled equipment mesh · 3D placement`.
   Honest caveat: the cabled-vs-mooring mesh silhouette is subtle at the dive-in scale, but
   the node-class assignment and modeled label travel correctly per node (cabled for
   orcasound-lab/andrews-bay, mooring for north-sjc) per the catalog.

2. POV selector works. CONFIRMED. Frame 1 shows `Hydrophone POV` active and a low
   dive-in framing; frame 4 (`?view=topdown`) shows `Top-down` active and the camera
   reframed to the elevated orbit context. The selector toggled and the framing changed.

3. Clip-less nodes show live-listen only with NO invented audio. CONFIRMED.
   Both North SJC and Andrews Bay show the chip `Live-listen only`, `No archived clip bound
   for this station.`, `Audio: Orcasound (CC BY-NC-SA 4.0)`, `Live-listen (Orcasound)`, and
   the legend line `live-listen only · no archived clip to scrub`. Neither frame renders a
   STFT spectrogram HUD or an estimate/SRKW chip, and no reenactment count is claimed. The
   clip-bound Orcasound Lab (frame 1) is the only node that bakes the spectrogram + estimate
   chip + `orcas shown: 1 · presence-gated`.

   A faint thin shape mid-left appears in these frames AND in the no-slice homepage baseline,
   so it is pre-existing ambient twin content, not a slice-spawned orca at a clip-less node.

## Defects

None. No fix applied in the BST scope.

## Note on the cross-lane blocker

The homepage was crashing for all lanes before this gate (see the consolidated report):
a module-load forbidden-claim guard in the BSH-owned `interpretiveOceanLayer.ts` threw on
its own negated copy. I fixed that copy (label-only) so the scene mounts. BST frames were
captured after that fix.

## Commit gate

Nothing committed or pushed.
