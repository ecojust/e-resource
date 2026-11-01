// Run from repository root. This constructs production shaders; browser QA performs GPU compilation.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import vm from 'node:vm';
const project=resolve(process.argv[2]||'projects/shanghai'),root=resolve(project,'../..');
const baseline='a47e69e9cbde689266855d573aa8d1f25b02944d',limit=224;
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(resolve(project,p));
const oldBytes=execFileSync('git',['show',baseline+':projects/shanghai/src/candidate-city-clipping.js'],{cwd:root});
const currentBytes=read('src/candidate-city-clipping.js');
assert.equal(currentBytes.toString().replace('const MAX_TRIANGLES=224;','const MAX_TRIANGLES=192;'),oldBytes.toString(),'Only the bounded capacity constant may change');
const THREE=await import(pathToFileURL(resolve(project,'vendor/three.module.js')));
const {CandidateCityClipper:NewClipper}=await import(pathToFileURL(resolve(project,'src/candidate-city-clipping.js')));
const {CandidateCityClipper:OldClipper}=await import('data:text/javascript;base64,'+oldBytes.toString('base64'));
const original=p=>JSON.parse(execFileSync('git',['show',baseline+':projects/shanghai/'+p],{cwd:root}));
const catalogue=original('data/candidate-city-integrations.json');assert.equal(catalogue.models.length,38);
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(read('vendor/maplibre-gl.js').toString(),context);const maplibre=context.module.exports;
const origin=maplibre.MercatorCoordinate.fromLngLat([121.4737,31.2304]),unit=origin.meterInMercatorCoordinateUnits();
const geographicPosition=(lng,lat)=>{const p=maplibre.MercatorCoordinate.fromLngLat([lng,lat]);return new THREE.Vector3((p.x-origin.x)/unit,0,(p.y-origin.y)/unit);};
const clips=new Map();for(const row of catalogue.models){if(row.replacement_geometry)clips.set(row.id,{id:row.id,geometry:row.replacement_geometry,owner:row.owner,owners:row.owners,source_feature_ids:row.source_feature_ids});if(row.site_replacement)clips.set(row.site_replacement.id,row.site_replacement);}
const old=new OldClipper({THREE,geographicPosition}),next=new NewClipper({THREE,geographicPosition});old.update([...clips.values()]);next.update([...clips.values()]);
assert.equal(old.triangleCount,192);assert.equal(next.triangleCount,192);assert.equal(old.texture.image.height,192);assert.equal(next.texture.image.height,224);
const oldRows=Buffer.from(old.data.buffer,0,192*64),newRows=Buffer.from(next.data.buffer,0,192*64);assert(oldRows.equals(newRows));assert(next.data.subarray(192*16).every(x=>x===0));assert.deepEqual(next.triangleOwners,old.triangleOwners);
const shaderChecks=[];
for(const spec of [
 {name:'stadium-west-untagged',ids:[1646],featureIds:false,expected:25},
 {name:'stadium-east-shared-untagged',ids:[1816,1768,677,2225],featureIds:false,expected:20},
 {name:'future-gym-is-not-an-old-clip',ids:[1558],featureIds:false,expected:0},
 {name:'far-per-vertex-owners',ids:null,featureIds:true,expected:192},
]){
 const built=[];
 for(const clipper of [old,next]){
  const group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);
  if(spec.featureIds)mesh.geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute(new Float32Array(mesh.geometry.getAttribute('position').count).fill(1646),1));
  clipper.bindObject(group,{id:'14-13722-6690/'+spec.name,parent:{id:'14-13722-6690'},...(spec.ids?{ids:spec.ids}:{})});
  const rows=[];
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){
   const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});
   assert.equal(shader.uniforms.candidateClipCount.value,spec.expected);
   rows.push({kind,shader,cacheKey:material.customProgramCacheKey(),payload:Buffer.from(shader.uniforms.candidateClipTexture.value.image.data.buffer,0,spec.expected*64)});
  }
  built.push({rows,group,mesh});
 }
 for(let i=0;i<3;i++){
  const a=built[0].rows[i],b=built[1].rows[i];assert(a.payload.equals(b.payload));assert.equal(a.shader.vertexShader,b.shader.vertexShader);
  assert.equal(b.shader.fragmentShader.replace('i<224;','i<192;').replace(')/224.0',')/192.0'),a.shader.fragmentShader);
  assert.equal(b.cacheKey.replace('|224|','|192|'),a.cacheKey);
  assert.equal(a.shader.uniforms.candidateMacro.value,b.shader.uniforms.candidateMacro.value);assert.equal(a.shader.uniforms.candidateHasFeatureIds.value,b.shader.uniforms.candidateHasFeatureIds.value);
  assert.match(b.shader.fragmentShader,/for\(int i=0;i<224;i\+\+\)/);assert.match(b.shader.fragmentShader,/\/224\.0/);
 }
 shaderChecks.push({name:spec.name,feature_ids:spec.ids,scoped_rows:spec.expected,passes:built[0].rows.map(r=>r.kind),payload_equal:true,shader_equal_except_loop_and_uv_capacity:true});
 for(let i=0;i<2;i++){[old,next][i].releaseObject(built[i].group);built[i].mesh.geometry.dispose();built[i].mesh.material.dispose();}
}
for(let i=0;i<limit;i++)assert(Math.abs(((i+.5)/limit)*limit-.5-i)<1e-10);
const report={schema:'jiangwan-gymnasium-clipping-budget-preflight-v1',passed:true,baseline,
 scope:'Actual frozen38-candidate catalogue decoded as metadata and passed through old and new production clippers. No historical GLB assets read. This constructs standard/depth/distance shader source and uniforms; actual GPU compilation/rendering remains browser QA.',
 change:{old_rows:192,new_rows:224,new_gym_rows_expected:10,expected_final_total:202,remaining_rows:22,texture_width:4,old_texture_bytes:12288,new_texture_bytes:14336,added_bytes_per_texture:2048,only_constant_changed:true},
 frozen_catalogue:{records:38,sha256:sha(Buffer.from(JSON.stringify(catalogue)))},production_script:{file:'src/candidate-city-clipping.js',bytes:currentBytes.length,sha256:sha(currentBytes)},baseline_script_sha256:sha(oldBytes),
 historical_payload:{rows:192,bytes:12288,old_sha256:sha(oldRows),new_sha256:sha(newRows),identical:true,new_padding_zero:true,owners_identical:true},
 material_shader_checks:shaderChecks,all224_row_centres_addressable:true,boundary_tests:'clipping-budget-tests.tap: ten unit tests include global and scoped rows193/224,225 rejection preserving active state, source ownership, old cache-holder rebinding and shadow materials.'};
old.dispose();next.dispose();writeFileSync(new URL('clipping-budget-preflight.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,old_rows:192,new_limit:224,payload_bytes_equal:12288,material_shader_cases:shaderChecks.length,material_passes:shaderChecks.length*3}));
