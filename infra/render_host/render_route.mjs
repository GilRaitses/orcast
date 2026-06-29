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

const route = process.argv[2] || '/orca';
const out = process.argv[3] || `/home/ubuntu/orcast/shots/shot${route.replace(/\//g, '_')}.png`;
const waitMs = parseInt(process.argv[4] || '9000', 10);
const base = process.env.ORCAST_DEV_BASE || 'http://127.0.0.1:3010';
// ORCAST_GL=gpu  -> real GPU via ANGLE/EGL (NVIDIA on the aimez-gpu-capture T4)
// ORCAST_GL=swiftshader (default) -> software GL (CPU host, correctness only)
const glMode = (process.env.ORCAST_GL || 'swiftshader').toLowerCase();
const args = glMode === 'gpu'
  ? ['--use-gl=angle', '--use-angle=gl-egl', '--enable-gpu', '--ignore-gpu-blocklist',
     '--no-sandbox', '--window-size=1280,800']
  : ['--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader',
     '--ignore-gpu-blocklist', '--no-sandbox', '--window-size=1280,800'];

const browser = await chromium.launch({ headless: true, args });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const errs = [];
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));

await page.goto(base + route, { waitUntil: 'domcontentloaded', timeout: 60000 });
let canvas = false;
try { await page.waitForSelector('canvas', { timeout: 25000 }); canvas = true; } catch {}
await page.waitForTimeout(waitMs);
await page.screenshot({ path: out });

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
}, null, 2));
await browser.close();
