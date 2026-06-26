import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";
import { assertMapsHealthy, waitForProvenanceLoaded } from "../helpers/demo";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 25_000);

test("beat-02 provenance", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/?lat=48.5465&lng=-123.03&provenance=1");
  await waitForProvenanceLoaded(page);
  await assertMapsHealthy(page);
  await page.waitForTimeout(pause);
});
