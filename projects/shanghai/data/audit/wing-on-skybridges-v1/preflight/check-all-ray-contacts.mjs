// Cross-sections of the distributed neighbors at the modeled bridge ends, in metres.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {registerHooks} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';

const audit=path.dirname(fileURLToPath(import.meta.url));
const project=process.env.SHANGHAI_PROJECT_ROOT || path.resolve(audit,'../../..');
const commit='92fd7a57326abaff1538d5f478d1a593ad6896c0';
const repo=path.resolve(project,'../..');
const digest=b=>createHash('sha256').update(b).digest('hex');
const readAt=p=>execFileSync('git',['show',commit+':projects/shanghai/'+p],{cwd:repo,maxBuffer:100000000});
registerHooks({resolve(specifier,context,next){
  return specifier==='three'?{url:pathToFileURL(path.join(project,'vendor/three.module.js')).href,shortCircuit:true}:next(specifier,context);
}});
const {GLTFLoader}=await import(path.join(project,'vendor/GLTFLoader.js'));
const {MeshoptDecoder}=await import(path.join(project,'vendor/meshopt_decoder.module.js'));
const {Vector3,Matrix4}=await import(path.join(project,'vendor/three.module.js'));
const contract=JSON.parse(fs.readFileSync(path.join(audit,'final-placement-contract.json')));
const base=JSON.parse(readAt('data/candidate-city-integrations.json'));
const ids=['huangpu-old-wing-on-company','huangpu-new-wing-on-company'];
const expectedEnd=[-5.65,5.65];
const rad=Math.PI/180;
const expectedSamples=[];
for(const depth of [-2,-1,0,1,2])for(const elevation of [13.1,15,17.5,20.4])expectedSamples.push({depth,elevation});
const results=[];
for(const [side,id] of ids.entries()){
  const r=base.models.find(r=>r.id===id);
  const offsetEast=(r.lng-contract.lng)*rad*6378137*Math.cos(contract.lat*rad);
  const offsetNorth=(r.lat-contract.lat)*rad*6378137;
  const parentAngle=r.heading*rad,angle=-contract.heading*rad;
  function bridgeSpace(p){
    const east=offsetEast+(Math.cos(parentAngle)*p.x-Math.sin(parentAngle)*p.z)*r.scale;
    const north=offsetNorth-(Math.sin(parentAngle)*p.x+Math.cos(parentAngle)*p.z)*r.scale;
    return [east*Math.cos(angle)+north*Math.sin(angle),-east*Math.sin(angle)+north*Math.cos(angle),p.y*r.scale+(r.altitude||0)];
  }
  for(const variant of ['web','lod']){
    const asset=r.assets[variant],b=readAt(asset.file);assert.equal(digest(b),asset.sha256);
    const gltf=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');
    gltf.scene.updateMatrixWorld(true);
    const probes=expectedSamples.map(probe=>({...probe,wallX:side===0?-Infinity:Infinity}));let triangleCount=0;
    gltf.scene.traverseVisible(node=>{
      if(!node.isMesh)return;
      const geo=node.geometry,pos=geo.getAttribute('position'),indices=geo.index;
      const start=geo.drawRange.start,end=Math.min(indices?.count??pos.count,start+geo.drawRange.count);
      for(let inst=0;inst<(node.isInstancedMesh?node.count:1);inst++){
        const matrix=node.matrixWorld.clone();
        if(node.isInstancedMesh){const local=new Matrix4();node.getMatrixAt(inst,local);matrix.multiply(local);}
        function point(i){return bridgeSpace(new Vector3().fromBufferAttribute(pos,indices?indices.getX(i):i).applyMatrix4(matrix));}
        for(let i=start;i<end;i+=3){
          triangleCount++;
          const [a,b,c]=[point(i),point(i+1),point(i+2)];
          const du=b[1]-a[1],dv=b[2]-a[2],eu=c[1]-a[1],ev=c[2]-a[2],det=du*ev-dv*eu;
          if(Math.abs(det)<1e-9)continue;
          for(const probe of probes){
            const y=probe.depth-a[1],z=probe.elevation-a[2],s=(y*ev-z*eu)/det,t=(du*z-dv*y)/det;
            if(s<0||t<0||s+t>1)continue;
            const x=a[0]+s*(b[0]-a[0])+t*(c[0]-a[0]);
            probe.wallX=side===0?Math.max(x,probe.wallX):Math.min(x,probe.wallX);
          }
        }
      }
    });
    for(const p of probes){
      if(!Number.isFinite(p.wallX))console.log('No surface',id,variant,p.depth,p.elevation);
      p.penetration_m=(side===0?1:-1)*(p.wallX-expectedEnd[side]);
    }
    results.push({parent:id,variant,assetSha256:digest(b),triangles:triangleCount,owner:r.owner,probes,
      minimumEndOverlap_m:Math.min(...probes.map(p=>p.penetration_m)),maximumEndOverlap_m:Math.max(...probes.map(p=>p.penetration_m))});
  }
}
const report={referenceCommit:commit,scriptSha256:digest(fs.readFileSync(fileURLToPath(import.meta.url))),model:contract.id,
  contractSha256:digest(fs.readFileSync(path.join(audit,'final-placement-contract.json'))),
  method:'Intersect along the span at 20 positions on each modeled end plane with the actual visible triangles of each parent map GLB, including node and instance transforms. Positive overlap means the nominal end enters the outermost facade surface. Heights, depths and location are estimates. Tangency and decorative projections do not establish structural attachment.',
  expectedEnd,results,passed:results.every(r=>r.minimumEndOverlap_m>=0)};
fs.writeFileSync(path.join(audit,'attachment-check.json'),JSON.stringify(report,null,2)+'\n');
console.log(results.map(r=>[r.parent,r.variant,r.minimumEndOverlap_m,r.maximumEndOverlap_m]));assert(report.passed);
