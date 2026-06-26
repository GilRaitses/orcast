import fs from "fs";
import path from "path";
import { expect, type Page } from "@playwright/test";

const REPO_ROOT = path.resolve(__dirname, "../../..");
const FIGURES = path.join(REPO_ROOT, "docs/devpost/figures");
const DEMO_RUN = path.join(FIGURES, "_demo-run");
const DEMO_VIDEO = path.join(DEMO_RUN, "demo-walkthrough.webm");

export function demoPauseMs(): number {
  if (process.env.DEMO_SCREENSHOTS === "1") return 500;
  if (process.env.DEMO_RECORD === "1") return 12_000;
  if (process.env.PW_SLOW_MO) return Math.max(500, Number(process.env.PW_SLOW_MO));
  return 6000;
}

export async function pauseBeat(page: Page, label?: string): Promise<void> {
  if (label) console.log(`[demo] ${label}`);
  await page.waitForTimeout(demoPauseMs());
}

export async function screenshotBeat(page: Page, name: string): Promise<void> {
  if (process.env.DEMO_SCREENSHOTS !== "1") return;
  fs.mkdirSync(DEMO_RUN, { recursive: true });
  await page.screenshot({ path: path.join(DEMO_RUN, `${name}.png`), fullPage: true });
}

/** Fail when Google Maps key is missing or the JS API error overlay is shown. */
export async function assertMapsHealthy(page: Page): Promise<void> {
  await expect(page.getByText("Set NEXT_PUBLIC_MAPS_KEY")).toHaveCount(0);
  await expect(page.getByText(/can't load Google Maps correctly/i)).toHaveCount(0, { timeout: 15_000 });
  const mapRegion = page.getByRole("region", { name: "Map" });
  if (await mapRegion.count()) {
    await expect(mapRegion.first()).toBeVisible({ timeout: 30_000 });
  } else {
    await expect(page.locator(".gm-style").first()).toBeVisible({ timeout: 30_000 });
  }
}

/** Home beat: confidence meter loaded (not skeleton). */
export async function waitForHomeReady(page: Page): Promise<void> {
  await expect(page.getByText("Forecast confidence")).toBeVisible({ timeout: 45_000 });
  await expect(page.locator(".confidence-pct").first()).toBeVisible({ timeout: 45_000 });
  await expect(page.locator(".confidence-pct").first()).not.toHaveText(/^$/);
}

/** Provenance beat: modal content loaded (not spinner text). */
export async function waitForProvenanceLoaded(page: Page): Promise<void> {
  await expect(page.getByText("Why is this cell hot?")).toBeVisible({ timeout: 45_000 });
  await expect(page.getByText("Tracing provenance...")).toHaveCount(0, { timeout: 45_000 });
  const loaded = page.getByText(/Modeled intensity:/i);
  const outOfRegion = page.getByText("Outside the modeled region");
  await expect(loaded.or(outOfRegion)).toBeVisible({ timeout: 45_000 });
}

export async function openStaticFigure(page: Page, filename: string): Promise<void> {
  const source = path.join(FIGURES, filename);
  const publicSlide = path.join(REPO_ROOT, "web/public/demo-slides", filename);
  if (!fs.existsSync(source) && !fs.existsSync(publicSlide)) {
    throw new Error(`Static figure missing: ${source}`);
  }
  await page.goto(`/demo-slides/${filename}`);
  await page.waitForTimeout(1000);
}

export async function waitForJournalReady(page: Page): Promise<void> {
  await page.goto("/journal");
  await page.getByRole("button", { name: "Save to journal" }).waitFor({ state: "visible", timeout: 45_000 });
  await page.getByText("Sign in to use your journal").waitFor({ state: "hidden", timeout: 5_000 }).catch(() => undefined);
}

export async function seedJournalAndPublish(page: Page): Promise<void> {
  await waitForJournalReady(page);
  const stamp = new Date().toISOString().slice(11, 19);
  await page.getByLabel("Title").fill(`Shore watch ${stamp}`);
  await page.getByLabel("Place (optional)").fill("San Juan Island");
  await page.getByLabel("Notes").fill("Demo automation entry for moderation queue.");
  await page.getByRole("button", { name: "Save to journal" }).click();
  await page.getByRole("button", { name: "Publish to community" }).first().waitFor({ state: "visible", timeout: 30_000 });
  await page.getByRole("button", { name: "Publish to community" }).first().click();
  await page.getByText(/Published —/).first().waitFor({ state: "visible", timeout: 30_000 });
}

export async function approveFirstPending(page: Page): Promise<void> {
  await page.goto("/moderation");
  const approve = page.getByRole("button", { name: "Approve" }).first();
  await approve.waitFor({ state: "visible", timeout: 45_000 });
  const before = await page.getByRole("button", { name: "Approve" }).count();
  await approve.click();
  if (before > 1) {
    await expect(page.getByRole("button", { name: "Approve" })).toHaveCount(before - 1, { timeout: 15_000 });
  } else {
    await page.waitForTimeout(1500);
  }
}

export { DEMO_RUN, DEMO_VIDEO };
