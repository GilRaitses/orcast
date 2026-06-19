import { Page, expect } from '@playwright/test';

/**
 * Shared helpers for the orcast Playwright suite.
 *
 * These exist so every spec catches the classes of bug that unit tests missed:
 *  - a black/empty Google Map (no tiles ever render),
 *  - RefererNotAllowedMapError (wrong API key referrer),
 *  - silent console.error / uncaught pageerror across routes.
 */

interface ConsoleState {
  errors: string[];
}

// Per-page console state. Listeners must be attached before navigation, so call
// attachConsoleListeners(page) at the very top of each test.
const consoleStates = new WeakMap<Page, ConsoleState>();

/**
 * Console errors that are demonstrably not produced by orcast app code.
 * Keep this list tiny and documented. We do NOT add app errors here — those
 * should surface as test failures / findings.
 */
const IGNORED_CONSOLE_PATTERNS: RegExp[] = [
  /favicon\.ico/i, // browser auto-requests favicon; 404 is not an app bug
  /ResizeObserver loop/i, // benign Chromium layout notification, not an error we cause
];

export function attachConsoleListeners(page: Page): void {
  const state: ConsoleState = { errors: [] };
  consoleStates.set(page, state);

  page.on('console', msg => {
    if (msg.type() !== 'error') {
      return;
    }
    const text = msg.text();
    if (IGNORED_CONSOLE_PATTERNS.some(re => re.test(text))) {
      return;
    }
    state.errors.push(`console.error: ${text}`);
  });

  page.on('pageerror', err => {
    state.errors.push(`pageerror: ${err.message}`);
  });
}

/** Returns the console/page errors collected so far for this page. */
export function getConsoleErrors(page: Page): string[] {
  return consoleStates.get(page)?.errors ?? [];
}

/**
 * Fails the test if any console.error or uncaught pageerror was seen.
 * Always asserts there is no Google Maps referrer error specifically, since
 * that one renders a black map that looks fine to a naive visibility check.
 */
export function expectNoConsoleErrors(page: Page): void {
  const errors = getConsoleErrors(page);

  const refererErrors = errors.filter(e => /RefererNotAllowedMapError|ApiNotActivated|InvalidKeyMapError/i.test(e));
  expect(refererErrors, `Google Maps API key error(s):\n${refererErrors.join('\n')}`).toEqual([]);

  expect(errors, `Console/page errors detected:\n${errors.join('\n')}`).toEqual([]);
}

/**
 * Waits until a real Google Map has rendered tiles inside the given
 * <google-map> element — i.e. the map container has an <img> or <canvas>
 * child. A black void has none, so this catches the "map is visible but
 * empty" bug that `expect(googleMap).toBeVisible()` misses.
 *
 * It also opportunistically waits for a maps tile network response as a
 * second signal.
 */
export async function waitForMapTiles(
  page: Page,
  selector = 'google-map',
  opts: { timeout?: number } = {}
): Promise<void> {
  const timeout = opts.timeout ?? 30_000;

  // Signal 1: a Google Maps tile/image network response.
  const tileResponse = page
    .waitForResponse(
      res =>
        /maps\.googleapis\.com\/maps\/(vt|api\/js)/i.test(res.url()) ||
        /(khms|mts|mt[0-3]|vt)\d*\.(google|googleapis)\.com/i.test(res.url()) ||
        /maps.*\.google.*\/(vt|tile|kh)/i.test(res.url()),
      { timeout }
    )
    .catch(() => null);

  // Signal 2 (authoritative): tiles actually painted into the map container.
  const tilesPainted = page
    .waitForFunction(
      sel => {
        const root = document.querySelector(sel as string);
        if (!root) {
          return false;
        }
        const container = root.querySelector('.map-container') ?? root;
        return !!container.querySelector('img, canvas');
      },
      selector,
      { timeout }
    )
    .catch(() => null);

  await Promise.race([tileResponse, tilesPainted]);

  // Regardless of which signal won, require painted tiles as the final proof.
  await page.waitForFunction(
    sel => {
      const root = document.querySelector(sel as string);
      if (!root) {
        return false;
      }
      const container = root.querySelector('.map-container') ?? root;
      return !!container.querySelector('img, canvas');
    },
    selector,
    { timeout }
  );
}

/** Counts rendered map marker images inside a <google-map>. */
export async function countMapMarkers(page: Page, selector = 'google-map'): Promise<number> {
  return page.evaluate(sel => {
    const root = document.querySelector(sel as string);
    if (!root) {
      return 0;
    }
    // Google Maps renders advanced/legacy markers as <img> or button[role] overlays.
    const imgs = root.querySelectorAll('img[src*="marker"], img[src*="spotlight"], [role="button"] img, .map-marker');
    return imgs.length;
  }, selector);
}

/**
 * Lets async work (lazy chunks, map init, API responses) finish so that
 * deferred console.error / pageerror events are captured before we assert.
 * Without this, console checks race the data calls and flake.
 */
export async function settleForConsole(page: Page, quietMs = 1_500): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout: 20_000 }).catch(() => undefined);
  await page.waitForTimeout(quietMs);
}

/** Asserts a piece of text is absent anywhere in the rendered page body. */
export async function expectTextAbsent(page: Page, text: string | RegExp): Promise<void> {
  const body = (await page.locator('body').innerText()).toLowerCase();
  const needle = typeof text === 'string' ? text.toLowerCase() : text;
  if (typeof needle === 'string') {
    expect(body, `Expected "${text}" to be absent from the page`).not.toContain(needle);
  } else {
    expect(body, `Expected ${text} to be absent from the page`).not.toMatch(needle);
  }
}
