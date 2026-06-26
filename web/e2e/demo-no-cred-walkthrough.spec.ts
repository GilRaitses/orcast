import { test, expect } from "@playwright/test";
import { installAgentAuth } from "./loadAgentCreds";
import {
  approveFirstPending,
  assertMapsHealthy,
  openStaticFigure,
  pauseBeat,
  screenshotBeat,
  seedJournalAndPublish,
  waitForHomeReady,
  waitForProvenanceLoaded,
} from "./helpers/demo";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await installAgentAuth(page);
});

test("agent-automation demo walkthrough (no manual WorkOS sign-in)", async ({ page }) => {
  // Beat 1 — Home
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "orcast" })).toBeVisible();
  await expect(page.getByText("agent@orcast.dev")).toBeVisible();
  await expect(page.getByText("Automation")).toBeVisible();
  await waitForHomeReady(page);
  await assertMapsHealthy(page);
  await screenshotBeat(page, "beat-01-home");
  await pauseBeat(page, "home");

  // Beat 2 — Provenance (URL deep link)
  await page.goto("/?lat=48.5465&lng=-123.03&provenance=1");
  await waitForProvenanceLoaded(page);
  await assertMapsHealthy(page);
  await screenshotBeat(page, "beat-02-provenance");
  await pauseBeat(page, "provenance");

  // Beat 3 — Gates
  await page.goto("/gates");
  await expect(page.getByRole("heading", { name: /Fitness gates/i }).first()).toBeVisible({ timeout: 30_000 });
  await screenshotBeat(page, "beat-03-gates");
  await pauseBeat(page, "gates");

  // Beat 4 — Surface planner (agent key on /api/interactions/plan)
  await page.goto("/explore?planner=1&lat=48.5465&lng=-123.03");
  await expect(page.getByText(/Surface planner mode/i)).toBeVisible();
  await assertMapsHealthy(page);
  await page.getByRole("button", { name: "Continue exploration" }).click();
  await expect(page.getByText(/Surface planner ·/)).toBeVisible({ timeout: 60_000 });
  await expect(page.locator(".active-surface")).toBeVisible();
  await screenshotBeat(page, "beat-04-planner");
  await pauseBeat(page, "planner");

  // Beat 5 — Sighting check
  await page.goto("/ask");
  await assertMapsHealthy(page);
  await page.getByRole("button", { name: "Check sighting" }).click();
  await expect(page.locator(".ask-reply")).toBeVisible({ timeout: 60_000 });
  await screenshotBeat(page, "beat-05-ask");
  await pauseBeat(page, "ask");

  // Beat 6 — Journal publish + moderation approve (agent key on /api/be)
  await seedJournalAndPublish(page);
  await screenshotBeat(page, "beat-06-journal");
  await pauseBeat(page, "journal");
  await approveFirstPending(page);
  await screenshotBeat(page, "beat-06-moderation");
  await pauseBeat(page, "moderation");

  // Beat 7 — DynamoDB proof slide
  await openStaticFigure(page, "dynamodb-proof.png");
  await screenshotBeat(page, "beat-07-dynamodb");
  await pauseBeat(page, "dynamodb");

  // Beat 8 — Architecture close
  await openStaticFigure(page, "architecture.png");
  await screenshotBeat(page, "beat-08-architecture");
  await pauseBeat(page, "architecture");
});
