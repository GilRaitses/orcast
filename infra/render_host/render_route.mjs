// Headless render of one orcast sandbox/route on the aimez render host.
// Runs ON the host (aimez-services), driven over SSM by ../render_host/render.sh.
// Uses the repo-local Playwright + the ms-playwright chromium with SwiftShader,
// because the host is CPU-only (no GPU). Software GL is fine for CORRECTNESS
// frames (is the water green, is the orca countershaded); it is NOT a client-tier
// perf measurement (U must be measured on real client GPUs, not here).
//
// usage: node render_route.mjs <route> <outPng> [waitMs]
import pw from '/home/ubuntu/orcast/web/node_modules/playwright/index.js';
const { chromium } = pw;

// Route may come via ORCAST_ROUTE (base64-safe transport from render.sh for
// routes with shell-special chars like ?, &, ,) or argv[2] (back-compat).
const route = process.env.ORCAST_ROUTE || process.argv[2] || '/orca';
const out = process.argv[3] || `/home/ubuntu/orcast/shots/shot${route.replace(/[\/?=&,%]/g, '_')}.png`;
const waitMs = parseInt(process.argv[4] || '9000', 10);
// ORCAST_PERF=1 -> after the settle, sample rAF frame intervals on the host to
// produce an honest frame-time number for the BSH/BRE A/B gates. The T4 is a
// server-class GPU, so treat these as an upper-bound sanity check, not a
// binding client-tier (60fps-desktop / 30fps-laptop) budget.
const measurePerf = process.env.ORCAST_PERF === '1';
const perfSampleMs = parseInt(process.env.ORCAST_PERF_MS || '3000', 10);
// Optional viewport override (default 1280x800) to confirm DOM-overlay layout
// (e.g. whether a HUD legend is occluded at the demo viewport vs missing).
const vw = parseInt(process.env.ORCAST_VW || '1280', 10);
const vh = parseInt(process.env.ORCAST_VH || '800', 10);
const base = process.env.ORCAST_DEV_BASE || 'http://127.0.0.1:3010';
// ORCAST_GL=gpu  -> real GPU via ANGLE/EGL (NVIDIA on the aimez-gpu-capture T4)
// ORCAST_GL=swiftshader (default) -> software GL (CPU host, correctness only)
const glMode = (process.env.ORCAST_GL || 'swiftshader').toLowerCase();
const args = glMode === 'gpu'
  ? ['--use-gl=angle', '--use-angle=gl-egl', '--enable-gpu', '--ignore-gpu-blocklist',
     '--no-sandbox', `--window-size=${vw},${vh}`]
  : ['--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader',
     '--ignore-gpu-blocklist', '--no-sandbox', `--window-size=${vw},${vh}`];

const browser = await chromium.launch({ headless: true, args });
const page = await browser.newPage({ viewport: { width: vw, height: vh } });
const errs = [];
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));

await page.goto(base + route, { waitUntil: 'domcontentloaded', timeout: 60000 });
let canvas = false;
try { await page.waitForSelector('canvas', { timeout: 25000 }); canvas = true; } catch {}
await page.waitForTimeout(waitMs);
await page.screenshot({ path: out });

// Honest frame-time sampling (opt-in). Measures the page's requestAnimationFrame
// interval, which on a vsync-capped headless context reflects the per-frame
// main-thread + GPU cost: if a frame exceeds the refresh budget the rAF
// callbacks space out, so this is a real signal for the ocean-ON/OFF and
// nMax-1/3 A/B comparisons. Runs serially after the screenshot; the caller
// keeps GL contexts one-at-a-time on the host per SEQUENCING.md.
let frameTime = null;
if (measurePerf) {
  try {
    frameTime = await page.evaluate(async (sampleMs) => {
      return await new Promise((resolve) => {
        const deltas = [];
        let last = performance.now();
        const start = last;
        function tick(now) {
          deltas.push(now - last);
          last = now;
          if (now - start < sampleMs) {
            requestAnimationFrame(tick);
          } else {
            // drop the first interval (scheduling warm-up)
            deltas.shift();
            if (deltas.length === 0) { resolve({ frames: 0 }); return; }
            const sorted = [...deltas].sort((a, b) => a - b);
            const q = (p) => sorted[Math.min(sorted.length - 1, Math.floor(p * sorted.length))];
            const mean = deltas.reduce((s, x) => s + x, 0) / deltas.length;
            resolve({
              frames: deltas.length,
              meanMs: +mean.toFixed(2),
              medianMs: +q(0.5).toFixed(2),
              p95Ms: +q(0.95).toFixed(2),
              p99Ms: +q(0.99).toFixed(2),
              maxMs: +sorted[sorted.length - 1].toFixed(2),
              fps: +(1000 / mean).toFixed(1),
            });
          }
        }
        requestAnimationFrame(tick);
      });
    }, perfSampleMs);
  } catch (e) {
    frameTime = { error: String(e && e.message ? e.message : e) };
  }
}

// Confirm whether the GPU is actually driving WebGL (UNMASKED_RENDERER).
let glRenderer = 'unknown';
try {
  glRenderer = await page.evaluate(() => {
    const c = document.createElement('canvas');
    const gl = c.getContext('webgl2') || c.getContext('webgl');
    if (!gl) return 'no-webgl';
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'no-debug-ext';
  });
} catch {}

console.log(JSON.stringify({
  route, out, canvas, glMode, glRenderer,
  errorCount: errs.length,
  errors: errs.slice(0, 12),
  frameTime,
}, null, 2));
await browser.close();
