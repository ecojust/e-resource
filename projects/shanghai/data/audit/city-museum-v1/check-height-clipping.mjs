// Source-metre height corrections are GPU-only. Run after the catalog is frozen.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import vm from 'node:vm';
const project=resolve(process.argv[2]||'projects/shanghai'),runtimeProject=resolve(process.argv[3]||project),root=resolve(project,'../..');
const preflightPath=resolve(process.argv[4]||resolve(project,'data/audit/city-museum-v1/height-clip-input.json'));
const read=(p,base=project)=>readFileSync(resolve(base,p)),json=p=>JSON.parse(read(p));
const sha=b=>createHash('sha256').update(b).digest('hex'),baseline='93e3cb2d0ddeba1a7db7d435bf66c2f61492326e';
const original=p=>execFileSync('git',['show',`${baseline}:projects/shanghai/${p}`],{cwd:root,maxBuffer:12*1024*1024});
const spec=JSON.parse(readFileSync(preflightPath)),id='yangpu-former-shanghai-city-museum';
const THREE=await import(pathToFileURL(resolve(project,'vendor/three.module.js')));
const {CandidateCityClipper}=await import(pathToFileURL(resolve(runtimeProject,'src/candidate-city-clipping.js')));
const {CandidateCityState,mergeCandidateCityModels}=await import(pathToFileURL(resolve(runtimeProject,'src/candidate-city-integrations.js')));
const {markVerifiedOrdinaryAsset}=await import(pathToFileURL(resolve(runtimeProject,'src/ordinary-asset-verification.js')));
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(read('vendor/maplibre-gl.js').toString(),context);
const sceneSource=read('src/map-scene.js',runtimeProject).toString();
const coordinateSource=sceneSource.slice(sceneSource.indexOf('  const mercatorOrigin ='),sceneSource.indexOf('  const scene = new THREE.Scene();'));
const prepareSource=sceneSource.slice(sceneSource.indexOf('  function prepareCityObject('),sceneSource.indexOf('  function handleStreamingChange('));
const {geographicPosition,prepareCityObject}=new Function('THREE','maplibregl',`
  const ORIGIN=[121.4737,31.2304],EARTH=6378137,DEG=Math.PI/180;
  const cityDetails={prepareFarObject(){}},candidateClipper={bindObject(){}};
  function applyBuildingMaterial(){}
  ${coordinateSource}
  ${prepareSource}
  return {geographicPosition,prepareCityObject};
`)(THREE,context.module.exports);
const catalog=json('data/candidate-city-integrations.json'),museum=catalog.models.find(r=>r.id===id);
const heightClips=spec.display_height_clips;
assert.equal(heightClips.length,2);assert(heightClips.every(c=>c.owner.feature_local_id===1860&&c.owner.macro_id==='14-13722-6690'));
if(runtimeProject===project)assert.deepEqual(museum.display_height_clips,heightClips,'The tested extra clips must be published in the actual catalog');
else museum.display_height_clips=heightClips; // Explicit private preflight overlay only.
const merged=mergeCandidateCityModels([],catalog),scene=new THREE.Scene(),records=new Map();
for(const row of merged){
  const object=new THREE.Group();scene.add(object);
  const record={...row,object,status:'loaded',activeVariant:'full'};
  markVerifiedOrdinaryAsset(object,{modelId:row.id,variant:'web',asset:row.assets.web});records.set(row.id,record);
}
const state=new CandidateCityState({getRecords:()=>records,getScene:()=>scene});state.sync();
assert.deepEqual(state.displayClips.slice(0,-2),state.clips);assert.deepEqual(state.displayClips.slice(-2),heightClips);
const baseClips=models=>{const map=new Map();for(const r of models){if(r.replacement_geometry)map.set(r.id,{id:r.id,geometry:r.replacement_geometry,owner:r.owner,owners:r.owners,source_feature_ids:r.source_feature_ids||{}});if(r.site_replacement)map.set(r.site_replacement.id,{...r.site_replacement,source_feature_ids:r.site_replacement.source_feature_ids||{}});}return[...map.values()];};
assert.deepEqual(state.clips,baseClips(catalog.models));
const oldCode=original('src/candidate-city-clipping.js').toString();
const {CandidateCityClipper:OldClipper}=await import('data:text/javascript;base64,'+Buffer.from(oldCode).toString('base64'));
const {CandidateCityClipper:BeforeHeightClipper}=await import('data:text/javascript;base64,'+Buffer.from(oldCode.replace('const MAX_TRIANGLES=224;','const MAX_TRIANGLES=288;')).toString('base64'));
const old=new OldClipper({THREE,geographicPosition}),before=new BeforeHeightClipper({THREE,geographicPosition}),clipper=new CandidateCityClipper({THREE,geographicPosition});
old.update(baseClips(JSON.parse(original('data/candidate-city-integrations.json')).models));before.update(state.clips);clipper.update(state.displayClips);
assert.equal(old.triangleCount,218);assert.equal(before.triangleCount,258);assert.equal(clipper.triangleCount,262);
assert.equal(clipper.getState().triangleLimit,288);
assert(Buffer.from(old.data.buffer,0,218*64).equals(Buffer.from(clipper.data.buffer,0,218*64)));
assert(Buffer.from(before.data.buffer,0,258*64).equals(Buffer.from(clipper.data.buffer,0,258*64)));
assert(clipper.data.subarray(262*16).every(x=>x===0));

// Reproduce the shader's Float32 bbox/height/cross operations. The mapping
// polygons are decoded actual roof residues, independent of the expanded mask.
const f=Math.fround,sub=(a,b)=>f(f(a)-f(b)),cross=(ax,ay,bx,by)=>f(f(f(ax)*f(by))-f(f(ay)*f(bx)));
function inside(data,row,point){
  const i=row*16,x=f(point.x),y=f(point.y),z=f(point.z);
  if(x<data[i+8]||z<data[i+9]||x>data[i+10]||z>data[i+11]||y<data[i+6]||y>data[i+7])return false;
  const a=cross(sub(data[i+2],data[i]),sub(data[i+3],data[i+1]),sub(x,data[i]),sub(z,data[i+1]));
  const b=cross(sub(data[i+4],data[i+2]),sub(data[i+5],data[i+3]),sub(x,data[i+2]),sub(z,data[i+3]));
  const c=cross(sub(data[i],data[i+4]),sub(data[i+1],data[i+5]),sub(x,data[i+4]),sub(z,data[i+5]));
  return (a>=-.001&&b>=-.001&&c>=-.001)||(a<=.001&&b<=.001&&c<=.001);
}
const sampleReports=[],rows=Array.from({length:4},(_,i)=>Array.from(clipper.data.subarray((258+i)*16,(259+i)*16)));
for(let k=0;k<heightClips.length;k++){
  const patch=spec.patches[k],c=heightClips[k],ring=patch.actual_main_roof_retained_geometry_wgs84.coordinates[0].slice(0,-1);
  const ref=c.height_reference,group=new THREE.Group();prepareCityObject(group,{id:c.owner.macro_id,name:'source height',lng:ref[0],lat:ref[1]});group.updateMatrixWorld(true);
  const neighborY=new THREE.Vector3(0,patch.original_1262_top_native_m,0).applyMatrix4(group.matrixWorld).y;
  const roofY=new THREE.Vector3(0,patch.actual_original_main_top_native_m,0).applyMatrix4(group.matrixWorld).y;
  const minY=clipper.data[(258+2*k)*16+6],maxY=clipper.data[(258+2*k)*16+7];
  assert.equal(minY,Math.fround(geographicPosition(...ref,c.min_height).y));assert.equal(maxY,Math.fround(geographicPosition(...ref,c.max_height).y));
  assert(minY-f(neighborY)>.0048);assert(roofY>minY&&roofY<maxY);
  const samples=[];
  for(let i=0;i<ring.length;i++)for(let step=0;step<=32;step++){
    const t=step/32,a=ring[i],b=ring[(i+1)%ring.length];samples.push([a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t]);
  }
  const contour=ring.map(([x,y])=>new THREE.Vector2(x,y));
  for(const tri of THREE.ShapeUtils.triangulateShape(contour,[]))for(let i=0;i<=16;i++)for(let j=0;j<=16-i;j++){
    const a=i/16,b=j/16,d=1-a-b;samples.push([ring[tri[0]][0]*a+ring[tri[1]][0]*b+ring[tri[2]][0]*d,ring[tri[0]][1]*a+ring[tri[1]][1]*b+ring[tri[2]][1]*d]);
  }
  let cases=0;
  for(const sample of samples)for(const dx of [-.002,0,.002])for(const dz of [-.002,0,.002]){
    const p=geographicPosition(...sample);p.x+=dx;p.z+=dz;p.y=roofY;
    assert([258+2*k,259+2*k].some(row=>inside(clipper.data,row,p)),`${patch.interface}: actual original roof sample must be removed`);
    p.y=neighborY;assert(![258,259,260,261].some(row=>inside(clipper.data,row,p)),'1262 roof must survive even at identical XY');cases++;
  }
  sampleReports.push({interface:patch.interface,height_reference:ref,native_metres:[c.min_height,c.max_height],world_y_float32:[minY,maxY],neighbor_max_world_y:neighborY,neighbor_max_world_y_float32:f(neighborY),float32_gap:minY-f(neighborY),sample_count:samples.length,xy_perturbed_cases:cases,perturbation_m:[-.002,0,.002],target_roof_samples_removed:true,neighbor_roof_samples_preserved:true});
}
assert(spec.actual_cached_triangle_protection.foreign_owners.every(r=>r.intersection_area_m2===0&&r.intersection_length_m===0));
const nearChecks=[];
for(const [name,ids,featureIds,expected] of [['actual-eight-owner-near',[1262,1860,1931,510,958,1061,169,1697],false,44],['foreign-only-near',[1262,510,958,1061,169,1697],false,0],['per-vertex-far',[],true,262]]){
  const group=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());group.add(mesh);
  if(featureIds)mesh.geometry.setAttribute('_feature_id_0',new THREE.Float32BufferAttribute(new Float32Array(mesh.geometry.attributes.position.count).fill(1860),1));
  clipper.bindObject(group,{id:name,parent:{id:'14-13722-6690'},ids});
  for(const [material,kind] of [[mesh.material,'standard'],[mesh.customDepthMaterial,'depth'],[mesh.customDistanceMaterial,'distanceRGBA']]){
    const lib=THREE.ShaderLib[kind],shader={vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader,uniforms:{}};material.onBeforeCompile(shader,{});
    assert.equal(shader.uniforms.candidateClipCount.value,expected);assert.match(shader.fragmentShader,/candidateWorldPosition\.y<cy\.z\|\|candidateWorldPosition\.y>cy\.w/);
    nearChecks.push({group:name,pass:kind,rows:expected,feature_ids:featureIds});
  }
  clipper.releaseObject(group);mesh.geometry.dispose();mesh.material.dispose();
}
const reference=heightClips[0].height_reference,sourceGroup=new THREE.Group();prepareCityObject(sourceGroup,{id:'14-13722-6690',name:'source-transform',lng:reference[0],lat:reference[1]});sourceGroup.updateMatrixWorld(true);
const payload=Buffer.from(clipper.data.buffer,0,clipper.triangleCount*16*4);writeFileSync(new URL('gpu-height-rows.f32',import.meta.url),payload);
const dataPayload={file:'gpu-height-rows.f32',bytes:payload.length,sha256:sha(payload),rows:clipper.triangleCount,columns:16,little_endian:true,old218_prefix_sha256:sha(payload.subarray(0,218*64)),base258_prefix_sha256:sha(payload.subarray(0,258*64))};
const sourceTransform={height_reference:reference,scene_origin:[121.4737,31.2304],macro_id:'14-13722-6690',near_inherits_far_matrix:true,model_matrix_double:sourceGroup.matrixWorld.toArray(),model_matrix_float32:sourceGroup.matrixWorld.toArray().map(Math.fround),geographic_position_source:coordinateSource,prepare_city_object_source:prepareSource};
const diagnostics=state.getState();assert.equal(diagnostics.displayClips.length,diagnostics.clips.length+2);
const collisions=JSON.stringify(state.collisions()),vectorClips=JSON.stringify(state.clips);
delete records.get(id).display_height_clips;state.sync();assert.deepEqual(state.displayClips,state.clips);
assert.equal(JSON.stringify(state.collisions()),collisions);assert.equal(JSON.stringify(state.clips),vectorClips);
const bindings=['src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/map-scene.js','src/app.js','index.html','tools/build_candidate_city_integrations.py'].map(file=>{const b=read(file,runtimeProject);return{file,sha256:sha(b),bytes:b.length};});
const report={schema:'city-museum-height-clipping-runtime-v1',passed:true,private_preflight:runtimeProject!==project,old_rows:218,old_payload_bytes:13952,old_rows_identical:true,pre_height_rows:258,pre_height_payload_bytes:16512,pre_height_rows_identical:true,added_height_rows:4,total_rows:262,capacity:288,height_clip_ids:heightClips.map(c=>c.id),data_payload:dataPayload,source_transform:sourceTransform,rows,sample_checks:sampleReports,shader_checks:nearChecks,shader_passes:nearChecks.length,source_vector_collision_unchanged:true,debug_clips_separate:true,preflight_sha256:sha(readFileSync(preflightPath)),bindings,limitations:'Float32 bbox/height/cross simulation samples decoded actual roof polygons, including±2mm XY perturbation. It does not run WebGL rasterization or replay every instance shader operation. Full native triangle/foreign-owner safety is recorded separately by mapping, and final browser pixels require independent QA.'};
old.dispose();before.dispose();clipper.dispose();
writeFileSync(new URL('height-clipping-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,private_preflight:report.private_preflight,rows:report.total_rows,old218:true,base258:true,added:report.added_height_rows,shader_passes:report.shader_passes,samples:sampleReports.reduce((sum,r)=>sum+r.xy_perturbed_cases,0)}));
