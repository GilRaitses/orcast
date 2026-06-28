// Wave 1 de-risk (terrain+bathymetry coastal twin charter): the imperative
// NASA-AMMOS `3d-tiles-renderer` `TilesRenderer` mounted inside the existing
// react-three-fiber render loop. This hook is the reusable lifecycle artifact
// the Wave 2 integrator lifts into SalishScene.tsx; it does NOT touch the live
// scene. It mirrors the lifecycle the maintained `3d-tiles-renderer/r3f`
// `<TilesRenderer>` component performs (construct -> setCamera ->
// setResolutionFromRenderer + update() per frame -> dispose), written out by
// hand so the Wave 2 wiring into the imperatively-authored SalishScene is
// explicit and reviewable.

import { useEffect, useState } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { TilesRenderer } from "3d-tiles-renderer";
import { GLTFExtensionsPlugin, ImplicitTilingPlugin } from "3d-tiles-renderer/plugins";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import * as THREE from "three";

export interface UseTilesRendererOptions {
  /** Tileset root URL (tileset.json). Wave 1 uses a public stand-in; Wave 2 swaps the orcast pilot URL. */
  url: string;
  /** Screen-space error target in pixels. Lower = more detail / more tiles. */
  errorTarget?: number;
  /** Cap LoD depth (Infinity = load to leaves as the error target demands). */
  maxDepth?: number;
  /** When false, the per-frame `update()` is skipped (tiles freeze). */
  enabled?: boolean;
  /** Flag loaded tile meshes as shadow casters/receivers so r3f shadows include them. */
  enableShadows?: boolean;
}

/**
 * Construct a `TilesRenderer`, sync it to the r3f camera/renderer every frame,
 * and dispose it on unmount. Returns the instance (or null until constructed);
 * mount `tiles.group` into the scene graph with `<primitive object={tiles.group} />`.
 */
export function useTilesRenderer({
  url,
  errorTarget = 12,
  maxDepth = Infinity,
  enabled = true,
  enableShadows = true,
}: UseTilesRendererOptions): TilesRenderer | null {
  const camera = useThree((s) => s.camera);
  const gl = useThree((s) => s.gl);
  const invalidate = useThree((s) => s.invalidate);
  const [tiles, setTiles] = useState<TilesRenderer | null>(null);

  // Lifecycle: construct on url change, dispose on unmount/change. Plugins are
  // registered here because some plugin properties are construction-time only.
  useEffect(() => {
    const instance = new TilesRenderer(url);

    // Implicit tiling: required by the stand-in SparseImplicitQuadtree sample
    // (subtree files); harmless for explicit tilesets like the future pilot.
    instance.registerPlugin(new ImplicitTilingPlugin());
    // glTF/glb content loader with extension + compression support. The
    // meshopt decoder is wired now so the Wave 2 orcast pilot (meshopt-packed
    // glTF) loads with no further changes. DRACO/KTX2 loaders can be added the
    // same way (see WIRING-renderer.md).
    instance.registerPlugin(
      new GLTFExtensionsPlugin({ meshoptDecoder: MeshoptDecoder }),
    );

    if (enableShadows) {
      instance.addEventListener("load-model", (e) => {
        e.scene.traverse((o) => {
          if (o instanceof THREE.Mesh) {
            o.castShadow = true;
            o.receiveShadow = true;
          }
        });
        invalidate();
      });
    }

    // Keep r3f's demand-frameloop awake while tiles stream in. With the default
    // "always" frameloop this is a no-op safety net; it is what makes a
    // frameloop="demand" host (cheaper) still settle the LoD.
    const needsUpdate = () => invalidate();
    instance.addEventListener("needs-update", needsUpdate);

    setTiles(instance);

    return () => {
      instance.removeEventListener("needs-update", needsUpdate);
      instance.dispose();
      setTiles(null);
    };
  }, [url, enableShadows, invalidate]);

  // LoD knobs applied without rebuilding the tileset.
  useEffect(() => {
    if (!tiles) return;
    tiles.errorTarget = errorTarget;
    tiles.maxDepth = maxDepth;
    invalidate();
  }, [tiles, errorTarget, maxDepth, invalidate]);

  // Register the active camera; the renderer culls/prioritizes against it.
  useEffect(() => {
    if (!tiles) return;
    tiles.setCamera(camera);
    return () => {
      tiles.deleteCamera(camera);
    };
  }, [tiles, camera]);

  // Per-frame: push the live camera world matrix + viewport resolution into the
  // renderer, then advance one LoD/stream step. This is the single integration
  // point with r3f's loop and is exactly what Wave 2 adds to SalishScene.
  useFrame(() => {
    if (!tiles || !enabled) return;
    camera.updateMatrixWorld();
    tiles.setResolutionFromRenderer(camera, gl);
    tiles.update();
  });

  return tiles;
}
