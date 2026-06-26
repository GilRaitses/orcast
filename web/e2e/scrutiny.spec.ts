/**
 * Q1a — UI/visual scrutiny spec
 * Assertions not covered by the demo walkthrough spec.
 */
import { test, expect } from "@playwright/test";
import { installAgentAuth } from "./loadAgentCreds";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await installAgentAuth(page);
});

test("Q1a: gates page shows deviance skill value and integrity conditions", async ({ page }) => {
  await page.goto("/gates");
  await expect(page.getByRole("heading", { name: /Fitness gates/i }).first()).toBeVisible({ timeout: 30_000 });

  // Gates summary must load — caveats/integrity conditions visible
  const integrity = page.getByText(/effort assumed|unreviewed acoustic|single station|caveat/i).first();
  await expect(integrity).toBeVisible({ timeout: 25_000 });
});

test("Q1a: provenance modal opens on provenance deep-link", async ({ page }) => {
  await page.goto("/?lat=48.5465&lng=-123.03&provenance=1");
  // Modal uses data-demo="provenance-modal"
  await expect(page.locator("[data-demo='provenance-modal']").first()).toBeVisible({ timeout: 30_000 });
});

test("Q1a: explore guide chat panel loads on /explore", async ({ page }) => {
  await page.goto("/explore?lat=48.5465&lng=-123.03");
  // ExploreGuidePanel uses ask-layout class
  await expect(page.locator(".ask-layout, .card").first()).toBeVisible({ timeout: 30_000 });
  // Should have a cast-badge indicating the agent
  await expect(page.locator(".cast-badge").first()).toBeVisible({ timeout: 15_000 });
});

test("Q1a: surface planner mode available and shows planner banner", async ({ page }) => {
  await page.goto("/explore?planner=1&lat=48.5465&lng=-123.03");
  await expect(page.getByText(/Surface planner mode/i)).toBeVisible({ timeout: 30_000 });
});

test("Q1a: sighting check returns a reply with Bedrock badge", async ({ page }) => {
  await page.goto("/ask");
  await page.getByRole("button", { name: "Check sighting" }).click();
  await expect(page.locator(".ask-reply, [class*=reply]").first()).toBeVisible({ timeout: 60_000 });
  // Bedrock badge or model indicator should appear
  const badge = page.getByText(/bedrock|haiku|claude|sonnet/i).first();
  await expect(badge).toBeVisible({ timeout: 15_000 });
});

test("Q1a: moderation queue loads and shows submission cards", async ({ page }) => {
  await page.goto("/moderation");
  await expect(page.getByRole("heading", { name: /moderation|queue|review/i }).first()).toBeVisible({ timeout: 20_000 });
  // Moderation uses .card.interactive per submission or .badge elements for status
  await expect(page.locator(".card").first()).toBeVisible({ timeout: 15_000 });
});

test("Q1a: Automation chip visible when agent key active", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Automation")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("agent@orcast.dev")).toBeVisible({ timeout: 10_000 });
});
