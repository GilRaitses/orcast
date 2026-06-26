import fs from "fs";
import path from "path";
import type { Page } from "@playwright/test";

/** Load gitignored repo-root .agent-credentials.env into process.env. */
export function loadAgentCredentials(): void {
  const credsPath = path.resolve(__dirname, "../../.agent-credentials.env");
  if (!fs.existsSync(credsPath)) {
    throw new Error(
      `Missing ${credsPath}. Run: bash tools/testing/setup_agent_user.sh`,
    );
  }
  for (const line of fs.readFileSync(credsPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
    const idx = trimmed.indexOf("=");
    const key = trimmed.slice(0, idx).trim();
    const value = trimmed.slice(idx + 1).trim();
    if (key && process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
  if (!process.env.ORCAST_AGENT_KEY) {
    throw new Error("ORCAST_AGENT_KEY not set in .agent-credentials.env");
  }
}

export function agentKeyHeader(): Record<string, string> {
  loadAgentCredentials();
  return { "X-ORCAST-Agent-Key": process.env.ORCAST_AGENT_KEY! };
}

/** Inject agent key on same-origin requests only (never on Google Maps CDN). */
export async function installAgentAuth(page: Page): Promise<void> {
  loadAgentCredentials();
  const key = process.env.ORCAST_AGENT_KEY!;
  const base = process.env.PW_BASE_URL ?? "https://orcast-h0.vercel.app";
  const origin = new URL(base).origin;
  await page.route("**/*", async (route) => {
    const url = route.request().url();
    if (!url.startsWith(origin)) {
      await route.continue();
      return;
    }
    const headers = { ...route.request().headers(), "X-ORCAST-Agent-Key": key };
    await route.continue({ headers });
  });
}
