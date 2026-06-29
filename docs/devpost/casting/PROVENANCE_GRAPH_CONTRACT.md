# Provenance graph contract (metric drilldown)

Status: design for next deploy. Extends [INTERACTIONS_GROUNDING_PATTERN.md](INTERACTIONS_GROUNDING_PATTERN.md) and [UI_INTENT_SCHEMA.md](UI_INTENT_SCHEMA.md).

## Purpose

Render, for any displayed metric, the tools, transformations, scientific data, and analysis origins that produced it, with traceable links back to the research. This is the orcast-native analog of the Gemini "Grounding with Google Maps" `groundingSupports` structure, except leaf citations resolve to statistical artifacts and data, not place pins.

## Why (benchmark evidence)

Measured with [`tools/testing/maps_grounding_probe.py`](../../../tools/testing/maps_grounding_probe.py) against the live Gemini Interactions API (`google_maps` tool, Api-Revision 2026-05-20, model gemini-3.5-flash, San Juan coords 48.5465,-123.03). Baseline run 2026-06-24:

| Query type | Total citations | Place / scientific | Density /1k | Scientific claims | Uncited rate |
|------------|-----------------|--------------------|-------------|-------------------|--------------|
| POI (cafe near Friday Harbor) | 8 | 8 / 0 | 34.9 | 0 | n/a |
| Evidence (where are SRKWs seen + why) | 6 | 6 / 0 | 12.6 | 9 | 89% |
| Mixed (plan a shore afternoon) | 11 | 11 / 0 | 17.5 | 4 | 75% |

Finding: across all three queries, 0 of 25 citations were scientific or dataset sources. Every citation resolved to a Google Maps place pin (`maps.google.com/?cid=`). 11 of 13 scientific claims (85%) carried no citation. The evidence query named NOAA-style fisheries data, the Center for Whale Research census, Fraser River Chinook corridors, and J/K/L pod hydrophone data, and grounded none of them: the citations were the park, the lighthouse, and the museum as places. orcast must bind each claim to its fit, null test, representation run, and data.

## Node schema

A metric drilldown is a directed graph `G = (V, E)` built from the interaction `steps[]` and `annotations[]` already persisted on `exploration_turns`.

| Node | Source field | Example |
|------|--------------|---------|
| `metric` | rendered value | `effective_confidence(cell) = 0.62` |
| `claim` (C) | `model_output.annotations[]` | "lunar kernel beats null" |
| `method` (M) | `skill_invocation.skill` + grounding_refs | negative-binomial fit, phase-shuffled null |
| `experiment` (X) | `annotation.artifact` (`repr_id`, `run_id`) | Level 1 PSTH, p = 0.002 |
| `data` (D) | `provenance_citation` / `evidence_citation` | detector candidates, QC mix |
| `research` (R) | `artifact_citation` -> doc | method paper / kernel spec |

## Edge types

Mirrors the GraphiMind claim graph:

| Edge | From -> To | Meaning |
|------|-----------|---------|
| `validated_by` | C -> M | claim is tested by this method |
| `evaluated_by` | M -> X | method is scored by this experiment |
| `supports` | X -> C | experiment result supports/refutes the claim |
| `derived_from` | X -> D | experiment ran on this data |
| `grounded_in` | C -> R | claim traces to this research origin |

## Inline citation markers (claim-to-span binding)

Each `claim` node carries a text span so the UI can render an inline marker, equivalent to Firebase `groundingSupports` (`startIndex`/`endIndex` -> `groundingChunkIndices`):

```json
{
  "claim_id": "c_lunar_beats_null",
  "span": { "start": 142, "end": 188 },
  "edges": {
    "validated_by": ["m_negbin_nulltest"],
    "grounded_in": ["r_kernel_spec"]
  },
  "annotation_ref": "gate_citation:0"
}
```

## Component contract

`ProvenanceGraph` (new) consumes the existing plan payload, no backend change required for v1:

```ts
interface ProvenanceGraphProps {
  metric: { id: string; label: string; value: number | string };
  steps: InteractionStep[];        // from prepare.steps (already shipped)
  annotations: InteractionAnnotation[]; // from prepare.annotations (already shipped)
}
```

Render rules:
1. Root = metric. Children = claims from `model_output.annotations`.
2. Expand a claim to its `method` (`skill_invocation`), `experiment` (`artifact` ids), `data`, `research`.
3. Clicking a leaf deep-links to the artifact (`/review-dossier/latest`, repr/run view) via `policy.allowed_deep_links`.
4. Hovering a claim highlights its bound text span (inline marker).
5. Any claim with no `supports` edge renders a "no signal / uncited" badge, the honesty primitive Maps grounding lacks.

## Panel registry addition

Add `provenance_graph` to [`panel_registry.json`](../../../src/aws_backend/casting/panel_registry.json) and [UI_INTENT_SCHEMA.md](UI_INTENT_SCHEMA.md) so the surface planner can emit it.

## Demo beats (next deploy)

- Beat A (contrast, 20s): same orca question to Maps grounding (one park pin) vs orcast (metric graph with kernel, null test, run_id). "Maps grounds the place. We ground the evidence."
- Beat B (drilldown, 25s): click effective confidence, expand C -> M -> X -> Data, open a leaf to the repr run.
- Beat C (interactive sources, 15s): hover a claim span, the inline marker highlights the exact `skill_invocation` and artifact.

## Benchmark gate (optional)

Extend `maps_grounding_probe.py` output (citation-type split + uncited scientific-claim rate, already added) into a stored comparison so each deploy can assert orcast uncited-evidence rate stays below the Maps baseline for the same prompts.

## Roadmap (not v1)

- Embedding index over the step-log corpus for related-fit retrieval (hybrid dense + BM25, rerank), the Emergent Mind pattern.
- Neuro-symbolic filtering: embeddings for recall, the claim graph for precision.
