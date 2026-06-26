import { test } from "@playwright/test";
import { loadAgentCredentials } from "../loadAgentCreds";
import { openStaticFigure } from "../helpers/demo";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 25_000);

test("beat-08 architecture", async ({ page }) => {
  await openStaticFigure(page, "architecture.png");
  await page.waitForTimeout(pause);
});
