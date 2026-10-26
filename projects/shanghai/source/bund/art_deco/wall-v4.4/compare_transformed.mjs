/** Oriented-triangle bijection with bounded world-transform rounding error. */
import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const [projectArg,rawArg,webArg,output]=process.argv.slice(2);
if(!projectArg||!rawArg||!webArg||!output)throw Error('Usage: node compare_transformed.mjs PROJECT RAW WEB REPORT');
const project=resolve(projectArg),scratch=await mkdtemp(join(tmpdir(),'bund-transform-'));
const tolerance=0.0001,normalToleranceDegrees=0.05,url=name=>pathToFileURL(join(project,'vendor',name)).href;
try {
  await writeFile(join(scratch,'package.json'),'{"type":"module"}');
  for(const name of ['GLTFLoader.js','BufferGeometryUtils.js'])await writeFile(join(scratch,name),(await readFile(join(project,'vendor',name),'utf8')).replaceAll("from 'three'",`from '${url('three.module.js')}'`));
  const THREE=await import(url('three.module.js'));
  const {GLTFLoader}=await import(pathToFileURL(join(scratch,'GLTFLoader.js')).href);
  const {MeshoptDecoder}=await import(url('meshopt_decoder.module.js'));await MeshoptDecoder.ready;
  const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  async function decode(file) {
    const bytes=await readFile(file),gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');gltf.scene.updateMatrixWorld(true);
    const triangles=[],counts={};
    gltf.scene.traverse(mesh=>{
      if(!mesh.isMesh)return;if(mesh.isInstancedMesh||Array.isArray(mesh.material)||mesh.material.map)throw Error('Expected untextured, non-instanced primitive');
      const p=mesh.geometry.getAttribute('position'),n=mesh.geometry.getAttribute('normal'),index=mesh.geometry.index;
      const normalMatrix=new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld),cache=new Map(),count=index?.count||p.count,material=mesh.material.name;
      function at(offset){const id=index?index.getX(offset):offset;if(cache.has(id))return cache.get(id);const position=new THREE.Vector3().fromBufferAttribute(p,id).applyMatrix4(mesh.matrixWorld),normal=new THREE.Vector3().fromBufferAttribute(n,id).applyMatrix3(normalMatrix).normalize();const row=[...position.toArray(),...normal.toArray()];if(!row.every(Number.isFinite)||!normal.lengthSq())throw Error('Invalid geometry');cache.set(id,row);return row;}
      for(let i=0;i<count;i+=3){const data=new Float64Array([...at(i),...at(i+1),...at(i+2)]);const center=[0,1,2].map(k=>(data[k]+data[k+6]+data[k+12])/3);triangles.push({material,data,center,used:false});}
      counts[material]=(counts[material]||0)+count/3;mesh.geometry.dispose();mesh.material.dispose();
    });
    return {triangles,counts,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),file:resolve(file)};
  }
  const raw=await decode(rawArg),web=await decode(webArg);
  if(raw.triangles.length!==web.triangles.length)throw Error('Triangle counts differ');
  const bins=new Map(),bucket=center=>center.map(x=>Math.floor(x/tolerance)),key=(material,b)=>material+'|'+b.join(',');
  for(const row of raw.triangles){const k=key(row.material,bucket(row.center));if(!bins.has(k))bins.set(k,[]);bins.get(k).push(row);}
  let maximumPositionDifferenceMetres=0,maximumNormalAngleDegrees=0,matched=0;
  for(const row of web.triangles){
    const b=bucket(row.center);let best=null,bestDistance=Infinity,bestAngle=Infinity;
    for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)for(const candidate of bins.get(key(row.material,[b[0]+x,b[1]+y,b[2]+z]))||[]){
      if(candidate.used)continue;
      for(let shift=0;shift<3;shift++){
        let distance=0,angle=0;
        for(let v=0;v<3;v++){
          const a=v*6,c=((v+shift)%3)*6;
          distance=Math.max(distance,Math.hypot(row.data[a]-candidate.data[c],row.data[a+1]-candidate.data[c+1],row.data[a+2]-candidate.data[c+2]));
          const dot=row.data[a+3]*candidate.data[c+3]+row.data[a+4]*candidate.data[c+4]+row.data[a+5]*candidate.data[c+5];
          angle=Math.max(angle,Math.acos(Math.max(-1,Math.min(1,dot)))*180/Math.PI);
        }
        if(distance<=tolerance&&angle<=normalToleranceDegrees&&(distance<bestDistance||(distance===bestDistance&&angle<bestAngle))){best=candidate;bestDistance=distance;bestAngle=angle;}
      }
    }
    if(!best)throw Error(JSON.stringify({unmatchedOrientedTriangle:row.material,center:row.center,tolerance,matched}));
    best.used=true;matched++;maximumPositionDifferenceMetres=Math.max(maximumPositionDifferenceMetres,bestDistance);maximumNormalAngleDegrees=Math.max(maximumNormalAngleDegrees,bestAngle);
  }
  if(raw.triangles.some(row=>!row.used))throw Error('Unmatched raw triangles');
  delete raw.triangles;delete web.triangles;
  const report={passed:true,decoder:'Actual vendored Three GLTFLoader and MeshoptDecoder; all node world transforms applied',comparison:'One-to-one oriented-triangle matching by material and three cyclic vertex orders. Same winding/counts; each actual vertex and normal measured. No raw vertex coalescing.',positionToleranceMetres:tolerance,normalToleranceDegrees,matchedTriangles:matched,maximumPositionDifferenceMetres,maximumNormalAngleDegrees,exactWorldPositions:maximumPositionDifferenceMetres===0,raw,web};
  await writeFile(output,JSON.stringify(report,null,2)+'\n');console.log('PASS',matched,'triangles; world difference metres',maximumPositionDifferenceMetres,'normal degrees',maximumNormalAngleDegrees);
} finally {await rm(scratch,{recursive:true,force:true});}
