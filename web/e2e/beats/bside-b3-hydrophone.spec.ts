import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";

// DEMO waveset, beat B3 "hydrophone acoustic" (see
// .cca/catalogue/O0/20260627_demo-waveset/W-STORY.md).
// Asks the console for a hydrophone so the orchestrator slots in the acoustic
// signal panel from the ONC relay. Honest: acoustic moderator context at a fixed
// hydrophone, not whale GPS; live spectrogram needs ONC_API_TOKEN, else metadata.
// Capture with DEMO_RECORD=1 at 1280x900. Held for operator green-light; run via:
// cd web && npm run demo:beat -- beats/bside-b3-hydrophone.spec.ts

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 18_000);
const HYDRO_PROMPT = "Show me the recent acoustic signal at the Lime Kiln hydrophone.";

test("bside-b3 hydrophone acoustic", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/");
  await expect(page.locator('[data-demo="explore-scene"]')).toBeVisible({ timeout: 45_000 });
  await expect(page.locator('[data-demo="explore-console"]')).toBeVisible({ timeout: 45_000 });

  await page.locator(".explore-console textarea").fill(HYDRO_PROMPT);
  await page.locator('[data-demo="explore-send"]').click();

  // The hydrophone panel slots in when the plan routes a hydrophone intent.
  const panel = page.locator('[data-panel="hydrophone_signal"]');
  await Promise.race([
    panel.first().waitFor({ state: "visible", timeout: 45_000 }).catch(() => undefined),
    page.locator('[data-demo="active-surface"]').waitFor({ state: "visible", timeout: 45_000 }).catch(() => undefined),
  ]);
  await page.waitForTimeout(pause);
});
