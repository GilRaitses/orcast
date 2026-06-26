import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";
import { assertMapsHealthy } from "../helpers/demo";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 25_000);

test("beat-04 planner", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/explore?planner=1&lat=48.5465&lng=-123.03");
  await expect(page.getByText(/Surface planner mode/i)).toBeVisible();
  await assertMapsHealthy(page);
  await page.getByRole("button", { name: "Continue exploration" }).click();
  await expect(page.getByText(/Surface planner ·/)).toBeVisible({ timeout: 60_000 });
  await expect(page.locator(".active-surface")).toBeVisible();
  await page.waitForTimeout(pause);
});
