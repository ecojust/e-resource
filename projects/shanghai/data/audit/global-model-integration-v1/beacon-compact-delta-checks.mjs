// Delta only: replay the measured 320x568 phone location-card top at y=348.
// The earlier ten-group report is preserved with its own source binding.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {layoutBeaconLabels,hitTestBeaconLabels,createBuildingBeacons} from '../../../src/building-beacons.js';

const read=path=>readFileSync(new URL(path,import.meta.url));
const json=path=>JSON.parse(read(path));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const records=[...json('../../landmarks.json'),...json('../../candidate-city-integrations.json').models];
const ids=records.map(row=>row.id).sort(),width=320,height=568;
const insets={left:12,right:65,top:182,bottom:228};
assert.equal(records.length,70);assert.equal(new Set(ids).size,70);

function verifyCards(cards){
  assert.equal(cards.length,70);assert.deepEqual(cards.map(row=>row.id).sort(),ids);
  for(const card of cards){
    const x=card.labelX??card.x,y=card.labelY??card.y;
    assert.equal(card.width,24);assert.equal(card.height,20);assert.equal(card.compact,true);
    assert(!card.overlapFallback);
    assert(x-12>=insets.left&&x+12<=width-insets.right);
    assert(y-10>=insets.top&&y+10<=height-insets.bottom);
    assert.equal(hitTestBeaconLabels(cards,{x,y}),card.id);
  }
  for(let i=0;i<cards.length;i++)for(let j=0;j<i;j++){
    const a=cards[i],b=cards[j],ax=a.labelX??a.x,ay=a.labelY??a.y,bx=b.labelX??b.x,by=b.labelY??b.y;
    assert(Math.abs(ax-bx)>=24||Math.abs(ay-by)>=20,`${a.id} overlaps ${b.id}`);
  }
  assert.equal(new Set(cards.map(card=>card.labelX??card.x)).size,10);
  assert.equal(new Set(cards.map(card=>card.labelY??card.y)).size,7);
}
const pure=layoutBeaconLabels(records.map(row=>({id:row.id,x:160,y:284,width:179,height:66})),{width,height,insets});
verifyCards(pure);

function element(tag){return {tag,style:{},children:[],width:0,height:0,
  setAttribute(){},append(...children){this.children.push(...children);},appendChild(child){this.children.push(child);},remove(){},
  getBoundingClientRect(){return {left:0,right:width,top:126,bottom:174};},
  getContext(){return new Proxy({createRadialGradient:()=>({addColorStop(){}}),
    getImageData:()=>({width:this.width,height:this.height,data:new Uint8ClampedArray(this.width*this.height*4)})},
    {get:(target,key)=>key in target?target[key]:()=>{}});}};}
const documentObject={createElement:element,
  getElementById:id=>id==='location-card'?{getBoundingClientRect:()=>({left:0,right:320,top:348,bottom:568})}:null,
  querySelector:selector=>selector==='.map-tools'?{getBoundingClientRect:()=>({left:263,right:320,top:190,bottom:348})}:null};
const sources=new Map(),layers=new Map(),images=new Map(),events=[],selected=[];
const map={
  canvas:{clientWidth:width,clientHeight:height,width,height,style:{}},container:element('div'),
  addImage(id,data,options){images.set(id,{data,options});},hasImage:id=>images.has(id),removeImage:id=>images.delete(id),
  addSource(id,row){sources.set(id,{...row,setData(data){this.data=data;}});},getSource:id=>sources.get(id),removeSource:id=>sources.delete(id),
  addLayer(row){layers.set(row.id,structuredClone(row));},getLayer:id=>layers.get(id),removeLayer:id=>layers.delete(id),
  setLayoutProperty(id,key,value){layers.get(id).layout[key]=structuredClone(value);},
  getCanvas(){return this.canvas;},getContainer(){return this.container;},getZoom:()=>8,triggerRepaint(){},
  project:([lng,lat])=>({x:160+(lng-121.45)*50,y:284-(lat-31.35)*50}),
  unproject:([x,y])=>({lng:121.45+(x-160)/50,lat:31.35-(y-284)/50}),
  on(...args){events.push(args);},off(...args){const index=events.findIndex(row=>row.every((value,i)=>value===args[i]));if(index>=0)events.splice(index,1);},
  queryRenderedFeatures(){assert.fail('A card-center pick must not use the stale native symbol hit boxes');}
};
const beacons=createBuildingBeacons({map,records,documentObject,onSelect:row=>selected.push(row.id)}),state=beacons.getState();
assert.equal(state.count,70);assert.equal(state.viewportLabelCount,70);assert.equal(state.overlapFallbackCount,0);assert.equal(state.labelMode,'numbers');
verifyCards(state.labelPositions);
const compact=[...layers.values()].find(layer=>layer.layout?.['icon-text-fit']==='none');
assert.equal(compact.layout['text-size'],12);assert.equal(compact.layout['icon-size'],1);
const number=images.get(compact.layout['icon-image']);assert.equal(number.data.width/number.options.pixelRatio,24);assert.equal(number.data.height/number.options.pixelRatio,20);
const source=sources.get(compact.source);assert.equal(source.data.features.length,70);
assert(source.data.features.every(feature=>feature.properties.inViewport&&feature.properties.compact));
for(const card of state.labelPositions){
  const point={x:card.x,y:card.y};assert.equal(beacons.hitTest(point),card.id);
  for(const [event,callback] of events.filter(row=>row.length===2))if(event==='click')callback({point,originalEvent:{preventDefault(){}}});
  assert.equal(selected.at(-1),card.id);
}
assert.equal(selected.length,70);assert.deepEqual([...selected].sort(),ids);beacons.destroy();

const baselineBytes=read('./beacon-checks.json'),baseline=JSON.parse(baselineBytes);
const baselineSource=baseline.bindings.find(item=>item.path.endsWith('/building-beacons.js'));
assert.equal(baseline.passed,10);assert.equal(baselineSource.sha256,'ed9fac594eb3776489d4fe5ba4189d91e06b639f6d6d01e3f653f9bb74374d94');
const bindingPaths=['./beacon-compact-delta-checks.mjs','../../../src/building-beacons.js','../../landmarks.json','../../candidate-city-integrations.json'];
const bindings=bindingPaths.map(path=>{const bytes=read(path);return {path,bytes:bytes.length,sha256:sha(bytes)};});
const report={schema:'building-beacon-compact-capacity-delta-v1',passed:2,
  checks:['70 real IDs fit ten columns by seven rows inside the measured available area without overlap or fallback',
    'Runtime UI rectangle handling retains 70 numbered signs and all 70 card-center clicks resolve correctly'],
  viewport:{width,height},replayed_browser_measurements:{location_card_top:348,legend_bottom:174,map_tools_left:263,clearance_pixels:8,
    source:'Browser measurements reported by the root agent; replayed here using map/canvas facades'},
  insets,available_pixels:[243,158],card_pixels:[24,20],font_pixels:12,grid_columns:10,grid_rows:7,identities:70,
  overlap_fallback_count:0,pairwise_overlap_count:0,correct_center_clicks:70,
  earlier_baseline:{path:'beacon-checks.json',bytes:baselineBytes.length,sha256:sha(baselineBytes),passed:10,
    source_sha256:baselineSource.sha256,rerun:false,scope:'Earlier identity, filtering, offset and interaction contracts remain bound to their earlier source version; this delta does not relabel them as a full rerun.'},
  bindings,scope:'Targeted zero-gap compact-capacity and center-hit delta only; no shader, unrelated regression, SDK or WebGL rerun.'};
writeFileSync(new URL('./beacon-compact-delta-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:2,grid:[10,7],identities:70,correct_center_clicks:70,current_source_sha256:bindings.find(item=>item.path.endsWith('/building-beacons.js')).sha256,baseline_rerun:false}));
