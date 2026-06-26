import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";
import { assertMapsHealthy, waitForHomeReady } from "../helpers/demo";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 20_000);

test("beat-01 home", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "orcast" })).toBeVisible();
  await expect(page.getByText("agent@orcast.dev")).toBeVisible();
  await waitForHomeReady(page);
  await assertMapsHealthy(page);
  await page.waitForTimeout(pause);
});
