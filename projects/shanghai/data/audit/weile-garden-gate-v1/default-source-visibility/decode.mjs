import fs from 'node:fs';import zlib from 'node:zlib';import crypto from 'node:crypto';import {registerHooks} from 'node:module';import{pathToFileURL}from'node:url';
const project='/workspace/e-resource/projects/shanghai/',mod=n=>pathToFileURL(project+'vendor/'+n).href,root=new URL('.',import.meta.url);
registerHooks({resolve(s,c,next){return s==='three'?{url:mod('three.module.js'),shortCircuit:true}:next(s,c);}});
const {GLTFLoader}=await import(mod('GLTFLoader.js')),{MeshoptDecoder}=await import(mod('meshopt_decoder.module.js')),{Vector3,Matrix4}=await import(mod('three.module.js')),spec=JSON.parse(fs.readFileSync(new URL(process.argv[2]+'-decode.json',root)));
for(const [gi,g] of spec.files.entries()){
 const res=await fetch(g.url),bytes=Buffer.from(await res.arrayBuffer());if(!res.ok||crypto.createHash('sha256').update(bytes).digest('hex')!==g.sha256)throw Error(g.url);
 const data=g.kind==='near'?zlib.gunzipSync(bytes):bytes,scene=(await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'')).scene;scene.updateMatrixWorld(true);
 const out=[],vec=new Vector3(),m=new Matrix4(),part=new Matrix4(),r=Math.PI/180,k=6371008.8*Math.cos(spec.anchor[1]*r),km=6378137*Math.cos(spec.origin[1]*r),delta=(spec.origin[0]-spec.anchor[0])*r*k,dy=(Math.asinh(Math.tan(spec.origin[1]*r))-Math.asinh(Math.tan(spec.anchor[1]*r)))*k;
 scene.traverse(o=>{if(!o.isMesh)return;const geom=o.geometry,pos=geom.getAttribute('position'),fid=geom.getAttribute('_feature_id_0'),idx=geom.getIndex();
 for(let inst=0;inst<(o.isInstancedMesh?o.count:1);inst++){if(o.isInstancedMesh){o.getMatrixAt(inst,part);m.multiplyMatrices(o.matrixWorld,part);}else m.copy(o.matrixWorld);for(let i=0;i<(idx?.count??pos.count);i+=3){const vs=[];for(let j=0;j<3;j++){let l=idx?idx.getX(i+j):i+j;vec.fromBufferAttribute(pos,l).applyMatrix4(m);vs.push([delta+vec.x*k/km,dy-vec.z*k/km,vec.y]);}if(vs.every(p=>p[0]>55)||vs.every(p=>p[0]<-55)||vs.every(p=>p[1]>55)||vs.every(p=>p[1]<-55))continue;out.push(...vs.flat(),g.kind==='far'?fid.getX(idx?idx.getX(i):i):0);}}});
 fs.writeFileSync(new URL(process.argv[2]+'-'+gi+'.f32.gz',root),zlib.gzipSync(Buffer.from(new Float32Array(out).buffer),{level:1}));
}
