import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolveNavigationRoute} from '../src/landmark-navigation.js';
import {walkingPose} from '../src/precise-registration-ui.js';

const landmarks=JSON.parse(await readFile(new URL('../data/landmarks.json',import.meta.url),'utf8'));
const districts=JSON.parse(await readFile(new URL('../data/districts.json',import.meta.url),'utf8')).districts.map(p=>({...p,id:String(p.id)}));
const bund={id:'bund',name:'外滩历史建筑群',walkStart:[121.48583,31.24045],bearing:265.447};
const context={landmarks,districts,bund};
const source=await readFile(new URL('../src/app.js',import.meta.url),'utf8');
const selection=source.slice(source.indexOf('async function selectPlace('),source.indexOf('function mapPlace('));
const hashHandlers=source.slice(source.indexOf('function currentRoute('),source.indexOf('function renderPlaces('));
function harness(initialMode='overview') {
  const calls=[],pending=[],status={textContent:''},location={hash:''};
  const env={walkingPose,resolveNavigationRoute,landmarks,districts,BUND:bund,location,
    mapPlace:()=>null,controller:{teleport:pose=>calls.push(['teleport',pose])},
    scene:{map:{stop:()=>calls.push(['stop'])},waitForData:()=>new Promise(resolve=>pending.push(resolve))},
    updateLocation:p=>calls.push(['location',p.id]),mobile:()=>false,togglePanel(){},
    history:{replaceState(_,__,hash){location.hash=hash;calls.push(['history',hash]);}},$:()=>status,
    toast:message=>calls.push(['toast',message])};
  const api=new Function(...Object.keys(env),`let navigation=0,activePlace=BUND,mode=${JSON.stringify(initialMode)};
    function syncMode(next){mode=next;}
    function showOverview(place){mode='overview';}
    ${selection}\n${hashHandlers}
    return {select:selectPlace,navigateHash,get mode(){return mode;},get activePlace(){return activePlace;}};
  `)(...Object.values(env));
  return {api,calls,pending,status,location};
}

test('every published landmark deep link resolves to its exact reviewed walking pose',()=>{
  assert.ok(landmarks.length>=31);
  const ids=new Set();
  for(const place of landmarks) {
    assert.ok(!ids.has(place.id));ids.add(place.id);
    const route=resolveNavigationRoute(`#landmark=${encodeURIComponent(place.id)}&mode=walk`,context);
    assert.equal(route.error,undefined);assert.equal(route.place,place);assert.equal(route.mode,'walk');
    const pose=walkingPose(route.place);
    const reviewed=place.kind==='building'?place.navigation.walkStart:place.walkStart;
    assert.deepEqual([pose.lng,pose.lat],reviewed,place.id);
    assert.ok(Object.values(pose).every(Number.isFinite),place.id);
  }
});

test('landmark links default to walking, while explicit overview and district links retain their modes',()=>{
  const id=landmarks[0].id;
  assert.equal(resolveNavigationRoute(`#landmark=${id}`,context).mode,'walk');
  assert.equal(resolveNavigationRoute(`#landmark=${id}&mode=overview`,context).mode,'overview');
  assert.equal(resolveNavigationRoute(`#district=${districts[0].id}`,context).mode,'overview');
  assert.equal(resolveNavigationRoute('',context).place,bund);
  assert.equal(resolveNavigationRoute('#district=bund&mode=walk',context).place,bund);
  assert.equal(resolveNavigationRoute('#landmark=bund&mode=walk',context).place,bund);
  assert.equal(resolveNavigationRoute('#mode=overview',{...context,activePlace:landmarks[2]}).place,landmarks[2]);
});

test('unknown destinations and malformed coordinates never silently fall back to Bund',()=>{
  for(const hash of ['#landmark=missing','#landmark=','#district=missing','#unknown=x','#mode=flight',
    '#lng=121','#lng=&lat=31','#lng=NaN&lat=31','#lng=999&lat=31','#lng=121&lat=90']) {
    const route=resolveNavigationRoute(hash,context);
    assert.ok(route.error,hash);assert.equal(route.place,undefined,hash);
  }
  assert.ok(resolveNavigationRoute('#lng=121&lat=31',{...context,coordinatePlace:()=>null}).error);
  const custom={id:'coordinate'};
  assert.equal(resolveNavigationRoute('#lng=121&lat=31&mode=walk',{...context,coordinatePlace:(lng,lat)=>{
    assert.equal(lng,121);assert.equal(lat,31);return custom;
  }}).place,custom);
});

test('direct list selection enters walking from overview and uses the reviewed position',async()=>{
  const h=harness();const place=landmarks.find(p=>p.id==='yangpu-library');
  const ready=h.api.select(place,{mode:'walk'});
  assert.equal(h.api.mode,'walk');assert.equal(h.api.activePlace,place);
  assert.deepEqual(h.calls.find(c=>c[0]==='teleport')[1],walkingPose(place));
  assert.equal(h.location.hash,'#landmark=yangpu-library&mode=walk');
  h.pending[0]();await ready;
});

test('requesting walking still cannot bypass an unreviewed ordinary building guard',async()=>{
  const h=harness('walk');
  await h.api.select({id:'unreviewed',kind:'building',lng:121,lat:31,navigation:{listed:false}},{mode:'walk'});
  assert.equal(h.api.mode,'overview');assert.equal(h.calls.filter(c=>c[0]==='teleport').length,0);
  assert.equal(h.calls.filter(c=>c[0]==='history').length,0);
});

test('same-page links navigate immediately and a slower previous destination cannot overwrite the new state',async()=>{
  const h=harness();
  h.location.hash='#landmark=yangpu-library&mode=walk';h.api.navigateHash();
  assert.equal(h.api.activePlace.id,'yangpu-library');assert.equal(h.api.mode,'walk');
  h.location.hash='#landmark=shanghai-tower&mode=overview';h.api.navigateHash();
  assert.equal(h.api.activePlace.id,'shanghai-tower');assert.equal(h.api.mode,'overview');
  h.status.textContent='new-destination-pending';
  h.pending[0]();await Promise.resolve();
  assert.equal(h.status.textContent,'new-destination-pending');
  assert.equal(h.api.activePlace.id,'shanghai-tower');assert.equal(h.api.mode,'overview');
  assert.equal(h.location.hash,'#landmark=shanghai-tower&mode=overview');
  h.pending[1]();await Promise.resolve();
  assert.equal(h.status.textContent,'全域地图已连接');
});

test('an unknown same-page landmark shows a notice and preserves the current position',()=>{
  const h=harness();h.location.hash='#landmark=not-in-the-city&mode=walk';h.api.navigateHash();
  assert.ok(h.calls.some(c=>c[0]==='toast'&&c[1].includes('找不到该地标')));
  assert.equal(h.calls.filter(c=>c[0]==='teleport').length,0);
});
