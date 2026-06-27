import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";
import { assertMapsHealthy, waitForProvenanceLoaded } from "../helpers/demo";

// DEMO waveset, beat B2 "provenance drilldown" (see
// .cca/catalogue/O0/20260627_demo-waveset/W-STORY.md).
// Opens the provenance for a hot cell: detections + fitted kernel contributions
// behind the value, with effective confidence held at 0% (gate caveat visible).
// Capture with DEMO_RECORD=1 at 1280x900. Held for operator green-light; run via:
// cd web && npm run demo:beat -- beats/bside-b2-provenance.spec.ts

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 18_000);

test("bside-b2 provenance drilldown", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/?lat=48.5465&lng=-123.03&provenance=1");
  await waitForProvenanceLoaded(page);
  await assertMapsHealthy(page);
  await page.waitForTimeout(pause);
});
