import { test, expect } from '@playwright/test';
import { attachConsoleListeners, expectNoConsoleErrors, settleForConsole, waitForMapTiles } from './helpers';

test.describe('Probability report page', () => {
  test('generates a report with hotspot cards and a visible map, no console errors', async ({ page }) => {
    attachConsoleListeners(page);

    await page.goto('/reports', { waitUntil: 'domcontentloaded' });

    const generate = page.locator('[data-cy="generate-report"]');
    await expect(generate).toBeVisible();
    await generate.click();

    // The report map is the hero of the page and must render real tiles.
    const reportMap = page.locator('.report-map google-map');
    await expect(reportMap).toBeVisible();
    await waitForMapTiles(page, '.report-map google-map');

    // Hotspot cards appear with human-readable chance copy.
    const hotspots = page.locator('.hotspot-card');
    await expect(hotspots.first()).toBeVisible({ timeout: 25_000 });
    expect(await hotspots.count()).toBeGreaterThanOrEqual(1);
    await expect(hotspots.first()).toContainText('Chance of sightings');

    // CSV export becomes available once a report loads.
    await expect(page.locator('[data-cy="download-csv"]')).toBeVisible({ timeout: 25_000 });

    await expect(page).toHaveScreenshot('reports.png', {
      fullPage: true,
      mask: [page.locator('google-map')],
    });

    await settleForConsole(page);
    expectNoConsoleErrors(page);
  });
});
