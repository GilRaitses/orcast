import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";
import { waitForProvenanceLoaded } from "../helpers/demo";

// DEMO waveset, beat B-DATA "data sources and the feature pipeline" (see
// .cca/catalogue/O0/20260627_demo-waveset/W-STORY.md).
// Shows the multi-source confirmed sightings on the map (GET /api/realtime/events, each
// event carries a source), then opens a provenance pin (GET /api/provenance) so the
// covariate-as-feature kernel contributions are visible. Honest: only diel and lunar are
// fitted; tide/depth/season/salmon are wired but not in the fit.
// Capture with DEMO_RECORD=1 at 1280x900. Held for operator green-light; run via:
// cd web && npm run demo:beat -- beats/bside-bdata-sources.spec.ts

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 16_000);

test("bside-bdata data sources and feature pipeline", async ({ page }) => {
  await installAgentAuth(page);

  // Sources: let the realtime events render so multi-source sighting points are visible.
  await page.goto("/");
  await expect(page.locator('[data-demo="explore-scene"]')).toBeVisible({ timeout: 45_000 });
  await expect(page.locator('[data-demo="explore-console"]')).toBeVisible({ timeout: 45_000 });
  await page.waitForTimeout(pause);

  // Feature pipeline: open a provenance pin to show the fitted kernel contributions.
  await page.goto("/?lat=48.5465&lng=-123.03&provenance=1");
  await waitForProvenanceLoaded(page);
  await page.waitForTimeout(pause);
});
