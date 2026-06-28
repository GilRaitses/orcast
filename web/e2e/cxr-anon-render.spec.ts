import { test, expect } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

// CXR acceptance render. Drives the anonymous home (AdaptiveExplore) with the
// backend fully stubbed, feeding a plan payload that DELIBERATELY carries every
// leak-prone field (raw planner agent id, skill manifest, promotion state,
// effective confidence, managed agent id, anonymous tier name). The redacted
// public components must render none of those internals. The visible console
// text and a screenshot are written to the lane evidence dirs; the console
// deny-term gate then scans the captured text.

const CAP_DIR = resolve(__dirname, "../../.cca/catalogue/O0/20260628_console-copy-redaction/gate_captures");
const SHOT_DIR = resolve(__dirname, "../../.cca/catalogue/O0/20260628_console-copy-redaction/gate_screenshots");

const INTERNAL_AGENT_ID = "surface-planner-internal-7f3a";

const planResponse = {
  status: "success",
  resolved_spec_hash: "deadbeefcafef00d",
  managed_agent_id: INTERNAL_AGENT_ID,
  agent_version: "public-2",
  hydration_mode: "inline",
  reply: "",
  ui_intent: {
    version: "ui-intent-2",
    planner_agent_id: INTERNAL_AGENT_ID,
    skill_plan: ["fetch_gates", "fetch_hotspots", "fetch_provenance"],
    panels: [
      { id: "explore_trace", surface: "sidebar", priority: 1 },
      { id: "gates_summary", surface: "sidebar", priority: 2 },
      { id: "local_area", surface: "sidebar", priority: 3 },
      {
        id: "sidequests",
        surface: "sidebar",
        priority: 4,
        props: {
          viewerTier: "anonymous-public",
          items: [
            {
              id: "s1",
              kind: "hydrophone",
              title: "Listen to a nearby hydrophone",
              prompt: "Open a live hydrophone feed and listen for calls.",
              honestyLabel: "measured",
            },
          ],
        },
      },
    ],
    deep_links: [{ label: "Open the map", href: "/" }],
    focus: { cell: "48.5,-123.0" },
  },
  prepare: {
    context: {
      gates: {
        status: "held",
        confidence: 0.42,
        effective_confidence: 0.0,
        promoted: false,
        caveats: ["Low data density this week"],
        gates: {
          cross_validation: { gate_pass: false },
          time_rescaling: { pooled_pass_exp: true },
          pit: { calibrated: false },
        },
      },
      hotspots: [1, 2, 3],
    },
    citations: [{ label: "Open the map", href: "/" }],
    deep_links: [{ label: "Open the map", href: "/" }],
    tools_used: ["fetch_gates"],
    gate_ids: ["cross_validation"],
    provenance_refs: [],
    steps: [
      { type: "resolve_agent", managed_agent_id: INTERNAL_AGENT_ID, output_status: "success", duration_ms: 12 },
      { type: "plan_output", output_status: "success", duration_ms: 30 },
      {
        type: "skill_invocation",
        skill: "fetch_gates",
        output_status: "success",
        duration_ms: 120,
        grounding_refs: ["gate:cross_validation"],
      },
    ],
    annotations: [],
  },
};

test("cxr anonymous home renders no leak terms", async ({ page }) => {
  await page.route("**/api/be/api/realtime/events", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ events: [] }) }),
  );
  await page.route("**/api/be/api/explore/sessions", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "success", session_id: "cxr-test-session" }) }),
  );
  await page.route("**/api/be/api/interactions/plan", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(planResponse) }),
  );
  // Force the streamed narration to fail so the client takes the JSON fallback.
  await page.route("**/api/narrate-stream", (r) => r.abort());
  await page.route("**/api/be/api/interactions/narrate", (r) =>
    r.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        reply: "This view is modeled, not a direct observation. Pick a spot on the map to see what grounds it.",
        source: "template",
      }),
    }),
  );

  await page.goto("/");

  const consoleEl = page.locator('[data-demo="explore-console"]');
  await expect(consoleEl).toBeVisible({ timeout: 45_000 });

  // Capture the empty anonymous home (starter prompts, placeholder, send button).
  const homeText = await consoleEl.innerText();
  mkdirSync(CAP_DIR, { recursive: true });
  mkdirSync(SHOT_DIR, { recursive: true });
  writeFileSync(resolve(CAP_DIR, "anon_home_console.txt"), homeText, "utf-8");
  await page.screenshot({ path: resolve(SHOT_DIR, "anon_home.png"), fullPage: false });

  // Run one plan turn: pick a starter chip, then send.
  await page.getByRole("button", { name: "Show me today's hotspots." }).click();
  await page.locator('[data-demo="explore-send"]').click();

  const activeSurface = page.locator('[data-demo="active-surface"]');
  await expect(activeSurface).toBeVisible({ timeout: 30_000 });
  // Let the narration fallback settle into the reply bubble.
  await page.waitForTimeout(2_000);

  const turnText = await consoleEl.innerText();
  writeFileSync(resolve(CAP_DIR, "anon_plan_turn_console.txt"), turnText, "utf-8");
  await page.screenshot({ path: resolve(SHOT_DIR, "anon_plan_turn.png"), fullPage: false });
});
