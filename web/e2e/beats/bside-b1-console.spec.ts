import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";

// DEMO waveset, beat B1 "ask the console" (see
// .cca/catalogue/O0/20260627_demo-waveset/W-STORY.md).
// Drives the root console (AdaptiveExplore -> ActiveSurfaceHost -> OrchestratorTrace):
// pick a public starter prompt, send a turn, and hold on the live orchestrator trace.
// Capture with DEMO_RECORD=1 at 1280x900 (web/playwright.config.ts). Held for operator
// green-light; run via: cd web && npm run demo:beat -- beats/bside-b1-console.spec.ts

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 22_000);
const STARTER_PROMPT = "How do I plan a trip to the San Juans?";

test("bside-b1 ask the console", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/");

  await expect(page.locator('[data-demo="explore-scene"]')).toBeVisible({ timeout: 45_000 });
  await expect(page.locator('[data-demo="explore-console"]')).toBeVisible({ timeout: 45_000 });

  // Show the chat UI in use: click a public starter chip, then send the turn.
  await page.getByRole("button", { name: STARTER_PROMPT }).click();
  await page.waitForTimeout(800);
  await page.locator('[data-demo="explore-send"]').click();

  // The orchestrator plans and the active surface slots in. The explore_trace panel
  // renders when the ui_intent includes it; hold on it when present.
  const activeSurface = page.locator('[data-demo="active-surface"]');
  await expect(activeSurface).toBeVisible({ timeout: 60_000 });

  const trace = page.locator('[data-demo="orchestrator-trace"]');
  await trace
    .first()
    .waitFor({ state: "visible", timeout: 20_000 })
    .catch(() => undefined);

  await page.waitForTimeout(pause);
});
