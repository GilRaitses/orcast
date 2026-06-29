// Interpretive ocean layer barrel. Default-off, labeled, guarded.
// The basic stub (createInterpretiveOceanLayer) and the promoted double-diffusion
// volumetric (createDoubleDiffusionLayer) both carry the same mandatory chip text
// and the same forbidden-claim guard. Existing exports are kept stable.
export {
  createInterpretiveOceanLayer,
  INTERPRETIVE_OCEAN_LABEL,
  INTERPRETIVE_OCEAN_DETAIL,
  FORBIDDEN_OCEAN_CLAIMS,
  assertNoForbiddenClaim,
} from "./interpretiveOceanLayer";
export type {
  InterpretiveOceanLayer,
  InterpretiveOceanOptions,
} from "./interpretiveOceanLayer";

export { createDoubleDiffusionLayer } from "./doubleDiffusion";
export type {
  DoubleDiffusionLayer,
  DoubleDiffusionOptions,
  OceanProcessHonestyLabel,
} from "./doubleDiffusion";

export {
  analyticHaloclineProfile,
  stratificationToTexture,
} from "./stratification";
export { measuredHaloclineProfile } from "./measuredProfile";
export type {
  StratificationProfile,
  StratificationSample,
  StratificationOrigin,
} from "./stratification";

export { measureFrameTimes, runFrameTimeAB, FRAME_BUDGETS } from "./perf";
export type {
  FrameTimeStats,
  FrameBudget,
  ABCondition,
  ABResult,
} from "./perf";
