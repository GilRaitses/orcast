import { NodeIO } from '@gltf-transform/core';

const io = new NodeIO();
const doc = await io.read(process.argv[2]);
const root = doc.getRoot();

for (const mesh of root.listMeshes()) {
  for (const prim of mesh.listPrimitives()) {
    const pos = prim.getAttribute('POSITION');
    const n = pos.getCount();
    const arr = [];
    const v = [0, 0, 0];
    let min = [Infinity, Infinity, Infinity];
    let max = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < n; i++) {
      pos.getElement(i, v);
      arr.push([v[0], v[1], v[2]]);
      for (let a = 0; a < 3; a++) { min[a] = Math.min(min[a], v[a]); max[a] = Math.max(max[a], v[a]); }
    }
    console.log('vertices', n);
    console.log('min', min.map(x=>x.toFixed(2)));
    console.log('max', max.map(x=>x.toFixed(2)));
    console.log('size', [0,1,2].map(a=>(max[a]-min[a]).toFixed(2)));

    // Analyze along Z (the longest axis = body length). Bin Z, measure lateral (X) and vertical (Y) spread per bin.
    const zmin = min[2], zmax = max[2];
    const bins = 10;
    const stats = Array.from({length: bins}, () => ({xmin:Infinity,xmax:-Infinity,ymin:Infinity,ymax:-Infinity,count:0}));
    for (const [x,y,z] of arr) {
      let b = Math.floor((z - zmin) / (zmax - zmin) * bins);
      if (b >= bins) b = bins-1;
      const s = stats[b];
      s.xmin=Math.min(s.xmin,x); s.xmax=Math.max(s.xmax,x);
      s.ymin=Math.min(s.ymin,y); s.ymax=Math.max(s.ymax,y);
      s.count++;
    }
    console.log('\nZ-bin (low->high Z) : Xspread(width)  Yspread(height)  count');
    stats.forEach((s,i)=>{
      const zlo=(zmin+(zmax-zmin)*i/bins).toFixed(0);
      const xs=(s.xmax-s.xmin); const ys=(s.ymax-s.ymin);
      console.log(`bin${i} z~${zlo}: width=${xs.toFixed(1).padStart(7)} height=${ys.toFixed(1).padStart(7)} n=${s.count}`);
    });
  }
}
