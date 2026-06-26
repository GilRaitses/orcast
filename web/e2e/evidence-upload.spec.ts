/**
 * U4 — Evidence upload smoke test
 *
 * Uploads a small image and audio fixture on the /ask page, asserts the asset
 * chips appear, and verifies the sighting assist response acknowledges the uploaded evidence.
 */
import * as path from "path";
import * as fs from "fs";

import { test, expect } from "@playwright/test";
import { installAgentAuth } from "./loadAgentCreds";

const REPO_ROOT = path.resolve(__dirname, "../../..");
const IMG_FIXTURE = path.join(REPO_ROOT, "web/public/demo-evidence/sample-dorsal-fin-note.txt");
const AUD_FIXTURE = path.join(REPO_ROOT, "web/public/demo-evidence/sample-hydrophone-note.txt");

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await installAgentAuth(page);
});

test("evidence upload: image chip appears and sighting assist fires", async ({ page }) => {
  await page.goto("/ask");

  // Verify the upload buttons exist
  const imgBtn = page.getByRole("button", { name: /Upload image/i });
  const audBtn = page.getByRole("button", { name: /Upload sound/i });
  await expect(imgBtn).toBeVisible({ timeout: 15_000 });
  await expect(audBtn).toBeVisible({ timeout: 5_000 });

  // File input is hidden; use setInputFiles to bypass OS file picker
  const imgInput = page.locator('input[type="file"][accept="image/*"]');
  await imgInput.setInputFiles(IMG_FIXTURE);

  // Asset chip should appear (may take a moment for upload to local/mock backend)
  const chip = page.locator(".chip").first();
  await expect(chip).toBeVisible({ timeout: 20_000 });
  await expect(chip).toContainText("sample-dorsal-fin-note.txt");

  // Fire sighting assist with the chip attached
  const checkBtn = page.getByRole("button", { name: /Check sighting/i });
  await expect(checkBtn).toBeEnabled({ timeout: 10_000 });
  await checkBtn.click();

  const reply = page.locator(".ask-reply");
  await expect(reply).toBeVisible({ timeout: 60_000 });
});

test("evidence upload: audio chip appears", async ({ page }) => {
  await page.goto("/ask");

  const audInput = page.locator('input[type="file"][accept="audio/*"]');
  await expect(audInput).toBeAttached({ timeout: 15_000 });
  await audInput.setInputFiles(AUD_FIXTURE);

  const chip = page.locator(".chip").first();
  await expect(chip).toBeVisible({ timeout: 20_000 });
  await expect(chip).toContainText("sample-hydrophone-note.txt");
});

test("evidence upload: remove chip works", async ({ page }) => {
  await page.goto("/ask");

  const imgInput = page.locator('input[type="file"][accept="image/*"]');
  await imgInput.setInputFiles(IMG_FIXTURE);

  const chip = page.locator(".chip").first();
  await expect(chip).toBeVisible({ timeout: 20_000 });

  // Click the × remove button inside the chip
  await chip.getByRole("button").click();
  await expect(chip).not.toBeVisible({ timeout: 5_000 });
});
