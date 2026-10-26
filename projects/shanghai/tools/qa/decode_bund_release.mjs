/** Actual vendored Three/GLTFLoader/Meshopt geometry decode; no browser or GPU.
 * Embedded JPEGs are genuinely decoded by Pillow. A dimension-only ImageBitmap
 * adapter lets Three build its normal texture/material objects in Node; this is
 * explicitly NOT a test of browser EXIF decoding, UV sampling or visual quality.
 */
import {readFile, writeFile, mkdtemp, rm, mkdir, rename} from 'node:fs/promises';
import {resolve, join, dirname, relative, isAbsolute} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';

const defaults=['bund02','bund03','bund12','bund15','bund17','bund18','bund19','bund20','bund23'];
const args={project:'.',output:null,ids:defaults,lod:false,tolerance:1e-4,python:'python3'};
for(let i=2;i<process.argv.length;i++) {
  const flag=process.argv[i];
  if(flag==='--help') {
    console.log('node decode_bund_release.mjs --project PATH --output REPORT.json [--ids bund02,bund03,...] [--include-lod] [--bounds-tolerance METRES] [--python PYTHON]\nDefault: nine updated Bund full web GLBs, excluding unchanged Customs House13. No browser or GPU is started. Python+Pillow is required for genuine embedded JPEG decoding.');
    process.exit(0);
  }
  if(flag==='--include-lod') {args.lod=true;continue;}
  if(!['--project','--output','--ids','--bounds-tolerance','--python'].includes(flag)) throw Error(`Unknown argument ${flag}`);
  const value=process.argv[++i];if(!value)throw Error(`Missing value for ${flag}`);
  if(flag==='--project')args.project=value;
  if(flag==='--output')args.output=value;
  if(flag==='--ids')args.ids=[...new Set(value.split(','))];
  if(flag==='--bounds-tolerance')args.tolerance=Number(value);
  if(flag==='--python')args.python=value;
}
assert(args.output,'--output is required');assert(args.tolerance>0&&Number.isFinite(args.tolerance),'Invalid bounds tolerance');
assert(args.ids.length&&args.ids.every(id=>defaults.includes(id)),'Only the nine explicit release targets are allowed');
const project=resolve(args.project), output=resolve(args.output), sha=b=>createHash('sha256').update(b).digest('hex');
const assetPath=name=>{assert(typeof name==='string'&&!isAbsolute(name),'Asset must be project relative');const path=resolve(project,name);assert(!relative(project,path).startsWith('..'),'Asset escapes project');return path;};
const json=async name=>JSON.parse(await readFile(assetPath(name),'utf8'));
const report={version:'bund-release-three-decode-v4.4',passed:false,started_at:new Date().toISOString(),
 project,ids:args.ids,variants:args.lod?['web','lod']:['web'],bounds_tolerance_m:args.tolerance,
 decoder:'Actual project vendored Three r180 GLTFLoader and MeshoptDecoder; only bare module import paths are remapped in a temporary directory.',
 image_decode:'Pillow fully decodes the original embedded JPEG; Node exposes only decoded dimensions to the GLTFLoader ImageBitmap path. Browser EXIF correction and GPU texture sampling are NOT verified here.',
 browser_started:false,gpu_used:false,files:[],jpeg_decodes:[],metadata_files:{},vendor_sha256:{}};
async function save() {await mkdir(dirname(output),{recursive:true});const temp=output+'.tmp';await writeFile(temp,JSON.stringify(report,null,2)+'\n');await rename(temp,output);}
const bitmapCache=new Map();
const pillowCode=String.raw`import sys,io,json,hashlib
from PIL import Image
b=sys.stdin.buffer.read()
im=Image.open(io.BytesIO(b)); fmt=im.format; raw=list(im.size); exif=int(im.getexif().get(274,1)); im.load()
print(json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'format':fmt,'raw_size':raw,'decoded_size':list(im.size),'exif_orientation':exif,'mode':im.mode,'fully_decoded':True}))
`;
globalThis.self=globalThis;
globalThis.ProgressEvent ||= class ProgressEvent extends Event {constructor(type,options={}){super(type);Object.assign(this,options);}};
globalThis.createImageBitmap=async blob=>{
 const bytes=Buffer.from(await blob.arrayBuffer()), digest=sha(bytes);
 let decoded=bitmapCache.get(digest);
 if(!decoded) {
  const result=spawnSync(args.python,['-c',pillowCode],{input:bytes,encoding:'utf8',maxBuffer:1024*1024,timeout:60000,env:{...process.env,OMP_NUM_THREADS:'1',OPENBLAS_NUM_THREADS:'1'}});
  if(result.error||result.status!==0)throw Error(`JPEG decode failed: ${result.error||result.stderr}`);
  decoded=JSON.parse(result.stdout);assert.equal(decoded.format,'JPEG','Expected embedded JPEG');
  bitmapCache.set(digest,decoded);report.jpeg_decodes.push(decoded);
 }
 return {width:decoded.decoded_size[0],height:decoded.decoded_size[1],audit_sha256:digest,
  audit_adapter:'Pillow-verified dimension-only ImageBitmap adapter; no browser/GPU',close(){this.closed=true;}};
};
// Self-contained GLBs may only fetch their internally created blob URLs.
const originalFetch=globalThis.fetch;
globalThis.fetch=(input,init)=>{const url=typeof input==='string'?input:input.url||String(input);assert(url.startsWith('blob:')||url.startsWith('data:'),`Unexpected external GLTF request: ${url}`);return originalFetch(input,init);};
function parseGLB(buffer) {
 assert(buffer.length>=28&&buffer.readUInt32LE(0)===0x46546c67&&buffer.readUInt32LE(4)===2&&buffer.readUInt32LE(8)===buffer.length,'Invalid GLB header');
 let document=null,binary=null;
 for(let p=12;p<buffer.length;) {const length=buffer.readUInt32LE(p),type=buffer.readUInt32LE(p+4);assert(p+8+length<=buffer.length,'Invalid GLB chunk');const content=buffer.subarray(p+8,p+8+length);if(type===0x4e4f534a)document=JSON.parse(content.toString('utf8'));if(type===0x004e4942)binary=content;p+=8+length;}
 assert(document&&binary,'GLB must contain JSON and BIN');
 assert((document.buffers||[]).every(b=>!b.uri),'External buffers are not allowed');
 const images=(document.images||[]).map(image=>{assert(!image.uri&&Number.isInteger(image.bufferView),'Images must be embedded');const v=document.bufferViews[image.bufferView];assert(v&&v.buffer===0,'Invalid embedded image view');const bytes=binary.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength);assert.equal(bytes.length,v.byteLength);return {sha256:sha(bytes),bytes:bytes.length,mimeType:image.mimeType};});
 return {document,images};
}
function compareBounds(actual,expected,tolerance,label) {
 assert(expected?.min?.length===3&&expected?.max?.length===3,`${label}: missing declared bounds`);
 const differences=['min','max'].flatMap(key=>actual[key].map((v,i)=>Math.abs(v-expected[key][i])));
 const error=Math.max(...differences);assert(error<=tolerance,`${label}: decoded bounds mismatch ${error}m > ${tolerance}m`);return error;
}
const normalizedLicense=x=>String(x).toLowerCase().replace(/[^a-z0-9]/g,'');
let scratch;
try {
 await save();
 const [landmarks,bund,lods]=await Promise.all([json('data/landmarks.json'),json('data/bund/manifest.json'),json('data/bund/lod-v4.json')]);
 for(const file of ['data/landmarks.json','data/bund/manifest.json','data/bund/lod-v4.json'])report.metadata_files[file]=sha(await readFile(assetPath(file)));
 const moduleURL=name=>pathToFileURL(join(project,'vendor',name)).href;
 scratch=await mkdtemp(join(tmpdir(),'shanghai-bund-decode-'));await writeFile(join(scratch,'package.json'),'{"type":"module"}');
 for(const name of ['GLTFLoader.js','BufferGeometryUtils.js']) {const bytes=await readFile(join(project,'vendor',name));report.vendor_sha256[name]=sha(bytes);await writeFile(join(scratch,name),bytes.toString('utf8').replaceAll("from 'three'",`from '${moduleURL('three.module.js')}'`));}
 for(const name of ['three.module.js','three.core.js','meshopt_decoder.module.js'])report.vendor_sha256[name]=sha(await readFile(join(project,'vendor',name)));
 const THREE=await import(moduleURL('three.module.js'));
 const {GLTFLoader}=await import(pathToFileURL(join(scratch,'GLTFLoader.js')).href);
 const {MeshoptDecoder}=await import(moduleURL('meshopt_decoder.module.js'));await MeshoptDecoder.ready;
 const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);report.three_revision=THREE.REVISION;
 for(const id of args.ids) {
  const found=landmarks.filter(r=>r.id===id);assert.equal(found.length,1,`${id}: duplicate/missing navigation record`);const record=found[0];
  assert.deepEqual(bund.buildings.find(r=>r.id===id),record,`${id}: Bund/navigation metadata differ`);
  const webMetadata=`data/bund/models/${id}-web.json`;assert.deepEqual(await json(webMetadata),record,`${id}: per-model/navigation metadata differ`);report.metadata_files[webMetadata]=sha(await readFile(assetPath(webMetadata)));
  const lod=lods.models.find(r=>r.id===id);assert(lod,`${id}: missing LOD record`);
  for(const [name,key] of [['model','lod_model'],['sha256','lod_sha256'],['bytes','lod_bytes'],['triangles','lod_triangles'],['full_triangles','triangles'],['switch_out_distance_m','lod_switch_out_m'],['switch_in_distance_m','lod_switch_in_m'],['full_model_unchanged_sha256','raw_sha256'],['close_up_web_unchanged_sha256','web_sha256'],['native_unchanged_sha256','native_sha256']])assert.equal(lod[name],record[key],`${id}: LOD summary ${name} differs`);
  if(lod.generation) {assert.equal(lod.generation.triangles,lod.triangles,`${id}: LOD generation triangle count is stale`);assert.equal(lod.generation.bytes,lod.bytes,`${id}: LOD generation bytes are stale`);}
  assert(Number.isFinite(record.lng)&&Number.isFinite(record.lat)&&record.height_m>0,`${id}: invalid anchor/height`);
  assert(Math.abs(record.bounds_glb.max[1]-record.height_m)<.01,`${id}: height and model envelope disagree`);
  for(const variant of report.variants) {
   const file=variant==='web'?record.model:record.lod_model;const bytes=await readFile(assetPath(file));
   assert(bytes.length<100000000,`${id}: exceeds100MB`);assert.equal(bytes.length,record[variant==='web'?'web_bytes':'lod_bytes'],`${id}: ${variant} bytes`);assert.equal(sha(bytes),record[variant==='web'?'web_sha256':'lod_sha256'],`${id}: ${variant} hash`);
   const {document,images}=parseGLB(bytes);const photo=record.photo_texture;const expectedImages=photo?.expected_images?.[variant]??0;assert([0,1].includes(expectedImages),'Only0/1 source image is supported');assert.equal(images.length,expectedImages,`${id}: ${variant} image count`);
   if(expectedImages) {assert.equal(images[0].sha256,photo.sha256,`${id}: embedded photograph changed`);assert.equal(images[0].bytes,photo.bytes,`${id}: embedded JPEG byte count`);assert.equal(images[0].mimeType,'image/jpeg');assert(document.asset.copyright?.includes(photo.author),`${id}: photographer attribution missing`);assert(normalizedLicense(document.asset.copyright).includes(normalizedLicense(photo.license)),`${id}: photo license missing`);const source=await readFile(assetPath(photo.image));assert.equal(sha(source),photo.sha256,`${id}: original JPEG source hash`);}
   const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');gltf.scene.updateMatrixWorld(true);
   const bounds=new THREE.Box3(),point=new THREE.Vector3(),instance=new THREE.Matrix4(),transform=new THREE.Matrix4();
   let triangles=0,referencedVertices=0,meshes=0,mappedPhotoMeshes=0;const textures=new Set(),geometries=new Set(),materials=new Set(),bitmaps=new Set();
   gltf.scene.traverse(mesh=>{
    if(!mesh.isMesh)return;meshes++;const geometry=mesh.geometry;geometries.add(geometry);const position=geometry.getAttribute('position'),index=geometry.index;assert(position,`${id}: missing positions`);const count=index?.count??position.count;assert.equal(count%3,0,`${id}: non-triangle primitive`);
    const ids=index?new Set(Array.from({length:index.count},(_,i)=>index.getX(i))):Array.from({length:position.count},(_,i)=>i);const instances=mesh.isInstancedMesh?mesh.count:1;triangles+=count/3*instances;
    for(let k=0;k<instances;k++) {if(mesh.isInstancedMesh){mesh.getMatrixAt(k,instance);transform.multiplyMatrices(mesh.matrixWorld,instance);}else transform.copy(mesh.matrixWorld);for(const i of ids){assert(Number.isInteger(i)&&i>=0&&i<position.count,`${id}: index outside position array`);point.fromBufferAttribute(position,i).applyMatrix4(transform);assert([point.x,point.y,point.z].every(Number.isFinite),`${id}: nonfinite decoded vertex`);bounds.expandByPoint(point);referencedVertices++;}}
    for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]) {materials.add(material);for(const value of Object.values(material))if(value?.isTexture){textures.add(value);if(value.image)bitmaps.add(value.image);}if(/^PhotoFacade_/i.test(material.name)&&material.map){mappedPhotoMeshes++;const uv=geometry.getAttribute('uv');assert(uv&&uv.count===position.count,`${id}: mapped photograph lacks per-vertex UV`);for(let i=0;i<uv.count;i++)assert(Number.isFinite(uv.getX(i))&&Number.isFinite(uv.getY(i)),`${id}: invalid photo UV`);}}
   });
   assert(!bounds.isEmpty()&&meshes>0,`${id}: empty decoded scene`);assert.equal(triangles,variant==='web'?record.triangles:record.lod_triangles,`${id}: actual Three triangle count differs`);const actualBounds={min:bounds.min.toArray(),max:bounds.max.toArray()};const boundsError=compareBounds(actualBounds,variant==='web'?record.bounds_glb:lod.lod_bounds_glb,args.tolerance,`${id}/${variant}`);
   const decodedImages=[...bitmaps].filter(image=>image.audit_sha256);assert.equal(decodedImages.length,expectedImages,`${id}: actual loader image count`);assert.equal(mappedPhotoMeshes>0,expectedImages===1,`${id}: mapped PhotoFacade presence`);
   for(const image of decodedImages){const decoded=bitmapCache.get(image.audit_sha256);assert.equal(image.audit_sha256,photo.sha256);assert.deepEqual(decoded.raw_size,photo.orientation.rawSize,`${id}: JPEG stored dimensions`);assert.deepEqual(decoded.raw_size,photo.dimensions_px,`${id}: JPEG dimension metadata disagree`);assert.equal(decoded.exif_orientation,photo.orientation.exifOrientation,`${id}: EXIF metadata disagree`);assert.equal(photo.orientation.uvConvention,'stored-pixels');}
   report.files.push({id,variant,file,sha256:sha(bytes),bytes:bytes.length,meshes,triangles,referenced_vertices:referencedVertices,bounds:actualBounds,maximum_declared_bounds_error_m:boundsError,images,mapped_photo_meshes:mappedPhotoMeshes,metadata_consistent:true,passed:true});
   for(const g of geometries)g.dispose();for(const m of materials)m.dispose();for(const t of textures)t.dispose();for(const image of bitmaps)image.close?.();
   console.log('DECODED',id,variant,triangles,'triangles',images.length,'JPEG');await save();
  }
 }
 assert.equal(report.files.length,args.ids.length*report.variants.length,'Incomplete decode coverage');report.passed=true;report.finished_at=new Date().toISOString();await save();console.log('PASS',report.files.length,'GLBs',output);
} catch(error) {report.error=error.stack||String(error);report.finished_at=new Date().toISOString();await save();throw error;}
finally {if(scratch)await rm(scratch,{recursive:true,force:true});}
