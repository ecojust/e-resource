/** Decode each final asset with the viewer's real loaders, including world TRS. */
import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const [projectArg,workArg]=process.argv.slice(2);
if(!projectArg||!workArg)throw Error('Usage: node decode_assets.mjs PROJECT WORKDIR');
const project=resolve(projectArg),work=resolve(workArg),scratch=await mkdtemp(join(tmpdir(),'art-deco-decode-'));
const url=name=>pathToFileURL(join(project,'vendor',name)).href;
try {
  await writeFile(join(scratch,'package.json'),'{"type":"module"}');
  for(const name of ['GLTFLoader.js','BufferGeometryUtils.js'])await writeFile(join(scratch,name),(await readFile(join(project,'vendor',name),'utf8')).replaceAll("from 'three'",`from '${url('three.module.js')}'`));
  const THREE=await import(url('three.module.js'));
  const {GLTFLoader}=await import(pathToFileURL(join(scratch,'GLTFLoader.js')).href);
  const {MeshoptDecoder}=await import(url('meshopt_decoder.module.js'));await MeshoptDecoder.ready;
  const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  async function decode(file) {
    const bytes=await readFile(file),doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
    if(doc.images?.length)throw Error('This untextured wall release must not acquire photographs.');
    const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');gltf.scene.updateMatrixWorld(true);
    const bounds=new THREE.Box3(),vector=new THREE.Vector3();let triangles=0,meshes=0;const materials=new Set();
    gltf.scene.traverse(mesh=>{
      if(!mesh.isMesh)return;if(mesh.isInstancedMesh)throw Error('Unexpected instanced asset');
      meshes++;const p=mesh.geometry.getAttribute('position'),n=mesh.geometry.getAttribute('normal'),index=mesh.geometry.index;
      const ids=index?new Set(Array.from({length:index.count},(_,i)=>index.getX(i))):Array.from({length:p.count},(_,i)=>i);
      for(const i of ids){vector.fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld);if(!vector.toArray().every(Number.isFinite))throw Error('Nonfinite decoded position');bounds.expandByPoint(vector);}
      if(!n)throw Error('Missing normals');triangles+=(index?.count||p.count)/3;
      for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]){materials.add(material.name);material.dispose();}
      mesh.geometry.dispose();
    });
    return {file,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),triangles,meshes,materials:[...materials].sort(),bounds:{min:bounds.min.toArray(),max:bounds.max.toArray()},copyright:doc.asset.copyright,images:doc.images?.length||0,extensionsRequired:doc.extensionsRequired||[]};
  }
  const reports=[];
  for(const id of ['bund19','bund20','bund23']) {
    const directory=join(work,'candidate',id),assets={};
    for(const [role,name]of [['raw',`${id}.glb`],['web',`${id}-web.glb`],['lod',`${id}-lod.glb`]])assets[role]=await decode(join(directory,name));
    const delta=role=>Math.max(...['min','max'].flatMap(key=>assets.raw.bounds[key].map((value,i)=>Math.abs(value-assets[role].bounds[key][i]))));
    const webBoundsDifferenceMetres=delta('web'),lodBoundsDifferenceMetres=delta('lod');
    if(assets.raw.triangles!==assets.web.triangles||webBoundsDifferenceMetres>0.0001||lodBoundsDifferenceMetres>0.05)throw Error(JSON.stringify({id,assets,webBoundsDifferenceMetres,lodBoundsDifferenceMetres}));
    if(!assets.lod.triangles||assets.lod.triangles>=assets.web.triangles)throw Error('LOD did not reduce geometry: '+id);
    const report={id,passed:true,decoder:'Actual vendored Three GLTFLoader + MeshoptDecoder; node world transforms applied to referenced vertices',webBoundsToleranceMetres:0.0001,lodBoundsToleranceMetres:0.05,webBoundsDifferenceMetres,lodBoundsDifferenceMetres,assets};
    await writeFile(join(directory,'decoded-assets.json'),JSON.stringify(report,null,2)+'\n');reports.push(report);
    console.log(id,'triangles',assets.raw.triangles,assets.lod.triangles,'web/LOD bounds delta m',webBoundsDifferenceMetres,lodBoundsDifferenceMetres);
  }
  await writeFile(join(work,'decoded-assets.json'),JSON.stringify({passed:true,models:reports},null,2)+'\n');
} finally {await rm(scratch,{recursive:true,force:true});}
