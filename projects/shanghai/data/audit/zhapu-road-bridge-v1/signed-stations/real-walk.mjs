import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {WalkController, distanceMetres} from '../src/walk-controller.js';
import {StreetInteraction, DEFAULT_GROUND_HEIGHT} from '../src/street-interaction.js';
import {bridgePosition, CandidateBridgeWalks, validBridgeWalk} from '../src/candidate-bridge-walk.js';
import {CandidateCityState,mergeCandidateCityModels} from '../src/candidate-city-integrations.js';
import {markVerifiedOrdinaryAsset} from '../src/ordinary-asset-verification.js';
import {MeshoptDecoder} from '../vendor/meshopt_decoder.module.js';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))), project='/workspace/e-resource/projects/shanghai';
const signed = process.env.BRIDGE_LIVE === '1'
  ? JSON.parse(fs.readFileSync(path.join(root,'tests/input-binding.json'))) : null;
const fetchedAssets = new Map();
let signedModels;
if (signed) {
  const response = await fetch(new URL('data/candidate-city-integrations.json',signed.url)); assert(response.ok);
  const catalog = Buffer.from(await response.arrayBuffer());
  assert.equal(createHash('sha256').update(catalog).digest('hex'),signed.catalog_sha256);
  signedModels = mergeCandidateCityModels([],JSON.parse(catalog));
}
globalThis.window=new EventTarget(); globalThis.document=new EventTarget();
window.requestAnimationFrame=()=>1;window.cancelAnimationFrame=()=>{};
const RAD=Math.PI/180;
const vec=([lng,lat])=>({lng,lat});
const arr=p=>[p.lng,p.lat];
function inside(p,ring) {
  let hit=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++) {
    const [x,y]=ring[i],[a,b]=ring[j];
    if((y>p[1]) !== (b>p[1]) && p[0]<(a-x)*(p[1]-y)/(b-y)+x)hit=!hit;
  }
  return hit;
}
function edgeDistance(p,a,b) {
  const k=Math.cos(p[1]*RAD),x=(a[0]-p[0])*k,y=a[1]-p[1],dx=(b[0]-a[0])*k,dy=b[1]-a[1];
  const t=Math.max(0,Math.min(1,-(x*dx+y*dy)/(dx*dx+dy*dy||1)));
  return Math.hypot(x+t*dx,y+t*dy)*RAD*6378137;
}
function query(p,rows,bridge) {
  if(rows.some(q=>q.layer==='building'&&inside(p,q.coordinates)))return 'building';
  if(!rows.some(q=>q.layer==='water'&&inside(p,q.coordinates)))return null;
  if(rows.some(q=>q.layer==='transportation'&&bridge.allowsNativeRoad(q.id,...p,q.width)&&q.coordinates.slice(1).some((b,i)=>edgeDistance(p,q.coordinates[i],b)<q.width)))return null;
  return bridge.coversWater(...p)?null:'water';
}
async function mesh(asset) {
  let blob;
  if(signed){
    const url=new URL(asset.file,signed.url),response=await fetch(url);assert(response.ok);
    blob=Buffer.from(await response.arrayBuffer());assert.equal(blob.length,asset.bytes);
    fetchedAssets.set(asset.sha256,{url:url.href,bytes:blob.length,sha256:asset.sha256});
  }else blob=fs.readFileSync(path.join(project,asset.file)); assert.equal(createHash('sha256').update(blob).digest('hex'),asset.sha256);
  const jlen=blob.readUInt32LE(12),j=JSON.parse(blob.subarray(20,20+jlen)),bin=blob.subarray(28+jlen);
  const views=await Promise.all(j.bufferViews.map(async v=>{
    const c=v.extensions?.EXT_meshopt_compression;
    if(!c)return bin.subarray(v.byteOffset||0,(v.byteOffset||0)+v.byteLength);
    await MeshoptDecoder.ready;
    const dest=Buffer.alloc(v.byteLength);
    MeshoptDecoder.decodeGltfBuffer(dest,c.count,c.byteStride,bin.subarray(c.byteOffset||0,(c.byteOffset||0)+c.byteLength),c.mode,c.filter);
    return dest;
  }));
  const widths={5121:1,5123:2,5125:4,5126:4};
  function accessor(i){
    const a=j.accessors[i],v=j.bufferViews[a.bufferView],b=views[a.bufferView],n={SCALAR:1,VEC3:3}[a.type],w=widths[a.componentType];
    const read={5121:'readUInt8',5123:'readUInt16LE',5125:'readUInt32LE',5126:'readFloatLE'}[a.componentType];
    return Array.from({length:a.count},(_,k)=>Array.from({length:n},(_,t)=>b[read]((a.byteOffset||0)+k*(v.byteStride||w*n)+t*w)));
  }
  const triangles=[];
  for(const node of j.nodes.filter(n=>n.mesh!==undefined)){
    assert(!node.rotation&&!node.translation&&!node.scale&&!node.matrix,'mesh transform must be included');
    for(const primitive of j.meshes[node.mesh].primitives){
      const pos=accessor(primitive.attributes.POSITION),ix=accessor(primitive.indices).flat();
      for(let i=0;i<ix.length;i+=3)triangles.push([pos[ix[i]],pos[ix[i+1]],pos[ix[i+2]]]);
    }
  }
  return triangles;
}
function yHit(tri,x,z,expected){
  let nearest=Infinity;
  for(const [a,b,c] of tri){
    const dx=b[0]-a[0],dz=b[2]-a[2],ex=c[0]-a[0],ez=c[2]-a[2],det=dx*ez-dz*ex;
    if(Math.abs(det)<1e-9)continue;
    const u=((x-a[0])*ez-(z-a[2])*ex)/det,v=(dx*(z-a[2])-dz*(x-a[0]))/det;
    if(u< -1e-6||v< -1e-6||u+v>1+1e-6)continue;
    const y=a[1]+u*(b[1]-a[1])+v*(c[1]-a[1]);if(Math.abs(y-expected)<Math.abs(nearest-expected))nearest=y;
  }
  return nearest;
}
function assertNear(got,expected,tol,why){assert(Math.abs(got-expected)<=tol,why+': '+got+' vs '+expected);}
async function run(n){
 const {record:input,frozen}=JSON.parse(fs.readFileSync(root+'/evidence/'+n+'-input.json'));
 const r=signed?signedModels.find(q=>q.id===input.id):input;
 if(signed){assert.deepEqual(r.bridge_walk,input.bridge_walk);assert.deepEqual(r.navigation,input.navigation);assert(r.navigation.listed);}
 const b=r.bridge_walk,angle=r.heading+(b.longitudinal_axis==='x'?90:0),rows=frozen.rows;
 const glscene={visible:true},street=new StreetInteraction(),bridges=new CandidateBridgeWalks(street),recs=new Map([[r.id,r]]);
 const city=new CandidateCityState({getRecords:()=>recs,getScene:()=>glscene,onChange:s=>bridges.sync(s.active)});
 const at=(s,v)=>vec(bridgePosition(r,s,v));
 const ground=p=>street.groundAt(p.lng,p.lat),state=()=>street.getState();
 const coord=(s,v)=>{const a=s+b.shear*v;return b.longitudinal_axis==='x'?[a,-v]:[v,-a];};
 function load(variant,trusted,sha){
   r.status='loaded';r.activeVariant=variant==='web'?'full':'distant';r.object={visible:true,parent:glscene};
   if(trusted)markVerifiedOrdinaryAsset(r.object,{modelId:r.id,variant,asset:{...r.assets[variant],sha256:sha||r.assets[variant].sha256}});
   city.sync();
 }
 let avatarHeight;const scene={map:{},setCamera(){},collisionAt:(lng,lat)=>query([lng,lat],rows,bridges),setPlayer:(x,y,a,s,t,h)=>{avatarHeight=h;},groundAt:(x,y)=>street.groundAt(x,y),streetInteractionRevision:()=>street.revision,sweepLocalCollision:(a,b,o)=>street.sweep(a,b,o)};
 const ctl=new WalkController(scene);ctl.setEnabled(true);
 const mid=(b.half_deck_m+b.half_road_m)/2,span=b.stations_m.at(-1)[0],report={id:r.id,tile_sha256:frozen.tile_sha256,groups:[],traversals:[],sources:{native_center:scene.collisionAt(...arr(at(0,mid))),native_river_14m:scene.collisionAt(...arr(at(0,14)))}};
 const sourceRiver=scene.collisionAt(...arr(at(0,14)));load('web',false);assert(!ground(at(0,mid)));load('web',true,'0'.repeat(64));assert(!ground(at(0,mid)));
 for(const variant of ['web','lod','web']){
   const old=street.revision;load(variant,true);assert(street.revision>old);assert.equal(state().activeOwners,1);
   const geo=await mesh(r.assets[variant]);let maxDifference=0;let rays=0;
   for(const s of [-span+.02,-31,-18.29,-8.1,0,9,17.9,29,span-.01]){
    for(const v of [-mid,1.3,mid]){
     const g=ground(at(s,v));assert(g);const height=r.altitude+yHit(geo,...coord(s,v),g.height-r.altitude);
     maxDifference=Math.max(maxDifference,Math.abs(height-g.height));assertNear(g.height,height,.003,'mesh and avatar sole');rays++;
    }
   }
   const blockedRail=street.sweep(at(0,mid),at(0,b.half_deck_m-.03),{radius:.38});assert.equal(blockedRail?.type,'street-obstacle');
   assert.equal(street.cameraCollision({...at(0,mid),alt:ground(at(0,mid)).height+.55},{...at(0,14),alt:ground(at(0,mid)).height+.55})?.type,'street-obstacle');
   assert.equal(query(arr(at(0,14)),rows,bridges),'water');assert.equal(ground(at(0,14)),null);assert.equal(bridges.coversWater(...arr(at(0,14))),false);
   for(const p of b.posts||[]){assert.equal(street.sweep(at(p.station_m,p.offset_m),at(p.station_m,p.offset_m))?.type,'street-obstacle');}
   if(variant==='web'&&report.groups.length)continue;
   report.groups.push({variant,hash:r.assets[variant].sha256,rays,max_mesh_floor_error_m:maxDifference,state:state(),rail:blockedRail.id});
   for(const across of [-mid,0,mid])for(const direction of [-1,1]){
    const start=at(-direction*(span+1.4),across),goal=at(direction*(span+1),across);
    ctl.setRun(direction<0);ctl.teleport({...start,bearing:angle+(direction<0?180:0)});ctl.keys.add('KeyW');
    let frames=0,maxStep=0,minH=Infinity,maxH=-Infinity,floors=0;let last=DEFAULT_GROUND_HEIGHT;
    for(;frames<1300;frames++){
      const old=distanceMetres(ctl.position,goal);if(old<.48)break;
      ctl._move(.05,frames*50);ctl._sendPlayer(ctl.speed,.05);
      maxStep=Math.max(maxStep,Math.abs(avatarHeight-last));last=avatarHeight;
      if(ground(ctl.position))floors++;minH=Math.min(minH,avatarHeight);maxH=Math.max(maxH,avatarHeight);
    }
    assert(frames<1300,'crossing blocked '+n+' '+across+' '+direction+' '+JSON.stringify(ctl.position)+' goal '+JSON.stringify(goal)); assert(maxStep<=.20001);assert(floors>140);
    assertNear(avatarHeight,DEFAULT_GROUND_HEIGHT,1e-8,'bank landing');
    report.traversals.push({variant,across,direction,frames,ground_frames:floors,closest_exit_m:distanceMetres(ctl.position,goal),max_step_m:maxStep,min_sole_m:minH,max_sole_m:maxH});
   }
 }
 r.object.visible=false;city.sync();assert.equal(state().activeOwners,0);assert(!ground(at(0,mid)));assert.equal(scene.collisionAt(...arr(at(0,14))),sourceRiver);assert(!street.sweep(at(0,mid),at(0,14)));
 load('lod',true);assert(ground(at(0,mid)));r.object.parent=null;city.sync();assert(!ground(at(0,mid)));
 load('web',true);assert(ground(at(0,mid)));r.catalogDisposed=true;city.sync();assert.equal(state().activeOwners,0);assert(!bridges.coversWater(...arr(at(0,mid))));
 ctl.destroy();return report;
}
const reports=[];for(const n of (signed?.orders||[221,223,230]))reports.push(await run(n));
fs.writeFileSync(root+'/evidence/walk.json',JSON.stringify({passed:true,source:signed?'signed-city-HTTP-and-current-style-vector-tile':'authored-model-and-frozen-vector-tile',catalog_sha256:signed?.catalog_sha256,asset_requests:[...fetchedAssets.values()],reports},null,2)+'\n');console.log(reports.map(r=>({id:r.id,crossings:r.traversals.length,geometry:r.groups.map(g=>g.max_mesh_floor_error_m),water:r.sources})));
