import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";
import { approveFirstPending } from "../helpers/demo";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 10_000);

test("beat-06 moderation", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/moderation");
  await expect(page.getByRole("button", { name: "Approve" }).first()).toBeVisible({ timeout: 45_000 });
  await page.waitForTimeout(2000);
  await approveFirstPending(page);
  await page.waitForTimeout(pause);
});
