/** Pure comparison controls shared by actual decoder and narrow CPU tests. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

export function glbTriplesToENU(values) {
  assert.equal(values.length%3,0);const out=[];
  for(let i=0;i<values.length;i+=3)out.push(values[i],-values[i+2],values[i+1]);
  assert(out.every(Number.isFinite));return out;
}

export function triangleKey(points, material) {
  const encoded=points.map(point=>{const b=Buffer.alloc(24);point.forEach((x,i)=>{assert(Number.isFinite(x));b.writeDoubleLE(Object.is(x,-0)?0:x,i*8);});return b;});
  const cycles=encoded.map((_,i)=>Buffer.concat([encoded[i],encoded[(i+1)%3],encoded[(i+2)%3]]));
  let rotation=0;for(let i=1;i<3;i++)if(Buffer.compare(cycles[i],cycles[rotation])<0)rotation=i;
  return {key:material+'|'+createHash('sha256').update(cycles[rotation]).digest('hex'),rotation};
}

export function addTriangle(map,key,normals) {
  if(!map.has(key))map.set(key,[]);map.get(key).push(normals);
}

export function compareTriangles(a,b,limit=.05) {
  assert(a.size>0&&b.size>0,'An empty triangle set is not evidence');
  assert.equal(a.size,b.size,'Oriented triangle/material key set differs');
  let copies=0,maxAngle=0,maxComponent=0;
  for(const [key,aa] of a){
    const bb=b.get(key);assert(bb&&aa.length===bb.length,'Triangle multiplicity differs');
    const remaining=[...bb];
    for(const x of aa){
      let best=-1,error=Infinity;
      remaining.forEach((y,i)=>{const e=Math.max(...x.map((v,k)=>Math.abs(v-y[k])));if(e<error){best=i;error=e;}});
      const y=remaining.splice(best,1)[0];maxComponent=Math.max(maxComponent,error);copies++;
      for(let k=0;k<9;k+=3){
        const u=x.slice(k,k+3),v=y.slice(k,k+3),un=Math.hypot(...u),vn=Math.hypot(...v);
        assert(un>.99&&un<1.01&&vn>.99&&vn<1.01,'Invalid normal');
        const cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
        const angle=Math.atan2(Math.hypot(...cross),u.reduce((s,z,i)=>s+z*v[i],0))*180/Math.PI;
        assert(angle<=limit,'Normal drift exceeds0.05 degrees');maxAngle=Math.max(maxAngle,angle);
      }
    }
  }
  return {triangle_copies:copies,maximum_normal_angle_degrees:maxAngle,maximum_normal_component_difference:maxComponent,normal_angle_tolerance_degrees:limit};
}

export function compareValues(a,b,tolerance=1e-6,location='material') {
  if(typeof a==='number'&&typeof b==='number'){
    if(a===b)return 0;assert(Number.isFinite(a)&&Number.isFinite(b),location+': nonfinite mismatch');
    const d=Math.abs(a-b);assert(d<tolerance,location+': numeric property changed');return d;
  }
  if(a===null||b===null||typeof a!=='object'||typeof b!=='object'){assert.deepEqual(a,b,location+': property changed');return 0;}
  assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort(),location+': property coverage changed');
  return Math.max(0,...Object.keys(a).map(k=>compareValues(a[k],b[k],tolerance,location+'.'+k)));
}

export function materialState(m) {
  const fields=['name','type','transparent','opacity','alphaTest','side','depthWrite','blending','roughness','metalness','transmission','ior','thickness','attenuationDistance','clearcoat','clearcoatRoughness','dispersion','specularIntensity','emissiveIntensity','iridescence','iridescenceIOR','sheen','sheenRoughness'];
  const out={};for(const k of fields)if(m[k]!==undefined){assert(typeof m[k]!=='number'||Number.isFinite(m[k])||(k==='attenuationDistance'&&m[k]===Infinity),'Nonfinite material property '+k);out[k]=m[k]===Infinity?'Infinity':m[k];}
  for(const k of ['color','emissive','attenuationColor','specularColor','sheenColor'])if(m[k]){out[k]=m[k].toArray();assert(out[k].every(Number.isFinite),'Nonfinite material color');}
  if(m.iridescenceThicknessRange){out.iridescenceThicknessRange=[...m.iridescenceThicknessRange];assert(out.iridescenceThicknessRange.every(Number.isFinite));}
  for(const [k,v]of Object.entries(m))if(k.toLowerCase().endsWith('map'))assert(v===null||v===undefined,'Unexpected texture binding '+k);
  return out;
}

export function compareProtectedGroups(raw,authored,allowedPatterns) {
  const patterns=allowedPatterns.map(x=>new RegExp(x)),removed=[];let protectedGroups=0,retainedGroups=0,triangles=0;
  for(const [key,g]of raw){
    const other=authored.get(key),allowed=patterns.some(x=>x.test(g.label));
    if(!other){assert(allowed,'Protected semantic group removed: '+g.label);removed.push({label:g.label,material:g.material,triangles:g.count});continue;}
    compareTriangles(g.triangles,other.triangles);retainedGroups++;triangles+=other.count;if(!allowed)protectedGroups++;
  }
  for(const key of authored.keys())assert(raw.has(key),'Authored LOD introduced new semantic geometry');
  return {protected_groups_preserved:protectedGroups,retained_groups:retainedGroups,retained_triangles:triangles,removed_groups:removed,comparison:'Actual decoded oriented triangles, material and normals for every retained semantic label; only allowlisted whole groups may be absent'};
}
