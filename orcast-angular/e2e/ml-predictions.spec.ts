import { test, expect } from '@playwright/test';
import {
  attachConsoleListeners,
  expectNoConsoleErrors,
  expectTextAbsent,
  settleForConsole,
  waitForMapTiles,
} from './helpers';

test.describe('Probability map (ml-predictions) page', () => {
  test('loads a grid with > 0 points, no fake model copy, no console errors', async ({ page }) => {
    attachConsoleListeners(page);

    await page.goto('/ml-predictions', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Probability map' })).toBeVisible();

    // The page auto-generates a grid on load. Wait for that; only fall back to
    // a manual generate if the panel never shows and the button is idle.
    const resultsPanel = page.locator('.results-panel');
    const generateBtn = page.locator('.generate-btn');
    try {
      await expect(resultsPanel).toBeVisible({ timeout: 25_000 });
    } catch {
      await expect(generateBtn).toBeEnabled({ timeout: 10_000 });
      await generateBtn.click();
      await expect(resultsPanel).toBeVisible({ timeout: 25_000 });
    }

    // Core regression: default threshold must not zero out the grid.
    const gridLine = resultsPanel.locator('p', { hasText: 'Grid points' });
    await expect(gridLine).toBeVisible();
    const gridText = await gridLine.innerText();
    const gridCount = parseInt(gridText.replace(/[^0-9]/g, ''), 10);
    expect(gridCount, `Grid points should be > 0 (saw "${gridText}")`).toBeGreaterThan(0);

    // No fake model / PINN selector copy.
    await expectTextAbsent(page, /\bPINN\b/);
    await expect(page.locator('.model-selector')).toHaveCount(0);
    await expect(page.locator('.model-info')).toHaveCount(0);
    await expect(resultsPanel.getByText('Model', { exact: true })).toHaveCount(0);

    await waitForMapTiles(page, '.map-shell google-map');

    // Full-bleed map: snapshot the controls aside (sliders, labels) rather than
    // a masked full page. Grid-point counts vary run-to-run, so the results
    // panel is covered by the functional assertion above, not the snapshot.
    await expect(page.locator('aside.grid-controls')).toHaveScreenshot('ml-controls.png');

    await settleForConsole(page);
    expectNoConsoleErrors(page);
  });
});
