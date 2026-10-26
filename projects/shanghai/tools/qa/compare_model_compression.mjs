/** Verify exact oriented triangle positions and bounded normal-direction error. */
import {readFile,writeFile,mkdtemp,rm} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const [projectArg,rawArg,webArg,output]=process.argv.slice(2);
if (!projectArg || !rawArg || !webArg) throw Error('Usage: node compare_model_compression.mjs PROJECT RAW_GLB WEB_GLB [REPORT]');
const project=resolve(projectArg), scratch=await mkdtemp(join(tmpdir(),'shanghai-compression-'));
const url=name=>pathToFileURL(join(project,'vendor',name)).href;
try {
  await writeFile(join(scratch,'package.json'),'{"type":"module"}');
  for (const name of ['GLTFLoader.js','BufferGeometryUtils.js']) {
    const code=(await readFile(join(project,'vendor',name),'utf8')).replaceAll("from 'three'",`from '${url('three.module.js')}'`);
    await writeFile(join(scratch,name),code);
  }
  const THREE=await import(url('three.module.js'));
  const {GLTFLoader}=await import(pathToFileURL(join(scratch,'GLTFLoader.js')).href);
  const {MeshoptDecoder}=await import(url('meshopt_decoder.module.js'));
  await MeshoptDecoder.ready;
  const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  // This CPU check inspects geometry/UVs. The browser check decodes the actual
  // embedded photo; do not require a fake DOM image decoder inside Node.
  loader.register(()=>({name:'CPU_geometry_texture_placeholder',loadTexture:()=>Promise.resolve(new THREE.Texture())}));
  async function decode(file) {
    const bytes=await readFile(file), gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
    gltf.scene.updateMatrixWorld(true);
    const triangles=new Map(), counts={};
    gltf.scene.traverse(mesh=>{
      if (!mesh.isMesh) return;
      if (mesh.isInstancedMesh || Array.isArray(mesh.material)) throw Error('This comparison expects one material per non-instanced mesh.');
      // Optimizers may remove unused UVs from untextured materials. Only a
      // mapped material's UVs affect the photographed facade appearance.
      const p=mesh.geometry.getAttribute('position'),n=mesh.geometry.getAttribute('normal'),uv=mesh.material.map?mesh.geometry.getAttribute('uv'):null,index=mesh.geometry.index;
      if (!n) throw Error('Normal attribute is required.');
      const normalMatrix=new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
      const keyAt=i=>{
        const vertex=index?index.getX(i):i;
        const position=new THREE.Vector3().fromBufferAttribute(p,vertex).applyMatrix4(mesh.matrixWorld);
        const normal=new THREE.Vector3().fromBufferAttribute(n,vertex).applyMatrix3(normalMatrix);
        const values=[...position.toArray(),...normal.toArray()];
        if (!values.every(Number.isFinite)) throw Error('Nonfinite decoded geometry.');
        return {position:JSON.stringify(position.toArray()),normal:normal.toArray(),uv:uv?[uv.getX(vertex),uv.getY(vertex)]:[]};
      };
      const count=index?.count||p.count;
      if (count%3) throw Error('Incomplete triangle.');
      const material=mesh.material.name;
      for (let i=0;i<count;i+=3) {
        const v=[keyAt(i),keyAt(i+1),keyAt(i+2)];
        const cycles=[v,[v[1],v[2],v[0]],[v[2],v[0],v[1]]];
        cycles.sort((a,b)=>a.map(x=>x.position).join('|').localeCompare(b.map(x=>x.position).join('|')));
        const ordered=cycles[0],key=material+':'+ordered.map(x=>x.position).join('|');
        if (!triangles.has(key)) triangles.set(key,[]);
        triangles.get(key).push([...ordered.flatMap(x=>x.normal),...ordered.flatMap(x=>x.uv)]);
      }
      counts[material]=(counts[material]||0)+count/3;
      mesh.geometry.dispose();mesh.material.dispose();
    });
    return {file:resolve(file),bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),counts,triangles};
  }
  const raw=await decode(rawArg),web=await decode(webArg);
  const unmatched=[];
  let maximumStoredNormalComponentDifference=0,maximumNormalizedNormalComponentDifference=0,maximumNormalAngleDegrees=0,maximumUVComponentDifference=0;
  for (const [key,rawNormals] of raw.triangles) {
    const webNormals=web.triangles.get(key);
    if (!webNormals || webNormals.length!==rawNormals.length) {unmatched.push(key.slice(0,180));continue;}
    // Identical triangles can occur more than once. Sort their normal records
    // deterministically before comparing the complete multiset.
    rawNormals.sort();webNormals.sort();
    for (let i=0;i<rawNormals.length;i++) {
      if(rawNormals[i].length!==webNormals[i].length)throw Error('UV attribute coverage differs');
      for(let j=9;j<rawNormals[i].length;j++) maximumUVComponentDifference=Math.max(maximumUVComponentDifference,Math.abs(rawNormals[i][j]-webNormals[i][j]));
    }
    for (let i=0;i<rawNormals.length;i++) for (let j=0;j<9;j+=3) {
      const a=rawNormals[i].slice(j,j+3),b=webNormals[i].slice(j,j+3);
      const al=Math.hypot(...a),bl=Math.hypot(...b);
      if (!al || !bl) throw Error('Zero-length normal.');
      const cosine=Math.max(-1,Math.min(1,a.reduce((sum,value,k)=>sum+value*b[k],0)/(al*bl)));
      maximumNormalAngleDegrees=Math.max(maximumNormalAngleDegrees,Math.acos(cosine)*180/Math.PI);
      for (let k=0;k<3;k++) {
        maximumStoredNormalComponentDifference=Math.max(maximumStoredNormalComponentDifference,Math.abs(a[k]-b[k]));
        maximumNormalizedNormalComponentDifference=Math.max(maximumNormalizedNormalComponentDifference,Math.abs(a[k]/al-b[k]/bl));
      }
    }
  }
  if (raw.triangles.size!==web.triangles.size || unmatched.length) throw Error(JSON.stringify({unmatched:unmatched.length,examples:unmatched.slice(0,2),rawUnique:raw.triangles.size,webUnique:web.triangles.size}));
  // The geometry requirement is exact vertex positions. Exporter processing
  // may slightly alter normal directions even for Float32 attributes; report
  // the measured deviation and enforce a 0.05 degree rendering tolerance.
  const normalAngleToleranceDegrees=0.05;
  if(maximumUVComponentDifference>1e-7)throw Error(JSON.stringify({maximumUVComponentDifference}));
  if (maximumNormalAngleDegrees>normalAngleToleranceDegrees) throw Error(JSON.stringify({maximumNormalAngleDegrees,normalAngleToleranceDegrees}));
  delete raw.triangles;delete web.triangles;
  const report={passed:true,decoder:'Vendored Three GLTFLoader and MeshoptDecoder used by the viewer',texture_pixels_decoded:false,maximumUVComponentDifference,comparison:'Exact raw/web world-space oriented-triangle position multiset and material names. Cyclic vertex order normalized; normal direction and UV errors measured separately. Embedded photo pixels are checked in the browser.',normalAngleToleranceDegrees,maximumNormalAngleDegrees,maximumStoredNormalComponentDifference,maximumNormalizedNormalComponentDifference,raw,web};
  if (output) await writeFile(output,JSON.stringify(report,null,2)+'\n');
  console.log('PASS',Object.values(raw.counts).reduce((a,b)=>a+b,0),'oriented triangle positions exact; maximum normalized normal difference',maximumNormalizedNormalComponentDifference);
} finally {await rm(scratch,{recursive:true,force:true});}
