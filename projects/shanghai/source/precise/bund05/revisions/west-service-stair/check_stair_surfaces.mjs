import assert from 'node:assert/strict';
import fs from 'node:fs';
import { loadDecoder, readMesh, sha } from './revision_mesh.mjs';

const [project,calibration,prior,raw,near,far,output] = process.argv.slice(2);
const decoder = await loadDecoder(project);
function inspect(file) {
  const { all, doc, view, read } = readMesh(file, decoder);
  const [southwestNorth, southwestSouth] = frame.polygon_local_east_north;
  const dx = southwestSouth[0] - southwestNorth[0], dy = southwestSouth[1] - southwestNorth[1];
  const length = Math.hypot(dx, dy), tx = dx / length, ty = dy / length;
  // Express geometry in station along the west wall, height, outward distance.
  const point = ([x, height, negNorth]) => {
    const e = x - southwestSouth[0], n = -negNorth - southwestSouth[1];
    return [-e * tx - n * ty, height, e * ty - n * tx];
  };
  const boundary = [];
  for (const mesh of doc.meshes) {
    for (const primitive of mesh.primitives) {
      const positions = read(primitive.attributes.POSITION).map(point);
      const indices = read(primitive.indices).flat();
      for (let i = 0; i < indices.length; i += 3) {
        const tri = [positions[indices[i]], positions[indices[i+1]], positions[indices[i+2]]];
        if (tri.every(p => p[0]<-.1) || tri.every(p => p[0]>7.2) ||
            tri.every(p => p[1]>5.2) || tri.every(p => p[2]<-.60) || tri.every(p => p[2]>2.5)) continue;
        boundary.push({tri, material: doc.materials[primitive.material].name});
      }
    }
  }
  // Orthogonal ray against the full triangle projected onto the two cross axes.
  // Keep the nearest hit in the specified segment, independent of face winding.
  function first(axis, origin, end) {
    const i = (axis+1)%3, j = (axis+2)%3;
    let best = null;
    for (const {tri: [a,b,c], material} of boundary) {
      const bx=b[i]-a[i], by=b[j]-a[j], cx=c[i]-a[i], cy=c[j]-a[j];
      const det=bx*cy-by*cx;
      if (Math.abs(det)<1e-10) continue;
      const vx=origin[i]-a[i], vy=origin[j]-a[j];
      const s=(vx*cy-vy*cx)/det, t=(bx*vy-by*vx)/det;
      if (s < -1e-6 || t < -1e-6 || s+t>1+1e-6) continue;
      const value=a[axis]+s*(b[axis]-a[axis])+t*(c[axis]-a[axis]);
      const fraction=(value-origin[axis])/(end-origin[axis]);
      if (fraction < -1e-6 || fraction>1 || (best && fraction>=best.fraction)) continue;
      best={material,fraction,coordinate:value};
    }
    return best ? {material:best.material,coordinate_m:+best.coordinate.toFixed(5)} : null;
  }
  const checks=[];
  function probe(name,axis,origin,end,expected,tolerance,material) {
    const hit=first(axis,origin,end);
    const passes=Boolean(hit && hit.material===material && Math.abs(hit.coordinate_m-expected)<tolerance);
    checks.push({name,axis,origin,end,expected_m:expected,tolerance_m:tolerance,material,hit,passes});
  }
  for (let k=0;k<14;k++) {
    const height=(k+1)*.155+.018;
    probe('tread '+(k+1),1,[.53+(k+.5)*.286,height+.20,.96],height-.14,height,.035,'pale stone stair treads');
  }
  probe('upper landing',1,[5.12,2.45,1.13],2.05,2.188,.035,'pale stone stair treads');
  for (const [number,station] of [[1,length/12],[2,length/4]]) {
    probe('glass below transom '+number,2,[station+.17,2.31,.21],-.5,-.18,.045,'recessed glass');
    probe('arched fixed glass '+number,2,[station+.18,3.91,.21],-.5,-.18,.045,'recessed glass');
    probe('stone bar between lights '+number,2,[station+.12,3.20,.30],-.1,.10,.04,'carved pale stone');
    probe('stone at outer arch shoulder '+number,2,[station+.54,4.21,.27],-.1,0,.04,'limestone');
  }
  for (const [i,station] of [0,5,10,13].map((k,i)=>[i,.53+(k+.5)*.286])) {
    const z=[.155,.930,1.705,2.17][i]+.64;
    probe('outer iron post '+(i+1),2,[station,z,2.0],1.51,1.736,.04,'wrought iron');
  }
  return {sha256:sha(all),bytes:all.length,selected_triangles:boundary.length,checks};
}
const frame=JSON.parse(fs.readFileSync(calibration));
const outcomes=Object.fromEntries([['original_web',prior],['raw',raw],['web',near],['lod',far]].map(([key,file])=>[key,inspect(file)]));
const record={frame:'station north from west wall south endpoint, height, distance outside wall; all in metres',outcomes};
fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
for (const [role,data] of Object.entries(outcomes)) {
  const failed=data.checks.filter(x=>!x.passes);
  console.log(role, data.checks.length-failed.length, '/',data.checks.length,failed.map(v=>v.name+' '+JSON.stringify(v.hit)).join('; '));
  if (role==='original_web') assert.ok(failed.length>=23);
  else assert.equal(failed.length,0,role);
}
