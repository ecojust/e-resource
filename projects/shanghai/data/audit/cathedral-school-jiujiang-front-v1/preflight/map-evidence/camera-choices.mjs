import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const w=path.dirname(fileURLToPath(import.meta.url)),modfile=path.join(w,'frozen-259/src/candidate-overview-camera.js');
const resp=await fetch('http://127.0.0.1:31259/src/candidate-overview-camera.js');const bytes=Buffer.from(await resp.arrayBuffer()),digest=createHash('sha256').update(bytes).digest('hex');if(!resp.ok)throw Error('Camera GET failed');const proof=JSON.parse(fs.readFileSync('/tmp/shanghai-yongjia-porch/scenes/259-comparison.json'));if(proof.files.find(q=>q.path==='src/candidate-overview-camera.js')?.sha256!==digest)throw Error('Wrong camera hash');
if(fs.existsSync(modfile)){if(!bytes.equals(fs.readFileSync(modfile)))throw Error('Wrong disk camera');}else fs.writeFileSync(modfile,bytes,{flag:'wx'});const {candidateOverviewCamera}=await import(pathToFileURL(modfile));
const placement=JSON.parse(fs.readFileSync(path.join(w,'ground-placement-fragment.json')));const ids=['whole','five-bays','roof-and-doors'];const focus=[null,{min:[23.35,.65,-.80],max:[52.30,20.80,1.5]},{min:[24.9,1.1,-.76],max:[51.7,20.5,.75]}];
const cases=[['desktop',900,650,[316,88,154,241]],['mobile',390,844,[16,65,182,228]]],all=[];
for(let i=0;i<focus.length;i++)for(let b=115;b<=211;b+=4)for(const p of [28,34,40,46,52,58,64,69]){
 const place={...placement,city_integration:true,overviewBearing:b,overviewPitch:p};if(focus[i])place.overview_focus_bounds_glb=focus[i];
 all.push({id:ids[i],focus:focus[i],bearing:b,pitch:p,views:cases.map(([name,width,height,[left,right,top,bottom]])=>({name,width,height,camera:candidateOverviewCamera(place,{width,height,insets:{left,right,top,bottom}})}))});
}
fs.writeFileSync(path.join(w,'camera-choices.json'),JSON.stringify({module_sha256:digest,cases:all}));
