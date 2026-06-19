import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for the orcast Angular app.
 *
 * Runs against the live deployed site (https://orcast.org) on purpose:
 * the Google Maps JS API key is locked to the orcast.org HTTP referrer,
 * so a localhost build renders a black map void / RefererNotAllowedMapError.
 * Testing the deployed site is the only way to exercise real map tiles.
 *
 * Override the target with PW_BASE_URL when needed (e.g. a preview deploy).
 */
const baseURL = process.env.PW_BASE_URL || 'https://orcast.org';

export default defineConfig({
  testDir: './e2e',
  snapshotDir: './e2e/__snapshots__',
  outputDir: './e2e/.results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'e2e/.report' }]],
  timeout: 60_000,
  expect: {
    timeout: 15_000,
    toHaveScreenshot: {
      // Map tiles and live data vary slightly between runs; allow a small drift.
      maxDiffPixelRatio: 0.05,
      animations: 'disabled',
    },
  },
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 900 },
      },
    },
    {
      name: 'mobile-iphone13',
      use: {
        // iPhone 13 viewport/UA, but run on the Chromium engine so we only
        // need `npx playwright install chromium` (no WebKit download).
        ...devices['iPhone 13'],
        defaultBrowserType: 'chromium',
      },
    },
  ],
});
