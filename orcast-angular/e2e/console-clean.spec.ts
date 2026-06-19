import { test } from '@playwright/test';
import { attachConsoleListeners, expectNoConsoleErrors } from './helpers';

/**
 * Cross-route guard: every public route must load without any console.error
 * or uncaught pageerror (including Google Maps RefererNotAllowedMapError).
 * This is the catch-all that the per-feature specs reinforce.
 */
const ROUTES = ['/', '/reports', '/historical', '/realtime', '/ml-predictions', '/plan', '/partners'];

for (const route of ROUTES) {
  test(`no console errors on ${route}`, async ({ page }) => {
    attachConsoleListeners(page);

    await page.goto(route, { waitUntil: 'domcontentloaded' });
    // Give lazy chunks, map init, and API calls time to surface errors.
    await page.waitForLoadState('networkidle', { timeout: 30_000 }).catch(() => undefined);
    await page.waitForTimeout(3_000);

    expectNoConsoleErrors(page);
  });
}
