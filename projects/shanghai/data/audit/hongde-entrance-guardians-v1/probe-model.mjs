/* Intersect one real GLB in a separate process to bound decoder memory. */
import {readFile, writeFile, mkdtemp, rm} from 'node:fs/promises';
import {resolve, join} from 'node:path';
import {tmpdir} from 'node:os';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const [project,file,baselineFile,output]=process.argv.slice(2).map(s=>resolve(s));
const {north_edge:e}=JSON.parse(await readFile(baselineFile));
const vec=(u,d,z)=>{
  const east=e.center_local_east_north_m[0]-u*e.tangent_east_north[0]-d*e.outward_normal_east_north[0];
  const north=e.center_local_east_north_m[1]-u*e.tangent_east_north[1]-d*e.outward_normal_east_north[1];
  return [east,z,-north];
};
const sha=b=>createHash('sha256').update(b).digest('hex');
const temporary=await mkdtemp(join(tmpdir(),'hongde-probes-'));
const url=name=>pathToFileURL(join(project,'vendor',name)).href;
try {
  await writeFile(join(temporary,'package.json'),'{"type":"module"}');
  for (const name of ['GLTFLoader.js','BufferGeometryUtils.js']) {
    const src=(await readFile(join(project,'vendor',name),'utf8')).replaceAll("from 'three'",`from '${url('three.module.js')}'`);
    await writeFile(join(temporary,name),src);
  }
  const {GLTFLoader}=await import(pathToFileURL(join(temporary,'GLTFLoader.js')).href);
  const T=await import(url('three.module.js'));
  const {MeshoptDecoder}=await import(url('meshopt_decoder.module.js'));
  await MeshoptDecoder.ready;
  const data=await readFile(file);
  const scene=(await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'' )).scene;
  scene.updateMatrixWorld(true);
  let triangles=0;scene.traverse(n=>{if(n.isMesh)triangles+=(n.geometry.index?.count??n.geometry.attributes.position.count)/3;});
  const probes=[];
  function record(name,origin,direction,max=20){
    const o=new T.Vector3(...vec(...origin));
    const tip=new T.Vector3(...vec(origin[0]+direction[0],origin[1]+direction[1],origin[2]+direction[2]));
    const ray=new T.Raycaster(o,tip.sub(o).normalize(),0,max);
    const hit=ray.intersectObject(scene,true)[0];
    probes.push({name,origin_u_depth_z_m:origin,direction_u_depth_z:direction,result:hit?{distance_m:hit.distance,material:hit.object.material.name,point_gltf_m:hit.point.toArray()}:null});
  }
  for (const side of [-1,1]){
    const name=side<0?'east':'west',u=1.95*side;
    for (const [part,x,d] of [['crest',0,-.52],['back mane',.045,-.427],['outside shoulder',.14,-.58],['front paws',side*.15,-.739],['raised forepaw',-side*.15,-.739]]){
      record(name+' top '+part,[u+x,d,2.25],[0,0,-1]);
    }
    for (const [part,x,z] of [['muzzle',0,1.512],['chest',.011,1.25],['near hip',.181,1.031],['brow',.073,1.575]]){
      record(name+' front '+part,[u+x,-1.38,z],[0,1,0]);
    }
    record(name+' outside clear',[u+.42*side,-.48,2.25],[0,0,-1]);
  }
  for (const u of [-.68,0,.68]){
    record('middle stair '+u,[u,-.72,2.5],[0,0,-1]);
    record('central doorway '+u,[u,-1.50,1.40],[0,1,0]);
  }
  record('farther up the original tower',[.012,-3,5.38],[0,1,0]);
  record('central roof crown',[.17,2,27],[0,0,-1]);
  await writeFile(output,JSON.stringify({file,sha256:sha(data),triangles,probes},null,2)+'\n');
} finally {await rm(temporary,{recursive:true,force:true});}
