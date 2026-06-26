import { test } from "@playwright/test";
import { loadAgentCredentials } from "../loadAgentCreds";
import { openStaticFigure } from "../helpers/demo";

loadAgentCredentials();
const pause = Number(process.env.BEAT_PAUSE_MS ?? 20_000);

test("beat-07 dynamodb", async ({ page }) => {
  await openStaticFigure(page, "dynamodb-proof.png");
  await page.waitForTimeout(pause);
});
