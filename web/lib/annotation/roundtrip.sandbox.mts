// Sandbox round-trip proof for the BSS annotation domain (BSS-BUILD gate).
// Runs without Next/DOM/network: load the REAL h5-derived fixture, create a
// provenance-tagged annotation against a real classified dive, persist it, read
// it back, and assert provenance survived intact.
//
//   cd web && npx tsx lib/annotation/roundtrip.sandbox.mts

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import assert from "node:assert/strict";

import { InMemoryAnnotationStore } from "./store.ts";
import { provenanceIntact } from "./provenance.ts";
import type { Annotation, AnnotationDraft, DtagFixture } from "./types.ts";

const here = dirname(fileURLToPath(import.meta.url));
const fixture = JSON.parse(
  readFileSync(join(here, "fixtures", "dtag_mn09_203a.json"), "utf-8"),
) as DtagFixture;

function fail(msg: string): never {
  console.error(`[roundtrip] FAIL ${msg}`);
  process.exit(1);
}

async function main() {
  assert.equal(fixture.meta.deployment_id, "mn09_203a", "real deployment id");
  assert.ok(fixture.expert_annotations.length >= 50, "real expert annotations present");

  const classifiedDive = fixture.dives.find((d) => d.classified_behavior);
  if (!classifiedDive) fail("no dive carries a real classified behavior");
  console.log(
    `[roundtrip] target dive #${classifiedDive.dive_id} behavior="${classifiedDive.classified_behavior}" ` +
      `samples ${classifiedDive.start_sample}..${classifiedDive.end_sample}`,
  );

  const store = new InMemoryAnnotationStore(() => new Date("2026-06-29T12:00:00Z"));
  const draft: AnnotationDraft = {
    target: {
      kind: "dive",
      dive_id: classifiedDive.dive_id,
      start_sample: classifiedDive.start_sample,
      end_sample: classifiedDive.end_sample,
    },
    behavior: classifiedDive.classified_behavior as string,
    state: "Feeding",
    confidence: 0.8,
    notes: "sandbox round-trip: expert-confirmed behavior on real dive window",
    annotator_id: "reviewer:bss-sandbox",
    annotator_role: "expert",
    source: "expert",
    method: "manual",
  };

  const created: Annotation = await store.create(draft, fixture);
  console.log(`[roundtrip] created id=${created.id} license="${created.provenance.license_status}"`);

  const readBack = await store.get(created.id);
  if (!readBack) fail("annotation did not persist");
  assert.ok(provenanceIntact(created, readBack), "provenance changed on round-trip");
  assert.equal(readBack.behavior, classifiedDive.classified_behavior);
  assert.equal(readBack.provenance.deployment_id, "mn09_203a");
  assert.ok(readBack.provenance.h5_refs.includes("dives/dive_indices"), "h5 grounding ref present");

  const listed = await store.list("mn09_203a");
  assert.equal(listed.length, 1, "annotation listed for deployment");

  console.log("[roundtrip] PASS create -> persist -> read-back; provenance intact");
}

main().catch((e) => fail(String(e)));
