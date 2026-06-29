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

const browser = await chromium.launch({
  headless: true,
  args: [
    '--use-gl=angle',
    '--use-angle=swiftshader-webgl',
    '--enable-unsafe-swiftshader',
    '--ignore-gpu-blocklist',
    '--no-sandbox',
    '--window-size=1280,800',
  ],
});
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const errs = [];
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));

await page.goto(base + route, { waitUntil: 'domcontentloaded', timeout: 60000 });
let canvas = false;
try { await page.waitForSelector('canvas', { timeout: 25000 }); canvas = true; } catch {}
await page.waitForTimeout(waitMs);
await page.screenshot({ path: out });

console.log(JSON.stringify({
  route, out, canvas,
  errorCount: errs.length,
  errors: errs.slice(0, 12),
}, null, 2));
await browser.close();
