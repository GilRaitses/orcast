import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 25_000);

test("beat-03 gates", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/gates");
  await expect(page.getByRole("heading", { name: /Fitness gates/i }).first()).toBeVisible({ timeout: 30_000 });
  await page.waitForTimeout(pause);
});
