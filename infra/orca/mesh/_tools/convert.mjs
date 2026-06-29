// OM-BUILD orca mesh conversion.
// Source: Poly Pizza "Killer Whale" (Poly by Google), CC-BY 3.0.
// Reorient to the twin frame (+X forward / +Y up), scale to metric meters,
// center on bbox, weld/dedup/prune, then EXT_meshopt_compression.
//
// Build-only. No web runtime dependency added.

import { NodeIO } from '@gltf-transform/core';
import { EXTMeshoptCompression } from '@gltf-transform/extensions';
import { weld, dedup, prune, transformMesh } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';

const SRC = process.argv[2];
const DST = process.argv[3];
const TARGET_LENGTH_M = 7.0; // adult orca length, midpoint of the 6-8 m range (SKELETON.md / charter)

await MeshoptEncoder.ready;
await MeshoptDecoder.ready;

const io = new NodeIO()
  .registerExtensions([EXTMeshoptCompression])
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(SRC);
const root = doc.getRoot();

// --- 1. measure source bbox over all primitives (in source units) ---
const min = [Infinity, Infinity, Infinity];
const max = [-Infinity, -Infinity, -Infinity];
const v = [0, 0, 0];
for (const mesh of root.listMeshes()) {
  for (const prim of mesh.listPrimitives()) {
    const pos = prim.getAttribute('POSITION');
    for (let i = 0; i < pos.getCount(); i++) {
      pos.getElement(i, v);
      for (let a = 0; a < 3; a++) { min[a] = Math.min(min[a], v[a]); max[a] = Math.max(max[a], v[a]); }
    }
  }
}
const sizeZ = max[2] - min[2]; // body length runs along source +Z (nose at +Z, fluke at -Z)
const scale = TARGET_LENGTH_M / sizeZ;

// bbox center in source units
const c = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2];

// --- 2. build bake matrix (column-major mat4) ---
// vertex pipeline: p -> Ry(+90) reorients nose +Z to +X, keep +Y up -> uniform scale s -> translate to center on origin.
// Ry(+90): x' = z, y' = y, z' = -x.  Combined with scale s and centering offset t:
//   X = s*z - s*c[2]
//   Y = s*y - s*c[1]
//   Z = -s*x + s*c[0]
const s = scale;
// gl-matrix column-major: M[col*4 + row]
const M = [
  // col0 (multiplies source x): contributes to Z row -> -s
  0, 0, -s, 0,
  // col1 (source y): contributes to Y row -> s
  0, s, 0, 0,
  // col2 (source z): contributes to X row -> s
  s, 0, 0, 0,
  // col3 translation: X = -s*c[2], Y = -s*c[1], Z = s*c[0]
  -s * c[2], -s * c[1], s * c[0], 1,
];

for (const mesh of root.listMeshes()) {
  transformMesh(mesh, M);
  mesh.setName('orca');
}
for (const node of root.listNodes()) {
  if (node.getMesh()) node.setName('orca');
}

// --- 3. cleanup ---
await doc.transform(
  weld(),
  dedup(),
  prune(),
);

// --- 4. meshopt compression (EXT_meshopt_compression) - the proven runtime path ---
doc.createExtension(EXTMeshoptCompression)
  .setRequired(true)
  .setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.QUANTIZE });

await io.write(DST, doc);

// --- 5. report resulting bbox + length-axis profile for verification ---
const out = await io.read(DST);
const omin = [Infinity, Infinity, Infinity];
const omax = [-Infinity, -Infinity, -Infinity];
let tris = 0, verts = 0;
const samples = [];
for (const mesh of out.getRoot().listMeshes()) {
  for (const prim of mesh.listPrimitives()) {
    const pos = prim.getAttribute('POSITION');
    verts += pos.getCount();
    const idx = prim.getIndices();
    tris += idx ? idx.getCount() / 3 : pos.getCount() / 3;
    for (let i = 0; i < pos.getCount(); i++) {
      pos.getElement(i, v);
      samples.push([v[0], v[1], v[2]]);
      for (let a = 0; a < 3; a++) { omin[a] = Math.min(omin[a], v[a]); omax[a] = Math.max(omax[a], v[a]); }
    }
  }
}
console.log(JSON.stringify({
  target_length_m: TARGET_LENGTH_M,
  scale_factor: s,
  out_min_m: omin.map(x => +x.toFixed(4)),
  out_max_m: omax.map(x => +x.toFixed(4)),
  out_size_m: [0,1,2].map(a => +(omax[a]-omin[a]).toFixed(4)),
  triangles: tris,
  vertices: verts,
}, null, 2));

// verify nose at +X / fluke at -X (width along Z) over X bins
const xmin = omin[0], xmax = omax[0];
const bins = 8;
const st = Array.from({length: bins}, () => ({zmin:Infinity,zmax:-Infinity,ymin:Infinity,ymax:-Infinity}));
for (const [x,y,z] of samples) {
  let b = Math.floor((x - xmin) / (xmax - xmin) * bins); if (b>=bins) b=bins-1;
  const o = st[b];
  o.zmin=Math.min(o.zmin,z); o.zmax=Math.max(o.zmax,z);
  o.ymin=Math.min(o.ymin,y); o.ymax=Math.max(o.ymax,y);
}
console.log('\nX-bin (-X tail -> +X nose): lateralWidth(Z)  vertical(Y)');
st.forEach((o,i)=>{
  const xlo=(xmin+(xmax-xmin)*i/bins).toFixed(2);
  console.log(`bin${i} x~${xlo}: width=${(o.zmax-o.zmin).toFixed(2).padStart(6)} height=${(o.ymax-o.ymin).toFixed(2).padStart(6)}`);
});
