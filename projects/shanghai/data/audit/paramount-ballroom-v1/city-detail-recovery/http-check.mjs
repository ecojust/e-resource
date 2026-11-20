import {createServer} from 'node:http';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {performance} from 'node:perf_hooks';

const [sourceRoot,dataRoot,version,output]=process.argv.slice(2);
assert(['before','after'].includes(version));
const app=await readFile(join(sourceRoot,'app.js'),'utf8');
const map=await readFile(join(sourceRoot,'map-scene.js'),'utf8');
const first=map.indexOf('  async function setCityManifest(');
const last=map.indexOf('  async function setNeighborhoods(',first);
assert(first>=0&&last>first);
const method=map.slice(first,last).replaceAll('import.meta.url','moduleURL');
const init=version==='after'?app.slice(app.indexOf('async function loadCityBuildings(scene)'),app.indexOf('function showOverview(')):
  'async function loadCityBuildings(scene){'+app.slice(app.indexOf("    const cityState=await scene.setCityManifest("),app.indexOf('    controller=new WalkController(scene'))+'}';
const loadCityBuildings=new Function(init+'\nreturn loadCityBuildings;')();
const data={};
for(const key of ['city','city-detail']) data[key]=await readFile(join(dataRoot,key+'.json'));
const requests=[],installed=[];
let complete;
const restored=new Promise(resolve=>{complete=resolve;});
const start=performance.now(),ms=()=>Math.round(performance.now()-start);
const server=createServer((req,res)=>{
  const key=req.url.split('/')[2];
  assert(data[key]);
  const r={file:req.url,started_ms:ms(),declared_bytes:data[key].length};
  requests.push(r);
  res.writeHead(200,{'Content-Type':'application/json','Content-Length':data[key].length,'Cache-Control':'no-store'});
  if(requests.length===1){r.actual_bytes=32;res.write(data[key].subarray(0,32));}
  else {r.actual_bytes=data[key].length;res.end(data[key]);}
});
server.listen(0,'127.0.0.1');
await new Promise(done=>server.once('listening',done));
const base='http://127.0.0.1:'+server.address().port+'/';
const errors=[];
const env={document:{baseURI:base},moduleURL:base+'src/map-scene.js',destroyed:false,cityManifestGeneration:0,localDataKind:'city',
  localStreamer:{async setManifest(manifest,{baseURL}){const key=new URL(baseURL).pathname.split('/')[2];assert.deepEqual(manifest,JSON.parse(data[key]));installed.push({key,ms:ms(),rows:manifest.tiles.length,sha256:createHash('sha256').update(data[key]).digest('hex')});if(key==='city-detail')complete();},getState:()=>({})},
  updateLocalModels:()=>{},updateLandmarkVisibility:()=>{},onLoadError:error=>errors.push(error.message)};
const setCityManifest=new Function('env','with(env){'+method+'\nreturn setCityManifest;}')(env);
try{
  await loadCityBuildings({setCityManifest});
  const returned_ms=ms();
  assert.deepEqual(installed.map(v=>v.key),['city']);
  if(version==='after'){await restored;assert.deepEqual(installed.map(v=>v.key),['city','city-detail']);}
  assert.equal(requests.length,version==='after'?3:2);
  assert.equal(errors.length,1);
  await writeFile(output,JSON.stringify({passed:true,scope:'Real HTTP directory requests using the production selection code and an instrumented manifest consumer.',version,app_sha256:createHash('sha256').update(app).digest('hex'),map_scene_sha256:createHash('sha256').update(map).digest('hex'),returned_ms,elapsed_ms:ms(),requests,installed,errors},null,2)+'\n');
}finally{server.closeAllConnections();await new Promise(done=>server.close(done));}
