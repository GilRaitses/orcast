// BRE reenactment barrel. Sandbox-only until O0 gates the SalishScene mount.
export type {
  AcousticWindow,
  AcousticClassificationRecord,
  BehaviorClassId,
  BehaviorMotionClip,
  ClipManifest,
  ReenactmentTimeline,
  OrcaSpawnInstance,
  ReenactmentSpawnRecord,
  SpawnCountBasis,
} from "./types";
export {
  buildSpawnRecord,
  chooseClip,
  presenceAtTime,
  type SpawnOptions,
} from "./spawnFromClassification";
export {
  createOrcaPool,
  type OrcaPool,
  type OrcaPoolOptions,
  type OrcaInstanceLabel,
} from "./OrcaPool";
export {
  createTimelineDriver,
  type TimelineDriver,
  type TimelineDriverState,
  type TimelineDriverOptions,
} from "./TimelineDriver";
export {
  loadClassification,
  loadClipManifest,
  CLASSIFICATION_URL,
  CLIP_MANIFEST_URL,
} from "./loaders";
export {
  bindReenactmentPov,
  REENACTMENT_POV_LABELS,
  type ReenactmentPov,
} from "./povBinding";
export {
  buildEthogram,
  modeledClipLabel,
  type Ethogram,
  type EthogramEntry,
  type ClipAssignmentOptions,
} from "@/lib/scene/orca/motion/clips/ethogram";
