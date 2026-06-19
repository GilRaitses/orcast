import { test, expect } from '@playwright/test';
import {
  attachConsoleListeners,
  expectNoConsoleErrors,
  expectTextAbsent,
  settleForConsole,
  waitForMapTiles,
} from './helpers';

test.describe('Historical sightings page', () => {
  test('shows behavior filters (not pod types), renders the map, no console errors', async ({ page }) => {
    attachConsoleListeners(page);

    await page.goto('/historical', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Historical sightings' })).toBeVisible();

    // Removed pod-type UI must be gone everywhere on the page.
    await expectTextAbsent(page, 'Pod types');
    await expectTextAbsent(page, 'Resident Pods');
    await expectTextAbsent(page, /\bJ Pod\b/);
    await expectTextAbsent(page, /\bK Pod\b/);
    await expectTextAbsent(page, /\bL Pod\b/);

    // Behavior filters are the current filtering model.
    await expect(page.getByText('Behaviors', { exact: true })).toBeVisible();
    const behaviorChecks = page.locator('.filter-checkbox input[type="checkbox"]');
    await expect(behaviorChecks.first()).toBeVisible();
    expect(await behaviorChecks.count()).toBeGreaterThanOrEqual(3);

    // Map must paint real tiles.
    await waitForMapTiles(page, '.map-shell google-map');

    // The map is full-bleed here, so a masked full-page shot would hide the
    // control panel. Snapshot the controls aside instead — that is the UI
    // (behavior filters, headings) we actually want to guard.
    await expect(page.locator('aside.historical-controls')).toHaveScreenshot('historical-controls.png');

    await settleForConsole(page);
    expectNoConsoleErrors(page);
  });
});
