// Run from projects/shanghai: node data/audit/global-model-integration-v1/beacon-checks.mjs
// Independent identity/layout checks use the real 40 + 30 catalogue records.
// The map/canvas facades below inspect contracts; real WebGL visibility is a
// separate browser check, not inferred from these results.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {layoutBeaconLabels,hitTestBeaconLabels,createBuildingBeacons} from '../../../src/building-beacons.js';

const checks=[],scenarios=[],compactScenarios=[];
const clone=x=>structuredClone(x);
function check(name,fn){fn();checks.push(name);}
function readJSON(path){return JSON.parse(readFileSync(new URL(path,import.meta.url)));}
const existing=readJSON('../../landmarks.json'),candidate=readJSON('../../candidate-city-integrations.json').models;
const districts=readJSON('../../districts.json').districts;
const records=[...existing,...candidate],expected=records.map(r=>r.id).sort();
const districtCounts=Object.fromEntries(districts.map(d=>[d.id,records.filter(r=>r.districtId===d.id).length]));

function element(tag){
  return {tag,children:[],style:{},attrs:{},width:0,height:0,parent:null,
    setAttribute(k,v){this.attrs[k]=v;},append(...children){for(const child of children){this.children.push(child);child.parent=this;}},
    appendChild(child){this.append(child);return child;},remove(){if(this.parent)this.parent.children=this.parent.children.filter(child=>child!==this);this.parent=null;},
    getBoundingClientRect(){return {left:0,top:0,right:0,bottom:0,width:this.width,height:this.height};},
    getContext(){const gradient={addColorStop(){}};return new Proxy({createRadialGradient:()=>gradient,
      getImageData:()=>({width:this.width,height:this.height,data:new Uint8ClampedArray(this.width*this.height*4)})},
      {get:(target,key)=>key in target?target[key]:()=>{}});}};
}
const documentObject={createElement:element};
class MapFacade {
  constructor(width=1280,height=800){this.width=width;this.height=height;this.zoom=8;this.sources=new Map();this.layers=new Map();this.images=new Map();this.events=[];this.queries=[];
    this.canvas=element('canvas');Object.assign(this.canvas,{width,height,clientWidth:width,clientHeight:height});this.container=element('div');}
  addImage(id,data,options){assert(!this.images.has(id));this.images.set(id,{data,options});}
  hasImage(id){return this.images.has(id);} removeImage(id){this.images.delete(id);}
  addSource(id,source){assert(!this.sources.has(id));this.sources.set(id,{...clone(source),setData(data){this.data=clone(data);}});}
  getSource(id){return this.sources.get(id);} removeSource(id){this.sources.delete(id);}
  addLayer(layer){assert(!this.layers.has(layer.id));this.layers.set(layer.id,clone(layer));}
  setLayoutProperty(id,name,value){assert(this.layers.has(id));this.layers.get(id).layout[name]=clone(value);}
  getLayer(id){return this.layers.get(id);} removeLayer(id){this.layers.delete(id);}
  getCanvas(){return this.canvas;} getContainer(){return this.container;} getZoom(){return this.zoom;} triggerRepaint(){}
  project(point){const [lng,lat]=Array.isArray(point)?point:[point.lng,point.lat],scale=50*2**(this.zoom-8);
    return {x:this.width/2+(lng-121.45)*scale,y:this.height/2-(lat-31.35)*scale};}
  unproject(point){const [x,y]=Array.isArray(point)?point:[point.x,point.y],scale=50*2**(this.zoom-8);
    return {lng:121.45+(x-this.width/2)/scale,lat:31.35-(y-this.height/2)/scale};}
  on(...args){this.events.push(args);} off(...args){this.events=this.events.filter(x=>!x.every((v,i)=>v===args[i]));}
  queryRenderedFeatures(point,options){this.queries.push({point:clone(point),options:clone(options)});return this.hits||[];}
  emitLayer(type,layer,event){for(const args of [...this.events])if(args[0]===type&&args[1]===layer)args[2](event);}
  emit(type,event){for(const args of [...this.events])if(args[0]===type&&args.length===2)args[1](event);}
}
function uniqueSourceIDs(source){return source.data.features.map(f=>f.properties.id).sort();}
function assertClamped(rows,width,height,insets={}){for(const row of rows){assert(Number.isFinite(row.labelX)&&Number.isFinite(row.labelY));
  assert(row.labelX-row.width/2>=(insets.left||0)&&row.labelX+row.width/2<=width-(insets.right||0),`${row.id} horizontal bounds`);
  assert(row.labelY-row.height/2>=(insets.top||0)&&row.labelY+row.height/2<=height-(insets.bottom||0),`${row.id} vertical bounds`);}}
function assertSeparate(rows){for(let i=0;i<rows.length;i++)for(let j=0;j<i;j++){
  const a=rows[i],b=rows[j];assert(Math.abs(a.labelX-b.labelX)>=(a.width+b.width)/2||Math.abs(a.labelY-b.labelY)>=(a.height+b.height)/2,
    `Overlapping readable labels ${a.id} / ${b.id}`);}}
function evaluateBooleanFilter(expression,properties){
  assert(Array.isArray(expression));
  if(expression[0]==='get'){assert.equal(expression.length,2);return properties[expression[1]];}
  if(expression[0]==='!'){assert.equal(expression.length,2);return !evaluateBooleanFilter(expression[1],properties);}
  if(expression[0]==='all'){assert(expression.length>1);return expression.slice(1).every(part=>Boolean(evaluateBooleanFilter(part,properties)));}
  assert.fail(`Unexpected label visibility filter ${JSON.stringify(expression)}`);
}
function evaluateOffset(expression,id){
  if(expression.length===2&&expression.every(Number.isFinite))return expression;
  assert.equal(expression[0],'match');assert.deepEqual(expression[1],['get','id']);
  let selected=expression.at(-1);
  for(let i=2;i<expression.length-1;i+=2){assert.equal(typeof expression[i],'string');if(expression[i]===id)selected=expression[i+1];}
  assert.equal(selected[0],'literal');assert.equal(selected.length,2);assert.equal(selected[1].length,2);
  assert(selected[1].every(Number.isFinite));return selected[1];
}
function assertAnchorOffsets(beaconMap,beaconState,rows){
  const rowByID=new Map(rows.map(row=>[row.id,row]));
  const full=[...beaconMap.layers.values()].find(layer=>layer.layout?.['icon-text-fit']==='both');
  const compact=[...beaconMap.layers.values()].find(layer=>layer.layout?.['icon-text-fit']==='none');
  const positions=new Map(beaconState.labelPositions.map(point=>[point.id,point]));
  for(const feature of beaconMap.getSource(full.source).data.features){
    const row=rowByID.get(feature.properties.id),position=positions.get(row.id),anchor=beaconMap.project([row.lng,row.lat]);
    assert.deepEqual(feature.geometry.coordinates,[row.lng,row.lat],'Labels keep true geographic anchors');
    assert(Object.values(feature.properties).every(value=>!Array.isArray(value)),'GeoJSON properties cannot carry pixel vec2 arrays');
    const expected=position?[position.x-anchor.x,position.y-anchor.y]:[0,0];
    const vectors=[evaluateOffset(full.layout['text-offset'],row.id).map(value=>value*12),
      evaluateOffset(compact.layout['text-offset'],row.id).map(value=>value*12),evaluateOffset(compact.layout['icon-offset'],row.id)];
    for(const vector of vectors)for(let axis=0;axis<2;axis++)assert(Math.abs(vector[axis]-expected[axis])<1e-8,'Literal style offsets must retain exact CSS pixel displacement');
  }
  for(const expression of [full.layout['text-offset'],compact.layout['text-offset'],compact.layout['icon-offset']])assert.deepEqual(evaluateOffset(expression,'unknown-beacon'),[0,0]);
}

check('the real shared catalogue supplies exactly 70 unique identities across all 16 known districts',()=>{
  assert.equal(existing.length,40);assert.equal(candidate.length,30);assert.equal(records.length,70);assert.equal(new Set(expected).size,70);
  assert.equal(Object.keys(districtCounts).length,16);assert.equal(Object.values(districtCounts).reduce((a,b)=>a+b,0),70);
  assert(Object.values(districtCounts).every(n=>n>0));assert.equal(districtCounts['310151'],20);
  assert(records.every(r=>r.name&&Number.isFinite(r.lng)&&Number.isFinite(r.lat)));
});

const map=new MapFacade(),selected=[],snapshot=JSON.stringify(records);
const decorated=records.map((r,i)=>({...r,status:['idle','loading','loaded','error'][i%4],catalogDisposed:i%2===0,
  detailWanted:false,object:{visible:false},activeVariant:i%2?'distant':'full'}));
const beacons=createBuildingBeacons({map,records:decorated,onSelect:row=>selected.push(row.id),documentObject});
const state=beacons.getState(),labelsLayer=state.layerIds.find(id=>map.layers.get(id).layout?.['icon-text-fit']==='both');
const compactLayer=state.layerIds.find(id=>map.layers.get(id).layout?.['icon-text-fit']==='none');
const anchorLayer=state.layerIds.find(id=>map.layers.get(id).type==='symbol'&&!map.layers.get(id).layout?.['text-field']);
assert(labelsLayer&&compactLayer&&anchorLayer);

check('all actual IDs remain in both sprite sources regardless of model loading, visibility, disposal or LOD',()=>{
  assert.equal(state.count,70);assert.equal(state.districtCount,16);assert.deepEqual([...state.ids].sort(),expected);
  for(const layer of [anchorLayer,labelsLayer])assert.deepEqual(uniqueSourceIDs(map.getSource(map.layers.get(layer).source)),expected);
  assert.equal(JSON.stringify(records),snapshot);
});

check('zoom 8 through 24 and resized viewports retain fixed pixel sizes and all 70 IDs without clustering',()=>{
  const sizes=[];
  for(const [width,height] of [[1280,800],[390,844],[320,568],[240,320]])for(const zoom of [8,11,15,19,24]){
    Object.assign(map,{width,height,zoom});Object.assign(map.canvas,{width,height,clientWidth:width,clientHeight:height});beacons.refresh();
    const current=beacons.getState();assert.equal(current.count,70);assert.equal(current.districtCount,16);
    for(const layer of [anchorLayer,labelsLayer,compactLayer]){
      const spec=map.layers.get(layer),source=map.getSource(spec.source);assert.deepEqual(uniqueSourceIDs(source),expected);
      assert.notEqual(source.cluster,true);assert.equal(spec.layout['icon-size'],1);assert.equal(spec.layout['icon-allow-overlap'],true);
      assert.equal(spec.layout['icon-ignore-placement'],true);assert.equal(spec.layout['icon-pitch-alignment'],'viewport');
      assert((spec.minzoom??0)<=8);assert.equal(spec.maxzoom,undefined,'Omit the upper cap: maxzoom 25 is rejected by the actual style specification');
      if(layer===anchorLayer)assert.equal(spec.filter,undefined,'No model/zoom visibility filter on anchor beacons');
    }
    const labelSpec=map.layers.get(labelsLayer),compactSpec=map.layers.get(compactLayer);
    const viewportIDs=new Set(current.labelPositions.map(point=>point.id)),filteredIDs=[];
    for(const spec of [labelSpec,compactSpec]){assert.equal(spec.layout['text-size'],12);
      assert.equal(spec.layout['text-allow-overlap'],true);assert.equal(spec.layout['text-ignore-placement'],true);}
    assert.equal(compactSpec.layout['icon-text-fit'],'none');
    for(const feature of map.getSource(labelSpec.source).data.features){
      const full=evaluateBooleanFilter(labelSpec.filter,feature.properties),compact=evaluateBooleanFilter(compactSpec.filter,feature.properties);
      const row=records[feature.properties.number-1];assert.equal(row.id,feature.properties.id);assert.equal(row.name,feature.properties.name);
      const point=map.project([row.lng,row.lat]),inViewport=point.x>=0&&point.x<=width&&point.y>=0&&point.y<=height;
      assert.equal(feature.properties.inViewport,inViewport);assert.equal(viewportIDs.has(row.id),inViewport);
      assert.equal(Number(Boolean(full))+Number(Boolean(compact)),Number(inViewport),'Each on-screen ID has one sign; offscreen anchors never leave name fragments');
      assert.equal(Boolean(compact),inViewport&&feature.properties.compact);assert.equal(Boolean(full),inViewport&&!feature.properties.compact);
      if(full||compact)filteredIDs.push(row.id);
      assert.equal(feature.properties.label,feature.properties.compact?String(feature.properties.number):row.name);
    }
    assert.deepEqual(filteredIDs.sort(),[...viewportIDs].sort());
    sizes.push([current.anchorPixelSize,current.labelPixelSize]);
    assertAnchorOffsets(map,current,records);
    scenarios.push({width,height,zoom,identities:current.count,viewport_layout_labels:current.viewportLabelCount,
      overlap_fallback_labels:current.overlapFallbackCount,anchor_pixels:current.anchorPixelSize,label_font_pixels:current.labelPixelSize,label_mode:current.labelMode});
  }
  assert(sizes.every(size=>JSON.stringify(size)===JSON.stringify(sizes[0])));
  const lamp=[...map.images.values()].find(image=>image.data.width===40);assert(lamp);assert.equal(lamp.data.width/lamp.options.pixelRatio,20);
  const number=map.images.get(map.layers.get(compactLayer).layout['icon-image']);assert(number);
  assert.equal(number.data.width/number.options.pixelRatio,24);assert.equal(number.data.height/number.options.pixelRatio,20);
});

check('viewport offsets keep all true anchors above the ground horizon without unprojecting sky label positions',()=>{
  const horizonMap=new MapFacade(320,568),unproject=horizonMap.unproject.bind(horizonMap);
  horizonMap.transform={isPointOnMapSurface:point=>(point.y??point[1])>=260};
  horizonMap.unproject=point=>{assert(horizonMap.transform.isPointOnMapSurface(point),'Sky labels must not be unprojected');return unproject(point);};
  const horizon=createBuildingBeacons({map:horizonMap,records,documentObject}),horizonState=horizon.getState();
  assert.equal(horizonState.count,70);assert.equal(horizonState.viewportLabelCount,70);assert.equal(horizonState.overlapFallbackCount,0);
  assertAnchorOffsets(horizonMap,horizonState,records);
  const sky=horizonState.labelPositions.filter(point=>!horizonMap.transform.isPointOnMapSurface(point));assert(sky.length>0);
  const lineLayer=[...horizonMap.layers.values()].find(layer=>layer.type==='line');
  const lines=new Map(horizonMap.getSource(lineLayer.source).data.features.map(feature=>[feature.properties.id,feature]));
  for(const point of sky){const row=records.find(row=>row.id===point.id);assert.deepEqual(lines.get(row.id).geometry.coordinates,[[row.lng,row.lat],[row.lng,row.lat]]);}
  horizon.destroy();
});

check('the actual 20 Chongming identities retain separate cards and complete names on a 390 by 844 viewport',()=>{
  const siteRecords=records.filter(r=>r.districtId==='310151'),siteMap=new MapFacade(390,844);
  const site=createBuildingBeacons({map:siteMap,records:siteRecords,documentObject});
  const positions=site.getState().labelPositions;
  assert.equal(positions.length,20);assert.deepEqual(positions.map(p=>p.id).sort(),siteRecords.map(r=>r.id).sort());
  const placed=positions.map(p=>({...p,labelX:p.x,labelY:p.y}));
  assertClamped(placed,390,844);assertSeparate(placed);assert.equal(site.getState().overlapFallbackCount,0);
  const siteLabels=[...siteMap.layers.values()].find(layer=>layer.layout?.['icon-text-fit']==='both');
  for(const feature of siteMap.getSource(siteLabels.source).data.features){
    assert.equal(feature.properties.name,siteRecords.find(row=>row.id===feature.properties.id).name);
    assert.equal(feature.properties.label,feature.properties.compact?String(feature.properties.number):feature.properties.name);
  }
  site.destroy();
});

check('all 70 actual identities fit separate 24 by 20 numbered cards clear of phone legend, location card and right-side tools',()=>{
  for(const width of [320,390]){
    const height=568,insets={top:182,bottom:190,left:12,right:65};
    const items=records.map((row,index)=>({id:row.id,name:row.name,number:index+1,x:width/2,y:284,width:179,height:66}));
    const snapshot=clone(items),placed=layoutBeaconLabels(items,{width,height,insets});
    assert.deepEqual(items,snapshot);assert.equal(placed.length,70);assert.deepEqual(placed.map(row=>row.id).sort(),expected);
    assert(placed.every(row=>row.compact&&!row.overlapFallback&&row.width===24&&row.height===20));
    assertClamped(placed,width,height,insets);assertSeparate(placed);
    assert.deepEqual(layoutBeaconLabels(items,{width,height,insets}),placed,'Compact arrangement is deterministic');
    for(const row of placed){assert.equal(row.id,records[row.number-1].id);assert.equal(row.name,records[row.number-1].name);}
    // Exercise actual create/refresh rectangle handling, not only the pure grid:
    // each measured UI boundary adds its required eight-pixel clearance.
    const phoneDocument={
      createElement(tag){const el=element(tag);el.getBoundingClientRect=()=>({left:0,top:126,right:width,bottom:174});return el;},
      getElementById(id){return id==='location-card'?{getBoundingClientRect:()=>({top:height-182,bottom:height,left:0,right:width})}:null;},
      querySelector(selector){return selector==='.map-tools'?{getBoundingClientRect:()=>({left:width-57,right:width,top:190,bottom:height-190})}:null;}
    };
    const phoneMap=new MapFacade(width,height),phone=createBuildingBeacons({map:phoneMap,records,documentObject:phoneDocument});
    const phoneState=phone.getState(),phonePositions=phoneState.labelPositions.map(p=>({...p,labelX:p.x,labelY:p.y}));
    assert.equal(phoneState.count,70);assert.equal(phoneState.viewportLabelCount,70);assert.equal(phoneState.overlapFallbackCount,0);
    assert.equal(phoneState.labelMode,'numbers');assert(phonePositions.every(row=>row.compact&&row.width===24&&row.height===20));
    assertClamped(phonePositions,width,height,insets);assertSeparate(phonePositions);phone.destroy();
    compactScenarios.push({width,height,insets,identities:placed.length,card_pixels:[24,20],overlap_fallback_labels:0,
      pairwise_overlap_count:0,runtime_ui_rectangles_checked:true});
  }
});

check('edge and offscreen layout inputs clamp cards without dropping IDs; dense overflow is explicit',()=>{
  for(const [width,height] of [[390,844],[1280,800],[240,320]])for(const [x,y] of [[0,0],[width,height],[-100,-100],[width+100,height+100]]){
    const items=Array.from({length:20},(_,i)=>({id:`edge-${i}`,x,y,width:176,height:60}));
    const output=layoutBeaconLabels(items,{width,height});assert.equal(output.length,20);assert.deepEqual(output.map(p=>p.id),items.map(p=>p.id));assertClamped(output,width,height);
    if(width>=390)assertSeparate(output);
  }
  const dense=records.map(r=>({id:r.id,x:120,y:160,width:176,height:60}));
  const output=layoutBeaconLabels(dense,{width:100,height:100});assert.equal(output.length,70);
  assert.deepEqual(output.map(p=>p.id).sort(),expected);assertClamped(output,100,100);assert(output.some(p=>p.overlapFallback));
});

check('140 actual card-center clicks resolve exact IDs even when native rendered-feature hits deliberately name another building',()=>{
  for(const [width,height,mode] of [[1920,1080,'names'],[320,568,'numbers']]){
    Object.assign(map,{width,height,zoom:8});Object.assign(map.canvas,{width,height,clientWidth:width,clientHeight:height});beacons.refresh();
    assert.equal(beacons.getState().labelMode,mode);
    const source=map.getSource(map.layers.get(labelsLayer).source),beforeMode=selected.length;
    const positions=new Map(beacons.getState().labelPositions.map(point=>[point.id,point]));
    assert.equal(positions.size,70);
    for(const [index,feature] of source.data.features.entries()){const before=selected.length;
      assert.equal(feature.properties.compact,mode==='numbers');
      const point=positions.get(feature.properties.id),center={x:point.x,y:point.y};
      map.hits=[clone(source.data.features[(index+1)%70])];
      const beforeQueries=map.queries.length;assert.equal(beacons.hitTest(center),feature.properties.id);
      map.emit('click',{point:center,originalEvent:{preventDefault(){}}});
      assert.equal(selected.length,before+1);assert.equal(selected.at(-1),feature.properties.id);
      assert.equal(map.queries.length,beforeQueries,'A displaced card must bypass stale native symbol hit boxes');
    }
    assert.deepEqual(selected.slice(beforeMode).sort(),expected);
  }
  assert.equal(selected.length,140);
  const before=selected.length;map.hits=[{properties:{id:'not-in-catalogue'}}];map.emit('click',{point:{x:1,y:1},originalEvent:{preventDefault(){}}});assert.equal(selected.length,before);
  assert.deepEqual(map.queries.at(-1).options.layers,[anchorLayer],'Native fallback is restricted to undisplaced lamps');
});

check('screen-card picking wins over an underlying lamp, hover shares the result, and native fallback only queries anchors',()=>{
  const features=map.getSource(map.layers.get(labelsLayer).source).data.features;
  const label=beacons.getState().labelPositions.find(point=>point.id===features[17].properties.id);
  const center={x:label.x,y:label.y};map.hits=[features[3]];
  const before=selected.length,beforeQueries=map.queries.length,event={point:center,originalEvent:{preventDefault(){}}};
  map.emit('click',event);map.emit('click',event);assert.equal(selected.length,before+1);assert.equal(selected.at(-1),features[17].properties.id);
  map.emit('mousemove',{point:center});assert.equal(map.canvas.style.cursor,'pointer');assert.equal(map.queries.length,beforeQueries);
  map.hits=[{properties:{id:'not-in-catalogue'}}];map.emit('mousemove',{point:{x:1,y:1}});assert.equal(map.canvas.style.cursor,'');
  map.hits=[features[3]];assert.equal(beacons.hitTest({x:1,y:1}),features[3].properties.id);assert.deepEqual(map.queries.at(-1).options.layers,[anchorLayer]);
  assert.equal(beacons.hitTest(null),null);assert.equal(beacons.hitTest({x:NaN,y:1}),null);
  assert.equal(hitTestBeaconLabels([{id:'under',x:40,y:40,width:24,height:20},{id:'top',x:40,y:40,width:24,height:20}],{x:40,y:40}),'top');
  assert.equal(hitTestBeaconLabels([{id:'only',x:40,y:40,width:24,height:20}],{x:53,y:40}),null);
});

check('disposal releases owned sprite resources and a later click cannot navigate',()=>{
  const oldFeatures=map.getSource(map.layers.get(labelsLayer).source).data.features;
  const before=selected.length;beacons.destroy();beacons.destroy();assert.equal(map.sources.size,0);assert.equal(map.layers.size,0);assert.equal(map.images.size,0);assert.equal(map.events.length,0);
  map.hits=[oldFeatures[0]];map.emit('click',{point:{x:20,y:20}});assert.equal(selected.length,before);
});

const bindings=['./beacon-checks.mjs','../../../src/building-beacons.js','../../landmarks.json','../../candidate-city-integrations.json','../../districts.json'].map(path=>{
  const bytes=readFileSync(new URL(path,import.meta.url));return {path,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')};});
const report={schema:'building-beacon-contract-checks-v1',passed:checks.length,checks,catalogue_count:70,district_count:16,district_counts:districtCounts,
  scenarios,compactScenarios,bindings,scope:'Independent real-catalogue identity, pure layout, in-viewport full-name/number filters with all 70 source anchors retained, literal style-vector offsets, horizon handling, fixed-pixel contracts, card-center picking against deliberately stale native hits and click dispatch using a map/canvas facade. This is not SDK style validation or actual WebGL/glyph visibility; those require separate vendor and browser checks.'};
writeFileSync(new URL('./beacon-checks.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:checks.length,catalogue_count:70,district_count:16,viewport_zoom_scenarios:scenarios.length}));
