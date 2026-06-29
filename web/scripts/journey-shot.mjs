// Throwaway journey-beat screenshotter for the /journey visual-remediation pass.
// Navigates headless chromium to /journey, waits for the WebGL canvas, and
// captures frames at the establishing, descent, follow, and orbit beats. The
// beat timings follow the choreography in JourneyScene.tsx, offset by an initial
// tile-load wait so the first frame already shows lit terrain and water.
//
// Usage: node scripts/journey-shot.mjs [baseUrl] [outDir]

import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";

const BASE = process.argv[2] ?? "http://localhost:3011";
const OUT =
  process.argv[3] ??
  "../.cca/catalogue/O0/20260627_console-journey-trips/gate_screenshots";

// State-driven beats: wait for the director HUD to report the beat's subject (or
// the orbit flag), then dwell into the beat before capturing, so each shot lands
// on its own beat regardless of how fast the tileset streams in.
const BEATS = [
  { name: "gate_establishing", match: (h) => h.subject === "San Juan Islands", dwellMs: 4000 },
  { name: "gate_descent", match: (h) => h.subject === "approach", dwellMs: 2600 },
  { name: "gate_follow", match: (h) => h.subject === "Anacortes to Orcas ferry", dwellMs: 8000 },
  { name: "gate_orbit", match: (h) => h.orbiting === "yes", dwellMs: 5000 },
];

function readHud(page) {
  return page
    .evaluate(() => {
      const el = document.querySelector("div");
      const txt = document.body.innerText || "";
      const m = txt.match(/altitude:\s*([\d.]+)\s*m/);
      const s = txt.match(/subject:\s*(.*)/);
      const o = txt.match(/orbiting:\s*(yes|no)/);
      return {
        altitude: m ? m[1] : null,
        subject: s ? s[1].trim() : null,
        orbiting: o ? o[1] : null,
      };
    })
    .catch(() => ({ altitude: null, subject: null, orbiting: null }));
}

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--ignore-gpu-blocklist"],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  page.on("console", (msg) => {
    const t = msg.type();
    if (t === "error" || t === "warning") console.log(`[page:${t}] ${msg.text()}`);
  });
  page.on("pageerror", (err) => console.log(`[pageerror] ${err.message}`));

  const url = `${BASE}/journey`;
  console.log(`navigating ${url}`);
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForSelector("canvas", { timeout: 60000 });

  const start = Date.now();
  for (const beat of BEATS) {
    // Poll the HUD until this beat is active, then dwell into it.
    const deadline = Date.now() + 90000;
    let reached = false;
    while (Date.now() < deadline) {
      const h = await readHud(page);
      if (beat.match(h)) {
        reached = true;
        break;
      }
      await page.waitForTimeout(150);
    }
    if (!reached) {
      console.log(`${beat.name}: TIMEOUT waiting for beat`);
      continue;
    }
    await page.waitForTimeout(beat.dwellMs);
    const hud = await readHud(page);
    const file = `${OUT}/${beat.name}.png`;
    await page.screenshot({ path: file });
    console.log(
      `${beat.name}: t+${((Date.now() - start) / 1000).toFixed(1)}s ` +
        `alt=${hud.altitude}m subject="${hud.subject}" orbiting=${hud.orbiting} -> ${file}`,
    );
  }

  await browser.close();
  console.log("done");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
