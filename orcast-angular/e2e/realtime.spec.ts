import { test, expect } from '@playwright/test';
import {
  attachConsoleListeners,
  expectNoConsoleErrors,
  expectTextAbsent,
  settleForConsole,
  waitForMapTiles,
} from './helpers';

test.describe('Recent sightings (realtime) page', () => {
  test('shows recent sightings and only in-region stations, no console errors', async ({ page }) => {
    attachConsoleListeners(page);

    await page.goto('/realtime', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Recent sightings' })).toBeVisible();

    // Recent sightings list should populate from the live DB.
    const sightingItems = page.locator('.sighting-item');
    await expect(sightingItems.first()).toBeVisible({ timeout: 25_000 });
    expect(await sightingItems.count()).toBeGreaterThan(0);

    await waitForMapTiles(page, '.map-shell google-map');

    // Expand the Stations panel (collapsed by default) to reveal the list.
    await page.locator('.cp__header', { hasText: 'Stations' }).click();
    await expect(page.locator('.station-list')).toBeVisible();
    await expect(page.locator('.station-list li').first()).toBeVisible();

    // Out-of-region stations must be filtered out.
    await expectTextAbsent(page, 'MaST Center');
    await expectTextAbsent(page, 'Port Townsend');
    await expectTextAbsent(page, 'Bush Point');

    // Full-bleed map: snapshot the expanded Stations panel. Its station list is
    // a stable in-region set, so this snapshot also guards against out-of-region
    // stations creeping back in.
    await expect(page.locator('aside.stations-panel')).toHaveScreenshot('realtime-stations.png');

    await settleForConsole(page);
    expectNoConsoleErrors(page);
  });
});
