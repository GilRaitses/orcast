import { defineConfig, devices } from "@playwright/test";
import { loadAgentCredentials } from "./e2e/loadAgentCreds";

loadAgentCredentials();

const baseURL = process.env.PW_BASE_URL ?? "https://orcast-h0.vercel.app";
const slowMo = process.env.PW_SLOW_MO ? Number(process.env.PW_SLOW_MO) : 0;
const recordVideo = process.env.DEMO_RECORD === "1";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./e2e/.results",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 180_000,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "off",
    screenshot: "off",
    video: recordVideo ? { mode: "on", size: { width: 1280, height: 900 } } : "off",
    actionTimeout: 30_000,
    navigationTimeout: 45_000,
    launchOptions: { slowMo },
  },
  projects: [
    {
      name: "chromium-desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 900 },
      },
    },
  ],
});
