import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {walkingPose} from '../src/precise-registration-ui.js';
const source=await readFile(new URL('../src/app.js',import.meta.url),'utf8');
const body=source.slice(source.indexOf('async function selectPlace('),source.indexOf('function mapPlace('));
function harness() {
  const calls=[],status={textContent:''};
  const env={walkingPose,controller:{teleport:pose=>calls.push(['teleport',pose])},scene:{waitForData:async()=>{}},
    updateLocation:p=>calls.push(['location',p.id]),showOverview:p=>calls.push(['overview',p]),mobile:()=>false,togglePanel(){},
    history:{replaceState(...args){calls.push(['history',...args]);}},$:()=>status,toast(){}};
  const names=Object.keys(env);
  const api=new Function(...names,`let navigation=0,activePlace=null,mode='walk';${body}\nreturn {select:selectPlace,reset:()=>selectPlace(activePlace),active:()=>activePlace};`)(...names.map(n=>env[n]));
  return {...api,calls};
}
test('all selection entry points including reset keep an unlisted ordinary building in overview',async()=>{
  const h=harness(),p={id:'ordinary',kind:'building',lng:121,lat:31,navigation:{listed:false}};
  await h.select(p);await h.reset();assert.equal(h.active(),p);
  assert.equal(h.calls.filter(c=>c[0]==='teleport').length,0);assert.equal(h.calls.filter(c=>c[0]==='overview').length,2);
  assert.equal(h.calls.filter(c=>c[0]==='history').length,0);
});
test('listed ordinary navigation uses its reviewed nested pose, never the building center or obsolete top-level pose',async()=>{
  const h=harness();await h.select({id:'ordinary',kind:'building',lng:121,lat:31,walkStart:[9,9],bearing:2,
    navigation:{listed:true,walkStart:[121.1,31.1],bearing:87}});
  assert.deepEqual(h.calls.find(c=>c[0]==='teleport')[1],{lng:121.1,lat:31.1,bearing:87});
  assert.throws(()=>walkingPose({kind:'building',navigation:{listed:true}}),/reviewed walking pose/);
});
test('legacy Bund and district navigation retain their existing poses',async()=>{
  const h=harness();await h.select({id:'bund17',height_m:30,walkStart:[121.49,31.24],bearing:260});
  await h.select({id:'310118',center:[121,31]});
  assert.deepEqual(h.calls.filter(c=>c[0]==='teleport').map(c=>c[1]),[{lng:121.49,lat:31.24,bearing:260},{lng:121,lat:31,bearing:45}]);
});
