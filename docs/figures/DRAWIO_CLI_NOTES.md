# draw.io Desktop CLI — Export Notes

Binary: `/opt/homebrew/bin/drawio` (Electron app, draw.io Desktop).
Invoke exports with `-x` (export). Format is taken from the `-o` extension, or `-f`.
All findings below were verified against a copy of a real figure
(`fig-08-architecture/figure.drawio`) plus synthetic test files. No original
files were modified.

## Flag reference

| Flag | Effect | Recommended? |
|------|--------|--------------|
| `-x, --export` | Required to export (vs. open GUI) | Yes — always |
| `-o, --output <file>` | Output path; extension sets format | Yes — always |
| `-f, --format <pdf\|png\|jpg\|svg\|xml>` | Explicit format; ignored if `-o` has an extension | Optional |
| `-s, --scale <n>` | Linear resolution multiplier. 1→1382×942, 2→2762×1882, 4→5522×3762 on the test figure | Yes — use `2` for whitepaper PNG |
| `--width <px>` | Fit output to exact width, preserves aspect (2000→2000×1364). Overrides `-s` for sizing | Use when you need an exact pixel width |
| `--height <px>` | Fit output to exact height, preserves aspect | Situational |
| `--crop` | Crops PDF to diagram bounds. **PDF only** — removes page whitespace (1050×763pt → 994×678pt). No effect on PNG (PNG already crops to content) | Yes — for PDF |
| `-b, --border <n>` | Uniform margin around diagram. At scale 2: `-b 10`→+15px/side, `-b 20`→+30px/side (scales with output) | Optional, `10`–`20` for breathing room |
| `-t, --transparent` | Transparent-background PNG (pix_fmt rgba). Without it, PNG bg is solid white (rgb24) | No for whitepaper (want white); Yes for overlays |
| `-e, --embed-diagram` | Embeds editable source copy into PNG/SVG/PDF | Optional (provenance) |
| `--embed-svg-images` | Inlines raster images into SVG | Yes if SVG has bitmaps |
| `--embed-svg-fonts <bool>` | Embed fonts in SVG (default true) | Keep default true |
| `-q, --quality <n>` | JPEG quality (default 90). JPEG only | Only if exporting JPEG |
| `-a, --all-pages` | Export all pages (PDF only) | Multi-page PDF |
| `-p, --page-index <n>` | Export one page (1-based) | Multi-page files |
| `-g, --page-range <a>..<b>` | Page range (PDF only) | Multi-page PDF |
| `-l, --layers <i,j>` | Export selected layer indexes | Layered diagrams |
| `--svg-theme <dark\|light\|auto>` | SVG theme (default auto) | Use `light` for print |
| `-u, --uncompressed` | Uncompressed XML output (XML format only) | Debugging |
| `-z, --zoom <n>` | Scales the app UI, **not** the export | No — does not affect output |
| `--enable-plugins` | Enable plugins | No |

## Recommended commands

### Crisp, tight, white-background ~2x PNG (whitepaper)
```bash
drawio -x -f png -s 2 -b 10 -o out.png input.drawio
```
- `-s 2` gives ~2.7k-px-wide, sharp output.
- PNG is already cropped to content bounds (no page whitespace), so `--crop` is unnecessary.
- No `-t`, so the background is solid white (rgb24) — correct for print.
- `-b 10` adds a small uniform margin; drop it if you want zero border.

### Vector PDF (tightly cropped)
```bash
drawio -x -f pdf --crop -o out.pdf input.drawio
```
- `--crop` is essential for PDF: it trims the fixed page margins down to the diagram bounds.

### Vector SVG
```bash
drawio -x -f svg --svg-theme light --embed-svg-fonts true -o out.svg input.drawio
```
- SVG is scale-independent (always 1× viewBox). Default background is transparent;
  set a white rect in the diagram or composite if you need an opaque print SVG.
- `--svg-theme light` avoids dark-mode color shifts.

## Auto-layout / fit-to-content

- There is **no auto-layout** (no graph re-layout / arrange) in the CLI.
- "Fit page to content" is handled by output bounds:
  - **PNG/JPG/SVG**: always exported at the diagram's content bounding box — excess
    whitespace is automatically removed. `--crop` is a no-op for these.
  - **PDF**: defaults to page-sized output with margins; use `--crop` to fit the page
    to content.

## Gotchas

- **`id="null"` silently drops cells (verified).** A cell whose `id` is the literal
  string `null` is omitted from the export with **no error**. Test result:
  - Control file (valid ids), two stacked cells → `325×365` px (both rendered).
  - Same file with one cell `id="null"` → `325×125` px (only the valid cell rendered;
    the `id="null"` cell is gone).
  - Fix: never use `null` (or empty) as a cell id; regenerate ids before export.
- `--crop` does nothing for PNG/SVG (already content-cropped) — only meaningful for PDF.
- `-z/--zoom` scales the app interface, not the export; do not use it for resolution
  (use `-s` or `--width`).
- `--width`/`--height` override `-s` for final sizing (aspect preserved).
- Transparent PNG (`-t`) changes pixel format to rgba; omit it for white-background prints.
- The CLI prints `input -> output` on success; a missing/extra arg yields
  `Error: input file/directory not found`.

## Verified test matrix (test figure)

| Output | Command extras | Result |
|--------|----------------|--------|
| PNG | `-s 1` | 1382×942, rgb24 |
| PNG | `-s 2` | 2762×1882, rgb24 |
| PNG | `-s 4` | 5522×3762, rgb24 |
| PNG | `-s 2 --crop` | 2762×1882 (identical to no-crop) |
| PNG | `-s 2 -b 10` | 2792×1912 |
| PNG | `-s 2 -b 20` | 2822×1942 |
| PNG | `-t -s 2` | 2762×1882, rgba |
| PNG | `--width 2000` | 2000×1364 (aspect preserved) |
| PDF | (default) | MediaBox 1050.96×762.96 pt |
| PDF | `--crop` | MediaBox 994.08×678 pt (tight) |
| SVG | (default) | 1381×941 viewBox, transparent bg |
