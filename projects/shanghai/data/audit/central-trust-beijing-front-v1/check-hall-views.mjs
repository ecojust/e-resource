import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
globalThis.self=globalThis;
const out=dirname(fileURLToPath(import.meta.url));
const project=fileURLToPath(new URL('../../../',import.meta.url));
const readModelDir=process.argv[2] || join(project,'assets/models/candidates/huangpu-central-trust-beijing-front');
const pub=name=>pathToFileURL(join(project,name)).href;
const THREE=await import('three');
const {GLTFLoader}=await import(pub('vendor/GLTFLoader.js'));
const {MeshoptDecoder}=await import(pub('vendor/meshopt_decoder.module.js'));
const {disposeModelResources}=await import(pub('src/model-resources.js'));
const sha=data=>createHash('sha256').update(data).digest('hex');
const html=await readFile(join(project,'central-trust-beijing-front.html'),'utf8');
const plan=JSON.parse(await readFile(join(project,'source/precise/huangpu-central-trust-beijing-front/source/plan-registration.json')));
const snippet=html.slice(html.indexOf('    const corners = '),html.indexOf('    function release()'));
const geometry=Function(snippet+';return {centreline,soffit,corners};')();
if(JSON.stringify(geometry.corners)!==JSON.stringify(plan.hall_opening_xy_m))throw Error('viewer and plan differ');
const manifest=JSON.parse(await readFile(join(readModelDir,'manifest.json'),'utf8'));
const details=[];
const start=html.slice(html.indexOf('    function choose(view)'),html.indexOf('    function keyboard'));
if(!start.includes('centreline(under ? .22 : .15, under ? soffit-4.45 : soffit+6.7)') ||
   !start.includes('centreline(under ? .46 : .48, under ? soffit+.14 : soffit+.55)')) throw Error('preset drift');
for(const role of ['full','lod']){
  const asset=manifest.assets[role];
  const buffer=await readFile(join(readModelDir,asset.file));
  if(buffer.length!==asset.bytes || sha(buffer)!==asset.sha256)throw Error('asset signature invalid');
  const {scene}=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(buffer.buffer.slice(buffer.byteOffset,buffer.byteOffset+buffer.byteLength),'');
  scene.updateMatrixWorld(true);
  let triangles=0;scene.traverse(m=>{if(m.isMesh)triangles+=(m.geometry.index?.count??m.geometry.attributes.position.count)/3;});
  for(const [w,h] of [[890,555],[368,464]]){
    for(const under of [true,false]){
      const camera=new THREE.PerspectiveCamera(under?(w/h<1.1?65:53):(w/h<1.1?74:61),w/h,.035,160);
      camera.position.fromArray(geometry.centreline(under?.22:.15,under?geometry.soffit-4.45:geometry.soffit+6.7));
      const target=new THREE.Vector3(...geometry.centreline(under?.46:.48,under?geometry.soffit+.14:geometry.soffit+.55));
      if(under)target.x+=.26;
      camera.lookAt(target);camera.updateMatrixWorld(true);
      const ray=new THREE.Raycaster();
      const observed={};const overlay=[];
      for(const y of [-.81,-.55,-.25,0,.25,.55,.81]){
        for(const x of [-.80,-.53,-.26,0,.26,.53,.80]){
          ray.setFromCamera(new THREE.Vector2(x,y),camera);
          const first=ray.intersectObject(scene,true)[0];
          const mat=first? (Array.isArray(first.object.material) ? first.object.material[first.face.materialIndex] : first.object.material).name:'empty';
          observed[mat]=(observed[mat]||0)+1;
          if(x===0||y===0)overlay.push({x,y,first:mat,point:first?.point.toArray()});
        }
      }
      const centre=overlay.find(a=>a.x===0&&a.y===0).first;
      if(under ? !centre.startsWith('Trust skylight') || /weather|zinc/.test(centre)
               : !/weather|zinc/.test(centre))throw Error('centre obscured '+centre);
      details.push({role,viewport:[w,h],view:under?'under':'courtyard',assets:asset.sha256,triangles,centre,observed,axes:overlay});
    }
  }
  disposeModelResources(scene);
}
const destination=process.argv[3]||join(out,'hall-camera-and-gltf.json');
await writeFile(destination,JSON.stringify({passed:true,html_sha256:sha(html),manifest_sha256:sha(await readFile(join(readModelDir,'manifest.json'))),source:readModelDir,details},null,2)+'\n');
console.log(details.map(a=>[a.role,a.viewport,a.view,a.centre,a.observed]));
