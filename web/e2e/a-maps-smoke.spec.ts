import { test, expect } from "@playwright/test";
import { assertMapsHealthy } from "./helpers/demo";

const MAP_ROUTES = ["/", "/explore?lat=48.5465&lng=-123.03", "/ask"];

for (const route of MAP_ROUTES) {
  test(`maps healthy on ${route}`, async ({ page }) => {
    await page.goto(route);
    await assertMapsHealthy(page);
  });
}
