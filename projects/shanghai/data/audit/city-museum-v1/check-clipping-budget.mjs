// Metadata-only preflight; constructs shader source, not a browser/GPU rendering claim.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import vm from 'node:vm';
const project=resolve(process.argv[2]||'projects/shanghai'),root=resolve(project,'../..');
const baseline='93e3cb2d0ddeba1a7db7d435bf66c2f61492326e',oldLimit=224,previousRows=218;
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(resolve(project,p));
const original=p=>execFileSync('git',['show',baseline+':projects/shanghai/'+p],{cwd:root,maxBuffer:12*1024*1024});
const oldBytes=original('src/candidate-city-clipping.js'),currentBytes=read('src/candidate-city-clipping.js');
const limit=Number(currentBytes.toString().match(/const MAX_TRIANGLES=(\d+);/)[1]);
assert(limit>=oldLimit);
assert.equal(currentBytes.toString(),oldBytes.toString().replace('const MAX_TRIANGLES=224;',`const MAX_TRIANGLES=${limit};`),'Only the reviewed capacity constant may change');
const THREE=await import(pathToFileURL(resolve(project,'vendor/three.module.js')));
const {CandidateCityClipper}=await import(pathToFileURL(resolve(project,'src/candidate-city-clipping.js')));
const {CandidateCityClipper:OldClipper}=await import('data:text/javascript;base64,'+oldBytes.toString('base64'));
const catalogue=JSON.parse(original('data/candidate-city-integrations.json'));assert.equal(catalogue.models.length,40);
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(read('vendor/maplibre-gl.js').toString(),context);const maplibre=context.module.exports;
const origin=maplibre.MercatorCoordinate.fromLngLat([121.4737,31.2304]),unit=origin.meterInMercatorCoordinateUnits();
const geographicPosition=(lng,lat)=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return new THREE.Vector3((p.x-origin.x)/unit,0,(p.y-origin.y)/unit);};
const clips=new Map();for(const row of catalogue.models){if(row.replacement_geometry)clips.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});if(row.site_replacement)clips.set(row.site_replacement.id,row.site_replacement);}
const old=new OldClipper({THREE,geographicPosition}),next=new CandidateCityClipper({THREE,geographicPosition});old.update([...clips.values()]);next.update([...clips.values()]);
assert.equal(old.triangleCount,previousRows);assert.equal(next.triangleCount,previousRows);assert.equal(old.texture.image.height,oldLimit);assert.equal(next.texture.image.height,limit);
const oldRows=Buffer.from(old.data.buffer,0,previousRows*64),newRows=Buffer.from(next.data.buffer,0,previousRows*64);assert(oldRows.equals(newRows));assert(next.data.subarray(previousRows*16).every(x=>x===0));assert.deepEqual(next.triangleOwners,old.triangleOwners);
const shaderChecks=[];
for(const spec of [
 {name:'stadium-west-untagged',ids:[1646],featureIds:false,expected:25},
 {name:'stadium-east-shared-untagged',ids:[1816,1768,677,2225],featureIds:false,expected:20},
 {name:'gym-shared-untagged',ids:[1709,112,1672,2097,349,337,480,1558,143,2066,2020,1639],featureIds:false,expected:10},
 {name:'swimming-shared-untagged',ids:[1162,1666,1870,769,1110],featureIds:false,expected:16},
 {name:'future-city-museum-eight-owner-group',ids:[1262,1860,1931,510,958,1061,169,1697],featureIds:false,expected:0},
 {name:'far-per-vertex-owners',ids:null,featureIds:true,expected:previousRows},
]){
 const built=[];
 for(const clipper of [old,next]){
  const group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);
  if(spec.featureIds)mesh.geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute(new Float32Array(mesh.geometry.getAttribute('position').count).fill(1666),1));
  clipper.bindObject(group,{id:'14-13722-6690/'+spec.name,parent:{id:'14-13722-6690'},...(spec.ids?{ids:spec.ids}:{})});
  const rows=[];
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){
   const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});
   assert.equal(shader.uniforms.candidateClipCount.value,spec.expected);assert.equal(shader.uniforms.candidateClipTexture.value.image.height,clipper===old?oldLimit:limit);
   rows.push({kind,shader,cacheKey:material.customProgramCacheKey(),payload:Buffer.from(shader.uniforms.candidateClipTexture.value.image.data.buffer,0,spec.expected*64)});
  }
  built.push({rows,group,mesh});
 }
 for(let i=0;i<3;i++){
  const a=built[0].rows[i],b=built[1].rows[i];assert(a.payload.equals(b.payload));assert.equal(a.shader.vertexShader,b.shader.vertexShader);assert.equal(a.shader.fragmentShader.replaceAll('i<224;',`i<${limit};`).replaceAll('/224.0',`/${limit}.0`),b.shader.fragmentShader);assert.equal(a.cacheKey.replace('|candidate-city-clip-v2|224|',`|candidate-city-clip-v2|${limit}|`),b.cacheKey);
  assert.equal(a.shader.uniforms.candidateMacro.value,b.shader.uniforms.candidateMacro.value);assert.equal(a.shader.uniforms.candidateHasFeatureIds.value,b.shader.uniforms.candidateHasFeatureIds.value);
  assert(b.shader.fragmentShader.includes(`for(int i=0;i<${limit};i++)`));assert(b.shader.fragmentShader.includes(`/${limit}.0`));
 }
 shaderChecks.push({name:spec.name,feature_ids:spec.ids,scoped_rows:spec.expected,passes:built[0].rows.map(r=>r.kind),payload_equal:true,shader_equal_except_capacity:true});
 for(let i=0;i<2;i++){[old,next][i].releaseObject(built[i].group);built[i].mesh.geometry.dispose();built[i].mesh.material.dispose();}
}
for(let i=0;i<limit;i++)assert(Math.abs(((i+.5)/limit)*limit-.5-i)<1e-10);
const report={schema:'city-museum-clipping-budget-preflight-v1',passed:true,baseline,
 scope:'Frozen40-candidate catalogue metadata passed through baseline and capacity-adjusted production clippers. No historical GLB assets read. Six explicit owner fixtures construct standard/depth/distance shader source; actual source geometry, final museum masks and real GPU rendering remain separate.',
 budget:{previous_catalogue_rows:218,old_capacity:oldLimit,capacity:limit,available_rows_before_new_model:limit-218,texture_width:4,texture_bytes:limit*64,production_change_only_capacity:limit!==oldLimit,new_model_rows_not_yet_final:true},
 frozen_catalogue:{records:40,sha256:sha(original('data/candidate-city-integrations.json'))},production_script:{file:'src/candidate-city-clipping.js',bytes:currentBytes.length,sha256:sha(currentBytes)},baseline_script_sha256:sha(oldBytes),
 historical_payload:{rows:previousRows,bytes:previousRows*64,old_sha256:sha(oldRows),new_sha256:sha(newRows),identical:true,padding_zero:true,owners_identical:true},
 material_shader_checks:shaderChecks,all_row_centres_addressable:true,boundary_tests:'clipping-budget-tests.tap: ten production tests check global/scoped row addressing, capacity+1 rejection preserving state, source owners and shadow materials.'};
old.dispose();next.dispose();writeFileSync(new URL('clipping-budget-preflight.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,old_rows:previousRows,limit,payload_bytes_equal:previousRows*64,material_shader_cases:shaderChecks.length,material_passes:shaderChecks.length*3,production_change_only_capacity:limit!==oldLimit}));
