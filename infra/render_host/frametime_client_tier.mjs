// Client-tier frame-time capture harness (BSWR-PRF, PRF-B).
//
// Produces an HONEST client-tier frame-time for the homepage Salish Sea twin with
// the BSW features on, against the 30fps budget (33.3 ms/frame). It is a
// VERIFICATION harness only: it adds NO scene behavior. It runs ON the render host
// (driven over SSM by scripts/perf/client_tier_frametime.sh) using the host's
// Playwright chromium, or locally for the vsync-uncap smoke.
//
// Method (locked at PRF-Q, see dispatch/PRF/findings/PRF-METHODOLOGY.md):
//  1. vsync: --disable-gpu-vsync + --disable-frame-rate-limit. VERIFIED LIMIT
//     (PRF-ADV): in pure headless these do NOT free-run rAF below 16.67ms (the
//     synthetic compositor BeginFrame still paces ~60Hz). The rAF interval is then
//     a quantised 30fps over/under-budget oracle (it spaces out for >16.67ms work),
//     NOT a sub-refresh frame-time meter. --smoke proves this; see PRF-ADV_VERDICT.
//  2. CPU throttle: CDP Emulation.setCPUThrottlingRate via page-scoped newCDPSession,
//     applied before navigate so warm-up is throttled too. (CPU only; the GPU is the
//     real host T4 and is NOT throttled -> the emulated number is a LOWER BOUND.)
//  3. client-matched viewport + deviceScaleFactor.
//  4. hardened rAF sampler: drop a ~2s warm-up (not one frame), >=8-10s counted
//     window, >=3 serial runs -> median-of-medians + worst-run p95.
//  5. serial only (one GL context at a time; concurrent contexts corrupt frame-time).
//
// HONESTY (binding, PRF-ADV1-DECISION.md): an emulated number is reported as
// "emulated client tier (method X)", never as a real device. The reading is
// vsync-QUANTISED and cannot resolve sub-refresh headroom. A clamped ~16.7ms median
// reads "PASS 30fps with margin (true cost < one refresh)" and is NEVER reported as
// "the frame-time is 16.7ms". A ~33.3ms cluster reads "at/under the 30fps budget".
// A sustained >=50ms bucket reads "FAIL 30fps, the miss is real" and is dispositive.
// A clamped pass does NOT certify the real client GPU (GPU cost is understated by
// CPU-only throttle on a faster GPU).
//
// usage:
//   node frametime_client_tier.mjs --smoke         # prove vsync uncap (sub-16.67ms), no scene
//   node frametime_client_tier.mjs --ab            # full BSW-on/off A/B (PRF-ACCEPT; gated)
//   node frametime_client_tier.mjs --route <r>     # one route
//
// env knobs (all recorded into the output JSON):
//   ORCAST_PW            absolute path to playwright (host); falls back to bare 'playwright'
//   ORCAST_DEV_BASE      dev server base (default http://127.0.0.1:3010)
//   ORCAST_GL            gpu | swiftshader (default gpu; swiftshader is correctness-only, NOT a tier)
//   ORCAST_VSYNC         uncapped (default) | default
//   ORCAST_CPU_THROTTLE  CDP setCPUThrottlingRate rate (default 1 = none)
//   ORCAST_VW/ORCAST_VH  viewport (default 1280x800)
//   ORCAST_DSF           deviceScaleFactor (default 1)
//   ORCAST_WARMUP_MS     warm-up dropped before counting (default 2000)
//   ORCAST_SAMPLE_MS     counted window (default 10000)
//   ORCAST_RUNS          serial repeats (default 3)
//   ORCAST_SETTLE_MS     extra settle after canvas before warm-up (default 6000; 12000 for BSW-on)
//   ORCAST_READY_SEL     optional CSS selector to await before sampling (settle gate)

const argv = process.argv.slice(2);
const hasFlag = (f) => argv.includes(f);
const flagVal = (f, d) => { const i = argv.indexOf(f); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };

const pwPath = process.env.ORCAST_PW || 'playwright';
const pwMod = await import(pwPath);
const chromium = pwMod.chromium || (pwMod.default && pwMod.default.chromium);
if (!chromium) { console.error('could not resolve playwright chromium from', pwPath); process.exit(2); }

const base = process.env.ORCAST_DEV_BASE || 'http://127.0.0.1:3010';
const glMode = (process.env.ORCAST_GL || 'gpu').toLowerCase();
const vsyncMode = (process.env.ORCAST_VSYNC || 'uncapped').toLowerCase();
const cpuThrottle = parseFloat(process.env.ORCAST_CPU_THROTTLE || '1');
const vw = parseInt(process.env.ORCAST_VW || '1280', 10);
const vh = parseInt(process.env.ORCAST_VH || '800', 10);
const dsf = parseFloat(process.env.ORCAST_DSF || '1');
const warmupMs = parseInt(process.env.ORCAST_WARMUP_MS || '2000', 10);
const sampleMs = parseInt(process.env.ORCAST_SAMPLE_MS || '10000', 10);
const runs = parseInt(process.env.ORCAST_RUNS || '3', 10);
const defaultSettleMs = parseInt(process.env.ORCAST_SETTLE_MS || '6000', 10);
const readySel = process.env.ORCAST_READY_SEL || '';

// The locked BSW A/B arms (R3). Orcasound Lab is the only clip-bearing node.
const OLAB = '48.5583362,-123.1735774,Orcasound%20Lab';
const AB_ARMS = [
  { label: 'pair1-off',   bsw: false, route: '/' },
  { label: 'pair1-on',    bsw: true,  route: `/?station=${OLAB}&bsw_demo=3&ocean=1` },
  { label: 'pair2-light', bsw: true,  route: `/?station=${OLAB}&view=topdown` },
  { label: 'pair2-heavy', bsw: true,  route: `/?station=${OLAB}&view=topdown&ocean=1&bsw_demo=3` },
];

function launchArgs() {
  const uncap = vsyncMode === 'uncapped' ? ['--disable-gpu-vsync', '--disable-frame-rate-limit'] : [];
  const gl = glMode === 'gpu'
    ? ['--use-gl=angle', '--use-angle=gl-egl', '--enable-gpu', '--ignore-gpu-blocklist']
    : ['--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
  return [...gl, '--no-sandbox', `--window-size=${vw},${vh}`, ...uncap];
}

function quantile(sorted, p) {
  if (sorted.length === 0) return null;
  return sorted[Math.min(sorted.length - 1, Math.floor(p * sorted.length))];
}
function dist(deltas) {
  if (deltas.length === 0) return { frames: 0 };
  const sorted = [...deltas].sort((a, b) => a - b);
  const mean = deltas.reduce((s, x) => s + x, 0) / deltas.length;
  return {
    frames: deltas.length,
    meanMs: +mean.toFixed(2),
    medianMs: +quantile(sorted, 0.5).toFixed(2),
    p95Ms: +quantile(sorted, 0.95).toFixed(2),
    p99Ms: +quantile(sorted, 0.99).toFixed(2),
    maxMs: +sorted[sorted.length - 1].toFixed(2),
    minMs: +sorted[0].toFixed(2),
    fps: +(1000 / mean).toFixed(1),
  };
}
const median = (xs) => { const s = [...xs].sort((a, b) => a - b); const m = Math.floor(s.length / 2); return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

// Sample rAF intervals in-page for warmupMs + sampleMs; drop everything in the
// warm-up window, return only the counted deltas. Runs after the screenshot-less
// settle; one context at a time.
async function sampleFrames(page, warm, count) {
  return await page.evaluate(async ({ warm, count }) => {
    return await new Promise((resolve) => {
      const counted = [];
      let last = performance.now();
      const start = last;
      let warmDrops = 0;
      function tick(now) {
        const dt = now - last;
        last = now;
        const elapsed = now - start;
        if (elapsed < warm) {
          warmDrops++;
        } else {
          counted.push(dt);
        }
        if (elapsed < warm + count) {
          requestAnimationFrame(tick);
        } else {
          resolve({ counted, warmDrops });
        }
      }
      requestAnimationFrame(tick);
    });
  }, { warm, count });
}

async function readRenderer(page) {
  try {
    return await page.evaluate(() => {
      const c = document.createElement('canvas');
      const gl = c.getContext('webgl2') || c.getContext('webgl');
      if (!gl) return 'no-webgl';
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'no-debug-ext';
    });
  } catch { return 'unknown'; }
}

function tag(extra = {}) {
  return {
    glMode, vsyncMode, cpuThrottle, viewport: `${vw}x${vh}@${dsf}`,
    warmupMs, sampleMs, runs, ...extra,
  };
}

// One arm = N serial runs of (fresh page -> settle -> sample). Reports per-run
// distributions, median-of-medians, and worst-run p95.
async function captureArm(browser, { label, route, settleMs }) {
  const runStats = [];
  const errsAll = [];
  let glRenderer = 'unknown';
  const url = route.startsWith('http') || route.startsWith('data:') ? route : base + route;
  for (let r = 0; r < runs; r++) {
    const page = await browser.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: dsf });
    const errs = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
    // CPU throttle BEFORE navigate so warm-up is throttled consistently (R2 §2).
    if (cpuThrottle && cpuThrottle !== 1) {
      const client = await page.context().newCDPSession(page);
      await client.send('Emulation.setCPUThrottlingRate', { rate: cpuThrottle });
    }
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    try { await page.waitForSelector('canvas', { timeout: 25000 }); } catch {}
    if (readySel) { try { await page.waitForSelector(readySel, { timeout: 30000 }); } catch {} }
    await page.waitForTimeout(settleMs);
    if (r === 0) glRenderer = await readRenderer(page);
    const { counted, warmDrops } = await sampleFrames(page, warmupMs, sampleMs);
    runStats.push({ run: r, warmDrops, ...dist(counted) });
    errsAll.push(...errs);
    await page.close();
  }
  const medians = runStats.map((s) => s.medianMs).filter((x) => x != null);
  const p95s = runStats.map((s) => s.p95Ms).filter((x) => x != null);
  return {
    label, url, glRenderer, ...tag(),
    runs: runStats,
    medianOfMediansMs: medians.length ? +median(medians).toFixed(2) : null,
    worstRunP95Ms: p95s.length ? +Math.max(...p95s).toFixed(2) : null,
    errorCount: errsAll.length,
    errors: errsAll.slice(0, 8),
  };
}

// --smoke: prove the vsync uncap. Load a trivial page (empty rAF loop) and confirm
// the sampler reports sub-16.67ms intervals. If still pinned at ~16.67ms the uncap
// failed. We sample both an uncapped and a capped page so the contrast is explicit.
async function runSmoke() {
  const TRIVIAL = 'data:text/html,<!doctype html><meta charset=utf-8><title>vsync-smoke</title>'
    + '<body style="margin:0;background:#024"><script>let f=0;function t(){f++;requestAnimationFrame(t);}requestAnimationFrame(t);</script>';
  const out = { mode: 'smoke', glMode, page: 'trivial-empty-raf' };
  // uncapped
  {
    const browser = await chromium.launch({ headless: true, args: launchArgs() });
    const page = await browser.newPage({ viewport: { width: vw, height: vh } });
    await page.goto(TRIVIAL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);
    const { counted } = await sampleFrames(page, 500, 2500);
    out.uncapped = { vsyncMode: vsyncMode, ...dist(counted) };
    await browser.close();
  }
  // capped (control): force vsync on for contrast
  {
    const capped = [...launchArgs().filter((a) => a !== '--disable-gpu-vsync' && a !== '--disable-frame-rate-limit')];
    const browser = await chromium.launch({ headless: true, args: capped });
    const page = await browser.newPage({ viewport: { width: vw, height: vh } });
    await page.goto(TRIVIAL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);
    const { counted } = await sampleFrames(page, 500, 2500);
    out.capped_control = { vsyncMode: 'default', ...dist(counted) };
    await browser.close();
  }
  const med = out.uncapped.medianMs;
  out.subRefreshProven = med != null && med < 16.67;
  out.verdict = out.subRefreshProven
    ? `PASS: uncapped median ${med}ms < 16.67ms -> vsync cap is broken, sampler can resolve sub-refresh frame cost.`
    : `FAIL: uncapped median ${med}ms not < 16.67ms -> cap NOT broken; no frame-time number is valid.`;
  console.log(JSON.stringify(out, null, 2));
  return out.subRefreshProven ? 0 : 1;
}

// Vsync-quantised over-budget oracle (PRF-ADV1-DECISION, Option 1). The rAF
// interval clamps to refresh multiples (~16.7 / 33.3 / 50 ms) and CANNOT resolve
// sub-refresh headroom (a 5ms frame and a 16ms frame both read ~16.7ms). It IS
// dispositive against the 30fps (33.3ms) budget in the direction that matters.
// A clamped ~16.7ms reading is NEVER reported as "the frame-time is 16.7ms"
// (the forbidden fabricated-headroom claim); it is reported as PASS-with-margin.
const ONE_REFRESH = 1000 / 60;          // ~16.67 ms
const BUDGET = 1000 / 30;               // 33.33 ms (30fps)
const MARGIN_EDGE = (ONE_REFRESH + BUDGET) / 2;  // ~25 ms: below = clamped at one refresh
const FAIL_EDGE = (BUDGET + 1000 / 20) / 2;      // ~41.7 ms: at/above = spilled to the 50ms bucket
function classifyBucket(medianMs, p95Ms) {
  if (medianMs == null) return { bucket: 'no-data', reading: 'no frames sampled' };
  if (medianMs < MARGIN_EDGE) {
    const p95Spill = p95Ms != null && p95Ms >= MARGIN_EDGE;
    return {
      bucket: '~16.7ms (one refresh)',
      reading: 'PASS 30fps with margin (true cost < one refresh; vsync-quantised, sub-refresh headroom unresolved)'
        + (p95Spill ? ' — but p95 spills to a higher bucket: intermittent over-refresh frames present' : ''),
    };
  }
  if (medianMs < FAIL_EDGE) {
    return { bucket: '~33.3ms (two refreshes)', reading: 'at/under the 30fps budget (true cost 16.7-33.3ms; vsync-quantised)' };
  }
  return { bucket: '>=~50ms (three+ refreshes)', reading: 'FAIL 30fps — the miss is real (sustained true cost > 33.3ms)' };
}

async function runArms(arms) {
  const browser = await chromium.launch({ headless: true, args: launchArgs() });
  const results = [];
  for (const arm of arms) {
    const settleMs = arm.bsw ? Math.max(defaultSettleMs, 12000) : defaultSettleMs;
    const armOut = await captureArm(browser, { ...arm, settleMs });
    armOut.verdict = classifyBucket(armOut.medianOfMediansMs, armOut.worstRunP95Ms);
    results.push(armOut);
  }
  await browser.close();
  const out = {
    mode: 'ab',
    method: 'emulated client tier (method X): real T4 GPU + CDP CPU throttle + client viewport + vsync-quantised rAF sampler. NOT a sub-refresh frame-time meter (subRefreshProven:false, vsync_smoke_local.json); it is a vsync-QUANTISED 30fps over-budget oracle (PRF-ADV1-DECISION.md, Option 1).',
    budgetMs: +BUDGET.toFixed(2),
    quantisation: 'rAF interval clamps to refresh multiples ~16.7 / 33.3 / 50 ms; it cannot distinguish a 5ms frame from a 16ms frame (both read ~16.7ms). A clamped ~16.7ms median is PASS-with-margin, NEVER reported as the measured frame-time.',
    honesty: 'emulated client tier = CPU-throttled LOWER BOUND on a server-class T4 GPU. A miss (sustained >=50ms bucket) is dispositive and real; a clamped ~16.7ms pass does NOT certify the real client GPU (the GPU work is not throttled). Emulated, not a real device.',
    verdict_legend: {
      'median <~25ms': 'clamped at one refresh -> PASS 30fps with margin',
      '~25-42ms': 'at/under the 30fps (33.3ms) budget',
      '>=~42ms': 'FAIL 30fps, the miss is real',
    },
    ...tag(),
    arms: results,
  };
  console.log(JSON.stringify(out, null, 2));
  return 0;
}

let code = 0;
if (hasFlag('--smoke')) {
  code = await runSmoke();
} else if (hasFlag('--ab')) {
  code = await runArms(AB_ARMS);
} else if (hasFlag('--route')) {
  code = await runArms([{ label: 'route', bsw: true, route: flagVal('--route', '/') }]);
} else {
  console.error('usage: --smoke | --ab | --route <route>');
  code = 2;
}
process.exit(code);
