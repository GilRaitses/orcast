import { test, expect } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";
import { assertMapsHealthy } from "../helpers/demo";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 20_000);

test("beat-05 ask", async ({ page }) => {
  await installAgentAuth(page);
  await page.goto("/ask");
  await assertMapsHealthy(page);

  // Redesigned composer: let the ghost suggestion cycle once, then type a real
  // sighting so the beat shows the chat UI in use (not just a button click).
  const input = page.locator(".chat-input");
  await expect(input).toBeVisible();
  await page.waitForTimeout(2_000); // let one ghost prompt show through
  await input.click();
  await input.type("I saw a tall black dorsal fin from shore near Lime Kiln — could it have been an orca?", { delay: 18 });
  await page.waitForTimeout(800);

  await page.getByRole("button", { name: "Check sighting" }).click();
  await expect(page.locator(".ask-reply")).toBeVisible({ timeout: 60_000 });
  await page.waitForTimeout(pause);
});
