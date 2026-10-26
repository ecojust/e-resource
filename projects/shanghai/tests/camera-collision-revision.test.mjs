import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const here = path.dirname(fileURLToPath(import.meta.url));
const sourceRoot = path.resolve(here, '..');
const controllerCode = readFileSync(path.join(sourceRoot, 'src/walk-controller.js'), 'utf8');
const sceneCode = readFileSync(path.join(sourceRoot, 'src/map-scene.js'), 'utf8');
// Small exact effective-source fixture; no private staging files or remote access.
const fixture = {
  "pose": {
    "bearing": 326.31010633186054,
    "listed": true,
    "overviewZoom": 19,
    "walkStart": [
      121.05105491533773,
      31.112992761093196
    ]
  },
  "neighbor": {
    "key": "building:89f6310b-5602-4121-92c5-ac67809118a5",
    "geometry": {
      "coordinates": [
        [
          [
            121.05110765,
            31.11289289
          ],
          [
            121.05107546,
            31.11296179
          ],
          [
            121.05128467,
            31.11302149
          ],
          [
            121.05131686,
            31.1129526
          ],
          [
            121.05110765,
            31.11289289
          ]
        ]
      ],
      "type": "Polygon"
    }
  },
  "provenance": {
    "macro": "14-13701-6700",
    "localId": 1148,
    "source_table_sha256": "45c5ac2f165e1646f351cfd81d544470900a7fbb1a766ef1df0d4f59555a964e",
    "source": "Overture Maps2026-10-21 effective building footprint; EastAsianBuildings/Zenodo source via Overture. Existing project data/SOURCES.md attribution and licenses apply."
  }
};
const { WalkController, distanceMetres } = await import('data:text/javascript;base64,' + Buffer.from(controllerCode).toString('base64'));

globalThis.window = new EventTarget();
globalThis.document = new EventTarget();
document.hidden = false;
window.requestAnimationFrame = () => 1;
window.cancelAnimationFrame = () => {};

function insideRing(ring, x, y) {
  let result = false;
  for (let i=0,j=ring.length-1;i<ring.length;j=i++) {
    const [xi,yi]=ring[i], [xj,yj]=ring[j];
    if ((yi>y)!==(yj>y) && x<(xj-xi)*(y-yi)/(yj-yi)+xi) result=!result;
  }
  return result;
}
function contains(g, x, y) {
  return (g.type==='Polygon' ? [g.coordinates] : g.coordinates)
    .some(r=>insideRing(r[0],x,y)&&!r.slice(1).some(h=>insideRing(h,x,y)));
}
function bounds(g) {
  const p=g.coordinates.flat(g.type==='Polygon'?1:2);
  return [Math.min(...p.map(v=>v[0])),Math.min(...p.map(v=>v[1])),
    Math.max(...p.map(v=>v[0])),Math.max(...p.map(v=>v[1]))];
}

/** Execute the actual scene cache functions, with only MapLibre I/O replaced. */
function cacheFixture() {
  let now=1000, present=false, queries=0, zoom=21;
  const map={getZoom:()=>zoom,querySourceFeatures(source,{sourceLayer}) {
    queries++;
    return present&&source==='buildings'&&sourceLayer==='building'
      ? [{id:fixture.neighbor.key,properties:{},geometry:fixture.neighbor.geometry}] : [];
  }};
  const declaration=sceneCode.match(/let collisionDirty = true[^;]+;/)[0];
  const functions=sceneCode.slice(sceneCode.indexOf('  function sourceFeatures('),sceneCode.indexOf('  async function waitForData('));
  const getter=sceneCode.match(/collisionRevision:\(\)=>\{([^}]+)\}/)?.[1] || 'return 0;';
  const cache=new Function('map','performance','boundsOf','geometryContains','nearestOnLine',
    `${declaration}\nconst buildingMode='overture',buildingSourceId='buildings',sourceId='basemap';\n${functions}\n`+
    `return {revision(){${getter}},collisionAt,dirty(){collisionDirty=true},`+
    `state(){return {dirty:collisionDirty,updated:collisionUpdated,polygons:polygons.length}}};`)(
      map,{now:()=>now},bounds,contains,()=>null);
  return {...cache,advance(ms){now+=ms},setPresent(value){present=value;cache.dirty()},
    setZoom(value){zoom=value},queryCount:()=>queries};
}

function controlled(cache) {
  const cameras=[]; const canvas=new EventTarget();
  const scene={map:{getCanvas:()=>canvas,areTilesLoaded:()=>true},
    setPlayer(){},setAvatarVisible(){},collisionAt:cache.collisionAt,
    collisionRevision:cache.revision,
    // Real jumpTo emits moveend, which dirties the source query cache.
    setCameraFromTo(request){cameras.push(request);cache.dirty()}};
  const ctl=new WalkController(scene);ctl.setEnabled(true);
  ctl.teleport({lng:fixture.pose.walkStart[0],lat:fixture.pose.walkStart[1],bearing:fixture.pose.bearing});
  return {ctl,scene,cameras};
}

test('actual scene revision changes only after a completed rebuild and respects 850ms throttle',()=>{
  const cache=cacheFixture();
  const first=cache.revision();assert.ok(first>0,'A completed source query exposes its revision');
  const queries=cache.queryCount();assert.equal(cache.revision(),first);assert.equal(cache.queryCount(),queries);
  cache.setPresent(true);cache.advance(849);
  assert.equal(cache.revision(),first,'Dirty alone must not claim fresh collision data');
  assert.equal(cache.queryCount(),queries);
  cache.advance(1);assert.equal(cache.revision(),first+1);assert.equal(cache.state().polygons,1);
  cache.setZoom(13);cache.setPresent(false);cache.advance(1000);
  assert.equal(cache.revision(),first+1,'A skipped low-zoom rebuild must not advance revision');
});

test('actual B pose: late 1148 source arrival shortens idle camera, source removal restores it',()=>{
  const cache=cacheFixture(), {ctl,cameras}=controlled(cache);
  try {
    const initial=cameras.at(-1), position={...ctl.position};
    assert.ok(contains(fixture.neighbor.geometry,initial.from.lng,initial.from.lat));
    cache.setPresent(true);cache.advance(900);const before=cameras.length;
    ctl._updateCamera(.05);
    assert.equal(cameras.length,before+1,'Idle camera must respond without player/ground movement');
    const shorter=cameras.at(-1);
    assert.equal(contains(fixture.neighbor.geometry,shorter.from.lng,shorter.from.lat),false);
    assert.ok(Math.abs(distanceMetres(shorter.from,shorter.to)-5.04*Math.sin(82*Math.PI/180))<.0001);
    assert.deepEqual(ctl.position,position,'Camera correction must not move the visitor');
    const queries=cache.queryCount(), count=cameras.length;
    for(let i=0;i<50;i++)ctl._updateCamera(.05);
    assert.equal(cameras.length,count);assert.equal(cache.queryCount(),queries,'Same-revision idle frames do not query source again');
    cache.advance(900);ctl._updateCamera(.05);
    assert.equal(cameras.length,count,'An identical rebuild must not re-submit jumpTo');
    assert.equal(cache.state().dirty,false,'The unchanged output does not start a moveend/dirty feedback loop');
    cache.setPresent(false);cache.advance(900);ctl._updateCamera(.05);
    assert.deepEqual(cameras.at(-1),initial,'Removed source obstruction restores the requested camera');
  } finally {ctl.destroy()}
});

test('an explicit camera reset still submits after external camera changes',()=>{
  const cache=cacheFixture(), {ctl,cameras}=controlled(cache);
  try {const count=cameras.length;ctl._updateCamera(0,true);assert.equal(cameras.length,count+1)}
  finally {ctl.destroy()}
});

test('legacy adapter without collisionRevision keeps prior behavior',()=>{
  const cache=cacheFixture(), {ctl,scene,cameras}=controlled(cache);
  try {delete scene.collisionRevision;ctl._updateCamera(0,true);const n=cameras.length;
    ctl._updateCamera(.05);assert.equal(cameras.length,n)}
  finally {ctl.destroy()}
});

// Execute the shipped MapLibre camera calculation without starting a Map,
// browser, GPU or network. Only its dimensions and field of view are supplied.
const vendorContext={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,
  setTimeout,clearTimeout,performance};
vendorContext.exports=vendorContext.module.exports;
vendorContext.self=vendorContext;vendorContext.globalThis=vendorContext;
vm.runInNewContext(readFileSync(path.join(sourceRoot,'vendor/maplibre-gl.js'),'utf8'),vendorContext);
const maplibre=vendorContext.module.exports;

function cameraAdapter() {
  const constant=sceneCode.match(/const WALK_CAMERA_MAX_ZOOM = [^;]+;/)?.[0] || '';
  const maximumExpression=sceneCode.match(/maxZoom: ([^,\n]+)/)[1];
  const maximum=new Function(`${constant};return ${maximumExpression}`)();
  const functionSource=sceneCode.slice(sceneCode.indexOf('  function setCameraFromTo('),sceneCode.indexOf('  function setDistricts('));
  let applied=null;
  const map={transform:{cameraToCenterDistance:760/2/Math.tan(64/2*Math.PI/180),tileSize:512},
    setCenterClampedToGround(value){assert.equal(value,false)},
    calculateCameraOptionsFromTo(...args){return maplibre.Map.prototype.calculateCameraOptionsFromTo.apply(this,args)},
    jumpTo(options){applied={...options,zoom:Math.min(maximum,options.zoom)}}};
  const set=new Function('map','clamp',`${constant};let explicitCamera;${functionSource};return setCameraFromTo`)(
    map,(x,a,b)=>Math.max(a,Math.min(b,x)));
  return {set,get:()=>applied,map};
}

test('actual vendored MapLibre shortened B camera is not clamped by either scene zoom limit',()=>{
  const cache=cacheFixture();cache.setPresent(true);
  const {ctl,cameras}=controlled(cache);
  try {
    const request=cameras.at(-1), adapter=cameraAdapter();
    adapter.set(request);
    const expected=adapter.map.calculateCameraOptionsFromTo([request.from.lng,request.from.lat],request.from.alt,
      [request.to.lng,request.to.lat],request.to.alt);
    assert.ok(expected.zoom>22.5&&expected.zoom<24,'The real5.04m request exceeds the former cap');
    assert.equal(adapter.get().zoom,expected.zoom,'Both the Map constructor and adapter must permit the requested zoom');
    assert.equal(adapter.get().elevation,request.to.alt,'Raised target must survive camera submission');
  } finally {ctl.destroy()}
});

test('the existing3.5m minimum boom also fits the vendored camera projection at the QA viewport',()=>{
  const cache=cacheFixture(), {ctl,scene,cameras}=controlled(cache);
  try {
    scene.collisionAt=()=> 'building';ctl._updateCamera(0,true);
    const request=cameras.at(-1),adapter=cameraAdapter();adapter.set(request);
    const expected=adapter.map.calculateCameraOptionsFromTo([request.from.lng,request.from.lat],request.from.alt,
      [request.to.lng,request.to.lat],request.to.alt);
    assert.ok(expected.zoom>22.5&&expected.zoom<24);
    assert.equal(adapter.get().zoom,expected.zoom);
  } finally {ctl.destroy()}
});
