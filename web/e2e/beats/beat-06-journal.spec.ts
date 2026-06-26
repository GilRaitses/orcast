import { test } from "@playwright/test";
import { installAgentAuth, loadAgentCredentials } from "../loadAgentCreds";
import { seedJournalAndPublish } from "../helpers/demo";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 15_000);

test("beat-06 journal", async ({ page }) => {
  await installAgentAuth(page);
  await seedJournalAndPublish(page);
  await page.waitForTimeout(pause);
});
