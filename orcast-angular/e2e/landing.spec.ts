import { test, expect } from '@playwright/test';
import { attachConsoleListeners, expectNoConsoleErrors, settleForConsole, waitForMapTiles } from './helpers';

test.describe('Landing page', () => {
  test('renders the map hero with real tiles, 3-step cards, and no console errors', async ({ page }) => {
    attachConsoleListeners(page);

    await page.goto('/', { waitUntil: 'domcontentloaded' });

    // The hero <google-map> must paint actual tiles, not a black void.
    const heroMap = page.locator('.map-hero google-map');
    await expect(heroMap).toBeVisible();
    await waitForMapTiles(page, '.map-hero google-map');

    // "Start here" guided steps: exactly 3 step cards.
    await expect(page.getByRole('heading', { name: 'Start here' })).toBeVisible();
    const stepCards = page.locator('.steps .step-card');
    await expect(stepCards).toHaveCount(3);
    await expect(page.locator('.step-card', { hasText: 'Probability report' })).toBeVisible();
    await expect(page.locator('.step-card', { hasText: 'Historical sightings' })).toBeVisible();
    await expect(page.locator('.step-card', { hasText: 'Probability map' })).toBeVisible();

    // Hero identity.
    await expect(page.getByRole('heading', { level: 1, name: 'orcast' })).toBeVisible();

    // Visual snapshot. Mask the live map (tiles vary run-to-run) so we still
    // catch layout/void/nav-truncation regressions deterministically. Taken
    // before the console gate so a baseline exists even when a console bug fails.
    await expect(page).toHaveScreenshot('landing.png', {
      fullPage: true,
      mask: [page.locator('google-map')],
    });

    // No console errors and specifically no Maps referrer error (black-map cause).
    await settleForConsole(page);
    expectNoConsoleErrors(page);
  });
});
