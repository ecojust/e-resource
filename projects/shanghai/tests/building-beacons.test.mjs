import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {layoutBeaconLabels,hitTestBeaconLabels,projectBeaconAnchor,beaconPerspectiveScale,createBuildingBeacons} from '../src/building-beacons.js';
import {candidateOverviewCamera} from '../src/candidate-overview-camera.js';

const clone=value=>structuredClone(value);
class Element {
  constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.style={};this.dataset={};this.listeners=new Map();this.attributes={};this.width=0;this.height=0;this.textContent='';this.parentNode=null;
    const classes=new Set();this.classList={add(...names){for(const name of names)classes.add(name);},remove(...names){for(const name of names)classes.delete(name);},toggle(name){if(classes.has(name))classes.delete(name);else classes.add(name);},contains:name=>classes.has(name)};
  }
  append(...nodes){for(const node of nodes){this.children.push(node);node.parentNode=this;}}
  appendChild(node){this.append(node);return node;}
  remove(){if(this.parentNode)this.parentNode.children=this.parentNode.children.filter(n=>n!==this);this.parentNode=null;}
  setAttribute(name,value){this.attributes[name]=String(value);}
  addEventListener(name,listener){this.listeners.set(name,listener);}
  removeEventListener(name){this.listeners.delete(name);}
  getContext(){return new Proxy({measureText:text=>({width:[...text].length*7}),
    getImageData:()=>({data:new Uint8ClampedArray(this.width*this.height*4),width:this.width,height:this.height}),
    createLinearGradient:()=>({addColorStop(){}}),createRadialGradient:()=>({addColorStop(){}})},
    {get:(object,key)=>key in object?object[key]:(()=>{})});}
  getBoundingClientRect(){return {left:0,top:0,width:this.clientWidth||this.width,height:this.clientHeight||this.height};}
}
const mockDocument=()=>({createElement:tag=>new Element(tag)});

class BeaconMap {
  constructor({width=1200,height=800}={}){
    this.width=width;this.height=height;this.zoom=8;this.center={lng:121,lat:31};
    this.sources=new Map();this.layers=new Map();this.images=new Map();this.listeners=[];this.operations=[];
    this.canvas=new Element('canvas');this.canvas.width=this.canvas.clientWidth=width;this.canvas.height=this.canvas.clientHeight=height;
    this.container=new Element('div');this.container.clientWidth=width;this.container.clientHeight=height;
  }
  on(type,layer,listener){if(typeof layer==='function'){listener=layer;layer=null;}this.listeners.push({type,layer,listener});return this;}
  off(type,layer,listener){if(typeof layer==='function'){listener=layer;layer=null;}this.listeners=this.listeners.filter(x=>x.type!==type||x.layer!==layer||x.listener!==listener);return this;}
  emit(type,event={},layer=null){for(const x of [...this.listeners])if(x.type===type&&(!x.layer||x.layer===layer))x.listener(event);}
  addImage(id,image,options){assert(!this.images.has(id));this.images.set(id,{image,options});this.operations.push(['addImage',id]);}
  hasImage(id){return this.images.has(id);}
  removeImage(id){this.images.delete(id);this.operations.push(['removeImage',id]);}
  addSource(id,options){assert(!this.sources.has(id));this.sources.set(id,{...options,data:clone(options.data),setData(data){this.data=clone(data);}});this.operations.push(['addSource',id]);}
  getSource(id){return this.sources.get(id);}
  removeSource(id){assert(![...this.layers.values()].some(l=>l.source===id));this.sources.delete(id);this.operations.push(['removeSource',id]);}
  addLayer(layer,before){assert(!this.layers.has(layer.id));this.layers.set(layer.id,clone(layer));this.operations.push(['addLayer',layer.id,before]);}
  getLayer(id){return this.layers.get(id);}
  setLayoutProperty(id,name,value){const layer=this.layers.get(id);assert(layer);layer.layout[name]=clone(value);this.operations.push(['setLayoutProperty',id,name]);}
  removeLayer(id){this.layers.delete(id);this.operations.push(['removeLayer',id]);}
  getStyle(){return {layers:[...this.layers.values()]};}
  moveLayer(id,before){this.operations.push(['moveLayer',id,before]);}
  getCanvas(){return this.canvas;}
  getContainer(){return this.container;}
  getZoom(){return this.zoom;}
  getCenter(){return this.center;}
  getBearing(){return 0;}
  getPitch(){return 60;}
  isStyleLoaded(){return true;}
  triggerRepaint(){}
  project(point){const lng=point.lng??point[0],lat=point.lat??point[1],scale=10000*2**(this.zoom-8);return {x:this.width/2+(lng-this.center.lng)*scale,y:this.height/2-(lat-this.center.lat)*scale};}
  unproject(point){const x=point.x??point[0],y=point.y??point[1],scale=10000*2**(this.zoom-8),lng=this.center.lng+(x-this.width/2)/scale,lat=this.center.lat-(y-this.height/2)/scale;return {lng,lat,toArray:()=>[lng,lat]};}
  queryRenderedFeatures(point,options={}){(this.queryCalls??=[]).push({point,options});return (this.clickedFeatures||[]).filter(feature=>!feature.layer?.id||!options.layers||options.layers.includes(feature.layer.id));}
  nativeClick(hitByLayer,point={x:195,y:422}){
    const originalEvent={preventDefault(){}};
    for(const listener of [...this.listeners])if(listener.type==='click'){
      const features=listener.layer?hitByLayer.get(listener.layer):undefined;
      if(!listener.layer||features?.length)listener.listener({features,point,originalEvent});
    }
  }
}
const records=Array.from({length:70},(_,i)=>({id:`model-${i}`,name:`建筑 ${i}`,lng:121+(i%10)*.0001,lat:31+Math.floor(i/10)*.0001,districtId:i<20?'310151':'310101'}));
const pointSources=map=>[...map.sources.values()].filter(s=>s.data?.features?.length&&s.data.features.every(f=>f.geometry.type==='Point'));
const idsOf=source=>source.data.features.map(f=>f.properties?.id??f.id).sort();
const expectedIDs=records.map(r=>r.id).sort();
function assertSeparated(placed){
  for(let i=0;i<placed.length;i++)for(let j=0;j<i;j++){
    const a=placed[i],b=placed[j],ax=a.labelX??a.x,ay=a.labelY??a.y,bx=b.labelX??b.x,by=b.labelY??b.y;
    assert(Math.abs(ax-bx)>=(a.width+b.width)/2||Math.abs(ay-by)>=(a.height+b.height)/2,`${a.id} overlaps ${b.id}`);
  }
}
function assertWithin(placed,{left,top,right,bottom}){
  for(const item of placed){const x=item.labelX??item.x,y=item.labelY??item.y;
    assert(x-item.width/2>=left&&x+item.width/2<=right,`${item.id} overlaps a reserved side panel`);
    assert(y-item.height/2>=top&&y+item.height/2<=bottom,`${item.id} overlaps a reserved header or footer`);
  }
}
function evaluateStyleExpression(expression,properties){
  if(!Array.isArray(expression)||typeof expression[0]!=='string')return expression;
  const [operator,...args]=expression;
  if(operator==='get')return properties[args[0]];
  if(operator==='literal')return args[0];
  if(operator==='all')return args.every(value=>evaluateStyleExpression(value,properties));
  if(operator==='!')return !evaluateStyleExpression(args[0],properties);
  if(operator==='match'){
    const value=evaluateStyleExpression(args[0],properties);
    for(let i=1;i<args.length-1;i+=2)if(args[i]===value)return evaluateStyleExpression(args[i+1],properties);
    return evaluateStyleExpression(args.at(-1),properties);
  }
  assert.fail(`Unexpected style expression: ${operator}`);
}
function nativeGroundSymbolRatio(transform,lib,coordinate){
  // The native symbol shader uses the projected ground anchor's homogeneous W.
  // Compute that independently from the vendor matrix, not the production
  // helper's public-value approximation of the same depth.
  const mercator=lib.MercatorCoordinate.fromLngLat(coordinate),matrix=transform._pixelMatrix3D;
  const w=matrix[3]*mercator.x*transform.worldSize+matrix[7]*mercator.y*transform.worldSize+matrix[15];
  return Math.max(0,Math.min(4,.5+.5*transform.cameraToCenterDistance/w));
}

test('twenty coincident site labels retain unique IDs and fit a readable mobile layout',()=>{
  const items=Array.from({length:20},(_,i)=>({id:`site-${i}`,x:195,y:422,width:120,height:24}));
  const original=clone(items),placed=layoutBeaconLabels(items,{width:390,height:844});
  assert.equal(placed.length,20);assert.deepEqual(placed.map(x=>x.id).sort(),items.map(x=>x.id).sort());assert.deepEqual(items,original);
  for(const row of placed){
    assert(Number.isFinite(row.labelX)&&Number.isFinite(row.labelY));
    assert(row.labelX-row.width/2>=0&&row.labelX+row.width/2<=390);
    assert(row.labelY-row.height/2>=0&&row.labelY+row.height/2<=844);
  }
  for(let i=0;i<placed.length;i++)for(let j=0;j<i;j++){
    const a=placed[i],b=placed[j];assert(Math.abs(a.labelX-b.labelX)>=(a.width+b.width)/2||Math.abs(a.labelY-b.labelY)>=(a.height+b.height)/2,`${a.id} overlaps ${b.id}`);
  }
});

test('layout preserves all seventy identifiers even when the viewport cannot fit every label',()=>{
  const items=records.map(r=>({id:r.id,x:195,y:350,width:180,height:30}));
  const placed=layoutBeaconLabels(items,{width:390,height:500});
  assert.equal(placed.length,70);assert.deepEqual(placed.map(r=>r.id).sort(),expectedIDs);
  assert(placed.every(r=>Number.isFinite(r.labelX)&&Number.isFinite(r.labelY)));
  assert.deepEqual(layoutBeaconLabels(items,{width:390,height:500}),placed,'layout should be deterministic');
});

test('seventy dense mobile signs become separate numbered cards outside reserved interface rectangles',()=>{
  const items=records.map((r,i)=>({id:r.id,number:i+1,x:195,y:422,width:176,height:62}));
  const options={width:390,height:844,insets:{top:182,bottom:190,left:12,right:65}};
  const placed=layoutBeaconLabels(items,options);
  assert.equal(placed.length,70);assert.deepEqual(placed.map(r=>r.id).sort(),expectedIDs);
  assert(placed.every(r=>r.compact===true&&r.width===24&&r.height===20&&r.overlapFallback===false));
  assertSeparated(placed);assertWithin(placed,{left:12,top:182,right:325,bottom:654});
  const byId=list=>Object.fromEntries(list.map(({id,number})=>[id,number]));
  assert.deepEqual(byId(placed),byId(items));
  assert.deepEqual(byId(layoutBeaconLabels([...items].reverse(),options)),byId(items),'numbering follows stable model identity, not layout traversal');
});

test('seventy numbered cards also fit a narrow 320 by 568 viewport with full reserved insets',()=>{
  const items=records.map((r,i)=>({id:r.id,number:i+1,x:160,y:284,width:179,height:66}));
  const placed=layoutBeaconLabels(items,{width:320,height:568,insets:{top:182,bottom:190,left:12,right:65}});
  assert.equal(placed.length,70);assert.deepEqual(placed.map(r=>r.id).sort(),expectedIDs);
  assert(placed.every(r=>r.compact===true&&r.width===24&&r.height===20&&r.overlapFallback===false));
  assertSeparated(placed);assertWithin(placed,{left:12,top:182,right:255,bottom:378});
  assert.deepEqual(placed.map(r=>r.number),Array.from({length:70},(_,i)=>i+1));
});

test('normal desktop capacity retains full name cards while avoiding the sidebar and header/footer',()=>{
  const items=records.slice(0,20).map((r,i)=>({id:r.id,number:i+1,x:190,y:100,width:176,height:62}));
  const placed=layoutBeaconLabels(items,{width:1200,height:800,insets:{left:360,right:88,top:154,bottom:152}});
  assert(placed.every(r=>r.compact===false&&r.width===176&&r.height===62&&r.overlapFallback===false));
  assertSeparated(placed);assertWithin(placed,{left:360,top:154,right:1112,bottom:648});
});

test('all model beacons use real sprite symbols with fixed pixels and no collision culling at any supported zoom',()=>{
  const map=new BeaconMap(),original=clone(records),beacons=createBuildingBeacons({map,records,onSelect(){},documentObject:mockDocument()});
  assert(map.images.size>0,'addImage must install an actual icon sprite');
  const symbols=[...map.layers.values()].filter(l=>l.type==='symbol');assert(symbols.length>0);
  for(const layer of symbols){
    assert((layer.minzoom??0)<=8);assert(layer.maxzoom===undefined||layer.maxzoom>24,'exclusive maxzoom must not hide beacons at the scene maximum');
    if(layer.layout['icon-image']){assert.equal(layer.layout['icon-allow-overlap'],true);assert.equal(layer.layout['icon-ignore-placement'],true);assert.equal(typeof layer.layout['icon-size'],'number');}
    if(layer.layout['text-field']){assert.equal(layer.layout['text-allow-overlap'],true);assert.equal(layer.layout['text-ignore-placement'],true);assert.equal(typeof layer.layout['text-size'],'number');}
  }
  for(const zoom of [8,14,19,24]){
    map.zoom=zoom;beacons.refresh();
    assert(pointSources(map).some(s=>JSON.stringify(idsOf(s))===JSON.stringify(expectedIDs)),'all anchors remain registered independently of zoom');
    for(const layer of symbols){
      const source=map.getSource(layer.source);assert.notEqual(source.cluster,true);
      assert.deepEqual(idsOf(source),expectedIDs,'both name signs and anchors retain every model at every zoom');
      assert.notEqual(layer.layout.visibility,'none');
    }
    assert.equal(beacons.getState().count,70);
  }
  assert.deepEqual(records,original);beacons.destroy();
});

test('beacon click resolves the exact model and disposal releases only owned layers, images and listeners',()=>{
  const map=new BeaconMap({width:390,height:844}),selected=[];
  map.addSource('unrelated',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
  map.addLayer({id:'unrelated',type:'line',source:'unrelated'});
  const beacons=createBuildingBeacons({map,records,onSelect:row=>selected.push(row),documentObject:mockDocument()});
  const layer=[...map.layers.values()].find(l=>l.type==='symbol'&&l.id.endsWith('-numbers'));
  const feature=map.getSource(layer.source).data.features.find(f=>(f.properties?.id??f.id)==='model-17');
  assert(feature,'each model has an individually addressable beacon');map.clickedFeatures=[feature];
  const position=beacons.getState().labelPositions.find(p=>p.id==='model-17');
  map.emit('click',{features:[feature],point:{x:position.x,y:position.y},originalEvent:{preventDefault(){}}},layer.id);
  assert.equal(selected.length,1);assert.equal(selected[0].id,'model-17');
  beacons.destroy();beacons.destroy();assert.deepEqual([...map.layers.keys()],['unrelated']);assert.deepEqual([...map.sources.keys()],['unrelated']);assert.equal(map.images.size,0);assert.equal(map.listeners.length,0);
  map.emit('click',{features:[feature]},layer.id);assert.equal(selected.length,1);
});

test('a name sign overlapping another model anchor selects its topmost model only once',()=>{
  const map=new BeaconMap(),selected=[],beacons=createBuildingBeacons({map,records,onSelect:row=>selected.push(row.id),documentObject:mockDocument()});
  const symbols=[...map.layers.values()].filter(l=>l.type==='symbol');
  const labelLayer=symbols.find(l=>l.layout['text-field']),anchorLayer=symbols.find(l=>!l.layout['text-field']);
  const label=map.getSource(labelLayer.source).data.features.find(f=>f.properties.id==='model-17');
  const anchor=map.getSource(anchorLayer.source).data.features.find(f=>f.properties.id==='model-2');
  map.clickedFeatures=[{...label,layer:{id:labelLayer.id}},{...anchor,layer:{id:anchorLayer.id}}];
  const position=beacons.getState().labelPositions.find(p=>p.id==='model-17');
  map.nativeClick(new Map([[labelLayer.id,[label]],[anchorLayer.id,[anchor]]]),{x:position.x,y:position.y});
  assert.deepEqual(selected,['model-17']);beacons.destroy();
});

test('screen hit testing uses current card bounds and reverse drawing order',()=>{
  const cards=[{id:'lower',labelX:100,labelY:80,width:40,height:20},
    {id:'upper',labelX:110,labelY:80,width:30,height:20}];
  assert.equal(hitTestBeaconLabels(cards,{x:100,y:80}),'upper');
  assert.equal(hitTestBeaconLabels(cards,{x:80,y:70}),'lower','the visible rectangle includes its border');
  assert.equal(hitTestBeaconLabels(cards,{x:79.9,y:80}),null);
  assert.equal(hitTestBeaconLabels([{id:'state-row',x:20,y:30,width:24,height:20}],{x:20,y:30}),'state-row');
  for(const point of [null,undefined,{x:NaN,y:80},{x:100,y:Infinity}])assert.equal(hitTestBeaconLabels(cards,point),null);
  assert.equal(hitTestBeaconLabels([],{x:100,y:80}),null);
});

for(const [count,viewport] of [[40,{width:1200,height:800}],[70,{width:320,height:568}]])
  test(`${count} current card centers select their own IDs despite stale native symbol query boxes`,()=>{
    const map=new BeaconMap(viewport),rows=records.slice(0,count),selected=[];
    const beacons=createBuildingBeacons({map,records:rows,onSelect:row=>selected.push(row.id),documentObject:mockDocument()});
    const symbols=[...map.layers.values()].filter(layer=>layer.type==='symbol');
    const labelLayer=symbols.find(layer=>layer.layout['text-field']),anchorLayer=symbols.find(layer=>!layer.layout['text-field']);
    for(const cycle of [0,1]){
      if(cycle){map.center={lng:121.0004,lat:31.0002};beacons.refresh();}
      const positions=beacons.getState().labelPositions;assert.equal(positions.length,count);
      assertSeparated(positions);
      for(let i=0;i<positions.length;i++){
        const current=positions[i],wrong=positions[(i+1)%count],point={x:current.x,y:current.y};
        const stale={id:wrong.id,properties:{id:wrong.id},layer:{id:labelLayer.id}};
        const underneath={id:wrong.id,properties:{id:wrong.id},layer:{id:anchorLayer.id}};
        map.clickedFeatures=[stale,underneath];map.queryCalls=[];
        assert.equal(beacons.hitTest(point),current.id);
        assert.equal(hitTestBeaconLabels(positions,point),current.id);
        const before=selected.length;let prevented=0;
        const event={features:[stale],point,originalEvent:{preventDefault(){prevented++;}}};
        map.emit('click',event);map.emit('click',event);
        assert.equal(selected.length,before+1,'one browser event must navigate once');
        assert.equal(selected.at(-1),current.id);assert.equal(prevented,1);
        assert.equal(map.queryCalls.length,0,'current card bounds take precedence over every native symbol hit box');
      }
    }
    beacons.destroy();
  });

test('blank space ignores stale label hits, anchor fallback is scoped, and hover uses the same current geometry',()=>{
  const map=new BeaconMap({width:390,height:844}),selected=[];
  const beacons=createBuildingBeacons({map,records,onSelect:row=>selected.push(row.id),documentObject:mockDocument()});
  const symbols=[...map.layers.values()].filter(layer=>layer.type==='symbol');
  const labelLayers=symbols.filter(layer=>layer.layout['text-field']),anchorLayer=symbols.find(layer=>!layer.layout['text-field']);
  const staleLabels=labelLayers.map(layer=>({properties:{id:'model-17'},layer:{id:layer.id}}));
  const blank={x:1,y:1};map.clickedFeatures=staleLabels;
  assert.equal(beacons.hitTest(blank),null);
  map.emit('click',{point:blank,features:staleLabels,originalEvent:{preventDefault(){assert.fail('blank click must pass through');}}});
  assert.deepEqual(selected,[]);
  for(const query of map.queryCalls)assert.deepEqual(query.options.layers,[anchorLayer.id]);
  const position=beacons.getState().labelPositions.find(row=>row.id==='model-17'),point={x:position.x,y:position.y};
  map.emit('mousemove',{point});assert.equal(map.canvas.style.cursor,'pointer');
  map.emit('mousemove',{point:blank,features:staleLabels});assert.equal(map.canvas.style.cursor,'');
  map.clickedFeatures=[...staleLabels,{properties:{id:'model-2'},layer:{id:anchorLayer.id}}];
  assert.equal(beacons.hitTest(blank),'model-2');
  map.emit('click',{point:blank});assert.deepEqual(selected,['model-2']);
  map.emit('mousemove',{point:blank});assert.equal(map.canvas.style.cursor,'pointer');
  map.emit('mouseout',{});assert.equal(map.canvas.style.cursor,'');
  map.clickedFeatures=[{properties:{id:'not-a-delivered-model'},layer:{id:anchorLayer.id}}];
  assert.equal(beacons.hitTest(blank),null);
  map.emit('mousemove',{point});assert.equal(map.canvas.style.cursor,'pointer');
  beacons.destroy();assert.equal(map.canvas.style.cursor,'');assert.equal(map.listeners.length,0);
  map.emit('mousemove',{point});map.emit('click',{point});
  assert.equal(map.canvas.style.cursor,'');assert.deepEqual(selected,['model-2']);
});

for(const viewport of [{width:390,height:844},{width:320,height:568}])test(`${viewport.width} by ${viewport.height}: compact runtime signs retain all seventy full names and stable numbers through zoom changes`,()=>{
  const map=new BeaconMap(viewport),beacons=createBuildingBeacons({map,records,onSelect(){},documentObject:mockDocument()});
  const labelLayer=[...map.layers.values()].find(l=>l.type==='symbol'&&l.layout['text-field']);
  let state=beacons.getState();assert.equal(state.labelMode,'numbers');assert.equal(state.viewportLabelCount,70);assert.equal(state.overlapFallbackCount,0);
  assertSeparated(state.labelPositions);assertWithin(state.labelPositions,{left:12,top:182,right:viewport.width-64,bottom:viewport.height-174});
  assert.deepEqual(map.getSource(labelLayer.source).data.features.map(f=>f.properties.label),records.map((_,i)=>String(i+1)));
  for(const zoom of [8,14,19,24,8]){
    map.zoom=zoom;beacons.refresh();
    const features=map.getSource(labelLayer.source).data.features;assert.equal(features.length,70);
    for(let i=0;i<features.length;i++){
      const p=features[i].properties;assert.equal(p.id,records[i].id);assert.equal(p.name,records[i].name);assert.equal(p.number,i+1);
      assert.equal(p.label,p.compact?String(i+1):records[i].name);
    }
  }
  assert.equal(beacons.getState().labelMode,'numbers');beacons.destroy();
});

test('full names and compact numbers have complementary layers, with a fixed 24 by 20 number sprite',()=>{
  const map=new BeaconMap({width:320,height:568}),beacons=createBuildingBeacons({map,records,onSelect(){},documentObject:mockDocument()});
  const textLayers=[...map.layers.values()].filter(l=>l.type==='symbol'&&l.layout['text-field']);assert.equal(textLayers.length,2);
  const evaluate=(expression,properties)=>{
    if(!Array.isArray(expression))return expression;
    const [op,...args]=expression;
    if(op==='get')return properties[args[0]];
    if(op==='all')return args.every(value=>evaluate(value,properties));
    if(op==='!')return !evaluate(args[0],properties);
    if(op==='==')return evaluate(args[0],properties)===evaluate(args[1],properties);
    assert.fail(`Unexpected filter operator: ${op}`);
  };
  for(const compact of [false,true])assert.equal(textLayers.filter(layer=>evaluate(layer.filter,{compact,inViewport:true})).length,1,'each visible sign renders in exactly one text layer');
  const numbers=textLayers.find(layer=>evaluate(layer.filter,{compact:true,inViewport:true})),names=textLayers.find(layer=>evaluate(layer.filter,{compact:false,inViewport:true}));
  assert.equal(numbers.layout['icon-text-fit'],'none');assert.equal(numbers.layout['text-size'],12);
  assert.equal(numbers.layout['icon-size'],1);assert.equal(names.layout['icon-text-fit'],'none');
  const sprite=map.images.get(evaluateStyleExpression(numbers.layout['icon-image'],map.getSource(numbers.source).data.features[0].properties));assert(sprite);
  assert.equal(sprite.image.width/sprite.options.pixelRatio,24);assert.equal(sprite.image.height/sprite.options.pixelRatio,20);
  assert.equal(sprite.options.stretchX,undefined);assert.equal(sprite.options.stretchY,undefined);
  beacons.destroy();
});

test('offscreen name cards are filtered while all seventy geographic anchors and records remain registered',()=>{
  const map=new BeaconMap({width:390,height:844}),beacons=createBuildingBeacons({map,records,onSelect(){},documentObject:mockDocument()});
  const symbols=[...map.layers.values()].filter(layer=>layer.type==='symbol');
  const labels=symbols.filter(layer=>layer.layout['text-field']),anchor=symbols.find(layer=>!layer.layout['text-field']);
  assert.equal(anchor.filter,undefined,'the original lamp anchors must not inherit card viewport filtering');
  for(const zoom of [8,24,8]){
    map.zoom=zoom;beacons.refresh();
    const state=beacons.getState(),visible=new Set(state.labelPositions.map(row=>row.id));
    const features=map.getSource(labels[0].source).data.features;
    assert.equal(features.length,70);assert.deepEqual(idsOf(map.getSource(labels[0].source)),expectedIDs);
    assert.deepEqual(idsOf(map.getSource(anchor.source)),expectedIDs);
    if(zoom===24)assert(visible.size>0&&visible.size<70,'the fixture must contain both on-screen and offscreen records');
    else assert.equal(visible.size,70,'zooming out restores all name cards without re-registering records');
    for(const feature of features){
      const properties=feature.properties;
      assert.equal(properties.inViewport,visible.has(properties.id));
      assert.equal(labels.filter(layer=>evaluateStyleExpression(layer.filter,properties)).length,properties.inViewport?1:0,
        `${properties.id} must render exactly one card only when its geographic anchor is in the viewport`);
    }
  }
  beacons.destroy();
});

test('runtime reflows around the real desktop sidebar bounds and frees its area after closing',()=>{
  const map=new BeaconMap(),doc=mockDocument(),panel=new Element();panel.inert=false;
  panel.getBoundingClientRect=()=>({left:20,right:348,top:160,bottom:650,width:328,height:490});
  doc.getElementById=id=>id==='explore-panel'?panel:null;
  const beacons=createBuildingBeacons({map,records:records.slice(0,20),onSelect(){},documentObject:doc});
  const before=beacons.getState().labelPositions;assertWithin(before,{left:360,top:154,right:1112,bottom:648});assertSeparated(before);
  panel.classList.add('closed');beacons.refresh();const after=beacons.getState().labelPositions;
  assertWithin(after,{left:12,top:154,right:1112,bottom:648});assertSeparated(after);
  assert.notDeepEqual(after,before);beacons.destroy();
});

test('narrow-phone signs avoid actual tool, legend and location-card rectangles as those elements resize',()=>{
  const map=new BeaconMap({width:320,height:568});
  let toolLeft=263,cardTop=386,legendBottom=174;
  const tools=new Element(),card=new Element();
  tools.getBoundingClientRect=()=>({left:toolLeft,right:308,top:190,bottom:370});
  card.getBoundingClientRect=()=>({left:12,right:308,top:cardTop,bottom:550});
  const doc={
    createElement(tag){const element=new Element(tag),rect=element.getBoundingClientRect.bind(element);
      element.getBoundingClientRect=()=>element.id==='building-beacon-legend'?{left:18,right:302,top:126,bottom:legendBottom}:rect();return element;},
    getElementById:id=>id==='location-card'?card:null,
    querySelector:selector=>selector==='.map-tools'?tools:null,
  };
  const beacons=createBuildingBeacons({map,records,onSelect(){},documentObject:doc});
  const check=()=>{
    const state=beacons.getState();assert.equal(state.viewportLabelCount,70);assert.equal(state.overlapFallbackCount,0);assert.equal(state.labelMode,'numbers');
    assert(state.labelPositions.every(p=>p.compact&&p.width===24&&p.height===20));assertSeparated(state.labelPositions);
    assertWithin(state.labelPositions,{left:12,right:toolLeft-8,top:Math.max(182,legendBottom+8),bottom:cardTop-8});
    assert.deepEqual(state.labelPositions.map(p=>p.number).sort((a,b)=>a-b),Array.from({length:70},(_,i)=>i+1));
  };
  check();toolLeft=260;cardTop=378;legendBottom=180;beacons.refresh();check();beacons.destroy();
});

test('all delivered models remain separate and clickable above a tall title card on a 320 by 568 phone',()=>{
  const delivered=[...JSON.parse(readFileSync(new URL('../data/landmarks.json',import.meta.url),'utf8')),
    ...JSON.parse(readFileSync(new URL('../data/candidate-city-integrations.json',import.meta.url),'utf8')).models];
  const count=delivered.length;assert(count>=70);
  assert(delivered.some(row=>[...row.name].length>12),'use the real long model titles');
  const map=new BeaconMap({width:320,height:568}),selected=[],tools=new Element(),card=new Element();
  // Citywide density keeps every geographic anchor on screen; the real title
  // card now occupies 228 px rather than the former shorter 190 px fixture.
  map.project=()=>({x:160,y:260});
  tools.getBoundingClientRect=()=>({left:263,right:308,top:190,bottom:370});
  card.getBoundingClientRect=()=>({left:12,right:308,top:348,bottom:556});
  const doc={
    createElement(tag){const element=new Element(tag),original=element.getBoundingClientRect.bind(element);
      element.getBoundingClientRect=()=>element.id==='building-beacon-legend'?{left:12,right:308,top:126,bottom:174}:original();return element;},
    getElementById:id=>id==='location-card'?card:null,
    querySelector:selector=>selector==='.map-tools'?tools:null,
  };
  const beacons=createBuildingBeacons({map,records:delivered,onSelect:row=>selected.push(row.id),documentObject:doc});
  const state=beacons.getState();
  assert.equal(state.viewportLabelCount,count);assert.equal(state.overlapFallbackCount,0);assert.equal(state.labelMode,'numbers');
  assert(state.labelPositions.every(row=>row.compact&&row.width===(count>70?22:24)&&row.height===20));
  assertSeparated(state.labelPositions);
  assertWithin(state.labelPositions,{left:12,right:255,top:182,bottom:340});
  assert.deepEqual(state.labelPositions.map(row=>row.id).sort(),delivered.map(row=>row.id).sort());
  for(const row of state.labelPositions){
    const point={x:row.x,y:row.y};
    assert.equal(beacons.hitTest(point),row.id);
    assert.equal(hitTestBeaconLabels(state.labelPositions,point),row.id);
    map.emit('click',{point});assert.equal(selected.at(-1),row.id);
  }
  assert.equal(selected.length,count);assert.equal(new Set(selected).size,count);
  beacons.destroy();
});

test('the 71st model uses a 22 by 20 emergency sprite while every number stays 12 px and individually clickable',()=>{
  const seventyOne=[...records,{id:'huangpu-new-wing-on-company',name:'新永安公司／七重天大楼',lng:121,lat:31,districtId:'310101'}];
  const map=new BeaconMap({width:320,height:568}),selected=[],tools=new Element(),card=new Element();
  map.project=()=>({x:160,y:260});
  tools.getBoundingClientRect=()=>({left:263,right:308,top:190,bottom:370});
  card.getBoundingClientRect=()=>({left:12,right:308,top:348,bottom:556});
  const doc={createElement:tag=>new Element(tag),getElementById:id=>id==='location-card'?card:null,
    querySelector:selector=>selector==='.map-tools'?tools:null};
  const beacons=createBuildingBeacons({map,records:seventyOne,onSelect:row=>selected.push(row.id),documentObject:doc});
  const state=beacons.getState(),numbers=[...map.layers.values()].find(layer=>layer.id.endsWith('-numbers'));
  assert.equal(state.count,71);assert.equal(state.viewportLabelCount,71);assert.equal(state.overlapFallbackCount,0);
  assert.equal(numbers.layout['text-size'],12);assert.equal(numbers.layout['icon-size'],1);assert.equal(numbers.layout['icon-text-fit'],'none');
  assert(state.labelPositions.every(row=>row.compact&&row.width===22&&row.height===20));
  assertSeparated(state.labelPositions);assertWithin(state.labelPositions,{left:12,right:255,top:182,bottom:340});
  for(const feature of map.getSource(numbers.source).data.features){
    const sprite=map.images.get(evaluateStyleExpression(numbers.layout['icon-image'],feature.properties));
    assert.equal(sprite.image.width/sprite.options.pixelRatio,22);assert.equal(sprite.image.height/sprite.options.pixelRatio,20);
    assert.equal(feature.properties.label,String(feature.properties.number));
  }
  for(const point of state.labelPositions){assert.equal(beacons.hitTest(point),point.id);map.emit('click',{point});assert.equal(selected.at(-1),point.id);}
  assert.equal(new Set(selected).size,71);beacons.destroy();
});

test('vendored MapLibre accepts every production beacon layer and keeps it visible at zoom 24',()=>{
  // Execute the actual shipped style-spec validator and layer factory. Only
  // map/GPU services unrelated to style acceptance are replaced by fixtures.
  const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
  context.exports=context.module.exports;context.self=context;context.globalThis=context;
  vm.runInNewContext(readFileSync(new URL('../vendor/maplibre-gl.js',import.meta.url),'utf8'),context);
  const {Style}=context.module.exports,map=new BeaconMap(),errors=[];
  const beacons=createBuildingBeacons({map,records,onSelect(){},documentObject:mockDocument()});
  const style=Object.create(Style.prototype);
  Object.assign(style,{_checkLoaded(){},_layers:{},_order:[],_removedLayers:{},_updatedSources:{},_globalState:{},
    getLayer(id){return this._layers[id];},_validateLayer(){},_updateLayer(){},fire(event){if(event.error)errors.push(event.error.message);},
    serialize:()=>({version:8,sources:Object.fromEntries([...map.sources].map(([id,s])=>[id,{type:'geojson',data:s.data}])),layers:[]}),
  });
  assert.equal(style._validate,Style.prototype._validate,'the real vendor validator must remain enabled');
  for(const layer of map.layers.values()){
    style.addLayer(clone(layer));assert.equal(errors.length,0,`${layer.id}: ${errors.join('; ')}`);
    const installed=style.getLayer(layer.id);assert(installed,`${layer.id} must actually be installed`);
    for(const zoom of [8,14,19,24])assert.equal(installed.isHidden(zoom),false,`${layer.id} hidden at ${zoom}`);
  }
  const specimen=clone([...map.layers.values()].find(l=>l.type==='symbol'));
  specimen.id='negative-control-maxzoom-25';specimen.maxzoom=25;style.addLayer(specimen);
  assert.equal(style.getLayer(specimen.id),undefined);assert.equal(errors.length,1);assert.match(errors[0],/maxzoom.*25.*maximum.*24/);
  beacons.destroy();
});

test('fixed name backgrounds, text and leaders agree with the actual ground projection below an elevated camera',()=>{
  const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
  context.exports=context.module.exports;context.self=context;context.globalThis=context;
  vm.runInNewContext(readFileSync(new URL('../vendor/maplibre-gl.js',import.meta.url),'utf8'),context);
  const lib=context.module.exports,style=Object.create(lib.Style.prototype);let transform;
  style.map={migrateProjection(next){transform=next;}};style.tileManagers={};style._setProjectionInternal('mercator');
  const delivered=JSON.parse(readFileSync(new URL('../data/candidate-city-integrations.json',import.meta.url),'utf8')).models;
  const stele={...delivered.find(row=>row.id==='chongming-stele-corridors'),city_integration:true};
  const viewport={width:960,height:720,insets:{left:16,right:64,top:154,bottom:152}},camera=candidateOverviewCamera(stele,viewport);
  assert.equal(camera.elevation,2.3);assert.equal(camera.pitch,50);
  transform.resize(viewport.width,viewport.height);transform.setFov(36.87);transform.setZoom(camera.zoom);
  transform.setCenter(lib.LngLat.convert(camera.center));transform.setElevation(camera.elevation);
  transform.setPadding(camera.padding);transform.setPitch(camera.pitch);transform.setBearing(camera.bearing);
  const map=new BeaconMap(viewport);map.transform=transform;
  map.project=point=>lib.Map.prototype.project.call({transform,style:{},terrain:null},point);
  map.unproject=point=>transform.screenPointToLocation({x:point.x??point[0],y:point.y??point[1]});
  const names=['门','学宫大成殿','崇明学宫尊经阁建筑','崇'.repeat(14),'崇'.repeat(25)];
  const rows=names.map((name,index)=>({...stele,id:`fixed-sign-${index}`,name,lng:stele.lng+index*.000005}));
  const original=map.project([stele.lng,stele.lat]),ground=projectBeaconAnchor(map,[stele.lng,stele.lat]);
  const actual=transform.coordinatePoint(lib.MercatorCoordinate.fromLngLat([stele.lng,stele.lat]),0,transform._pixelMatrix3D);
  assert.deepEqual([ground.x,ground.y],[actual.x,actual.y]);
  assert(ground.y-original.y>20,'the fixture must expose the previous centre-height projection error');
  const beacons=createBuildingBeacons({map,records:rows,onSelect(){},documentObject:mockDocument()});
  assert.equal(map.images.size,8,'five fixed name sprites, two number widths and one anchor lamp');
  const nameLayer=[...map.layers.values()].find(layer=>layer.id.endsWith('-labels-symbol'));
  assert(nameLayer);assert.equal(nameLayer.layout['icon-text-fit'],'none');
  const anchorLayer=[...map.layers.values()].find(layer=>layer.type==='symbol'&&!layer.layout['text-field']);
  const numberLayer=[...map.layers.values()].find(layer=>layer.id.endsWith('-numbers'));
  const features=map.getSource(nameLayer.source).data.features;
  const expectedSizes=[[84,34],[120,34],[176,34],[176,48],[176,62]];
  for(const [pitch,elevation] of [[50,2.3],[50,0],[0,0],[50,2.3]]){
    transform.setPitch(pitch);transform.setElevation(elevation);beacons.refresh();
    const state=beacons.getState();assert.equal(state.labelMode,'names');assert.equal(state.viewportLabelCount,5);
    if(pitch===0&&elevation===0){
      for(const layer of [anchorLayer,nameLayer,numberLayer])assert.equal(layer.layout['icon-size'],1,'flat ground views retain the constant icon size');
      for(const layer of [nameLayer,numberLayer])assert.equal(layer.layout['text-size'],12);
    }
    const leaders=[...map.sources.values()].find(source=>source.data.features[0]?.geometry.type==='LineString').data.features;
    for(let i=0;i<rows.length;i++){
      const row=rows[i],properties=features[i].properties,position=state.labelPositions.find(p=>p.id===row.id);
      const imageID=evaluateStyleExpression(nameLayer.layout['icon-image'],properties),sprite=map.images.get(imageID);
      assert.equal(typeof properties.sign,'string');assert(sprite);
      assert.deepEqual([sprite.image.width/sprite.options.pixelRatio,sprite.image.height/sprite.options.pixelRatio],expectedSizes[i]);
      assert.deepEqual([position.width,position.height],expectedSizes[i]);
      assert.equal(sprite.options.stretchX,undefined);assert.equal(sprite.options.stretchY,undefined);
      const anchor=projectBeaconAnchor(map,[row.lng,row.lat]),offset=[position.x-anchor.x,position.y-anchor.y];
      assert.deepEqual(evaluateStyleExpression(nameLayer.layout['icon-offset'],properties),offset);
      assert.deepEqual(evaluateStyleExpression(nameLayer.layout['text-offset'],properties),offset.map(v=>v/12));
      const ratio=nativeGroundSymbolRatio(transform,lib,[row.lng,row.lat]);
      const iconSize=evaluateStyleExpression(nameLayer.layout['icon-size'],properties);
      const textSize=evaluateStyleExpression(nameLayer.layout['text-size'],properties);
      assert(Math.abs(iconSize*ratio-1)<1e-8);assert(Math.abs(textSize*ratio-12)<1e-7);
      const iconOffset=evaluateStyleExpression(nameLayer.layout['icon-offset'],properties);
      const textOffset=evaluateStyleExpression(nameLayer.layout['text-offset'],properties);
      for(let axis=0;axis<2;axis++){
        const wanted=axis===0?position.x:position.y,start=axis===0?anchor.x:anchor.y;
        assert(Math.abs(start+iconOffset[axis]*iconSize*ratio-wanted)<.00001,'the native icon shader must draw the background at the hit rectangle centre');
        assert(Math.abs(start+textOffset[axis]*textSize*ratio-wanted)<.00001,'the native text shader must draw the name at that same centre');
        assert(Math.abs(expectedSizes[i][axis]*iconSize*ratio-(axis===0?position.width:position.height))<.00001,'native sprite bounds must retain their fixed screen dimensions');
      }
      assert(Math.abs(20*evaluateStyleExpression(anchorLayer.layout['icon-size'],properties)*ratio-20)<.00001,'the ground lamp remains 20 px');
      assert(Math.abs(24*evaluateStyleExpression(numberLayer.layout['icon-size'],properties)*ratio-24)<.00001,'the alternate number background remains 24 px');
      assert(Math.abs(evaluateStyleExpression(numberLayer.layout['text-size'],properties)*ratio-12)<.00001);
      const endpoint=leaders.find(feature=>feature.properties.id===row.id).geometry.coordinates[1];
      const projected=projectBeaconAnchor(map,endpoint);
      assert(Math.hypot(projected.x-position.x,projected.y-position.y)<.001,'ground-level leader endpoint must meet the same current card centre');
      assert.equal(beacons.hitTest({x:position.x,y:position.y}),row.id);
    }
  }
  beacons.destroy();assert.equal(map.images.size,0);
});

test('public transform depth compensation cancels the native symbol shader across bearings, pitches and elevations',()=>{
  const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
  context.exports=context.module.exports;context.self=context;context.globalThis=context;
  vm.runInNewContext(readFileSync(new URL('../vendor/maplibre-gl.js',import.meta.url),'utf8'),context);
  const lib=context.module.exports,style=Object.create(lib.Style.prototype);let transform;
  style.map={migrateProjection(next){transform=next;}};style.tileManagers={};style._setProjectionInternal('mercator');
  transform.resize(960,720);transform.setFov(36.87);transform.setMaxPitch(85);transform.setZoom(19.76);
  transform.setCenter(lib.LngLat.convert([121.397,31.621]));transform.setPadding({left:16,right:88,top:154,bottom:152});
  let cases=0;
  for(const bearing of [0,90,275])for(const pitch of [0,50,85])for(const elevation of [0,2.3,30]){
    transform.setBearing(bearing);transform.setPitch(pitch);transform.setElevation(elevation);
    for(const [east,north] of [[0,0],[.0001,.0001],[-.0001,.0001],[0,-.0002],[.0002,0]]){
      const coordinate=[121.397+east,31.621+north],ratio=nativeGroundSymbolRatio(transform,lib,coordinate);
      assert(ratio>0,'every fixture anchor is in front of the camera');
      const correction=beaconPerspectiveScale({transform},coordinate);
      assert(Math.abs(correction*ratio-1)<1e-8,`native ratio did not cancel at bearing ${bearing}, pitch ${pitch}, elevation ${elevation}`);
      if(pitch===0&&elevation===0)assert.equal(correction,1);
      cases++;
    }
  }
  assert.equal(cases,135);assert.equal(beaconPerspectiveScale({},[121.397,31.621]),1);
});

for(const count of [1,70])test(`${count} high-pitch signs use screen offsets above the horizon without unprojecting sky`,()=>{
  const map=new BeaconMap({width:390,height:844}),rows=records.slice(0,count),groundUnprojects=[],horizon=count===1?680:650;
  map.project=point=>({x:195+((point.lng??point[0])-121)*20,y:700+((point.lat??point[1])-31)*20});
  map.transform={isPointOnMapSurface:point=>(point.y??point[1])>=horizon};
  const originalUnproject=map.unproject.bind(map);
  map.unproject=point=>{assert(map.transform.isPointOnMapSurface(point),'sky screen positions must never be unprojected');groundUnprojects.push(point);return originalUnproject(point);};
  const beacons=createBuildingBeacons({map,records:rows,onSelect(){},documentObject:mockDocument()});
  const state=beacons.getState(),positions=new Map(state.labelPositions.map(p=>[p.id,p]));
  assert.equal(state.viewportLabelCount,count);assert(state.labelPositions.some(p=>p.y<horizon),'the fixture must really place a sign above the ground-plane horizon');
  const labels=[...map.layers.values()].filter(l=>l.type==='symbol'&&l.layout['text-field']);
  const numberLayer=labels.find(l=>l.id.endsWith('-numbers'));
  const labelData=map.getSource(labels[0].source).data.features;
  for(let i=0;i<rows.length;i++){
    const row=rows[i],feature=labelData.find(f=>f.properties.id===row.id),anchor=map.project([row.lng,row.lat]),position=positions.get(row.id);
    assert.deepEqual(feature.geometry.coordinates,[row.lng,row.lat],'the sign must retain its real geographic anchor');
    assert.equal(feature.properties.name,row.name);assert.equal(feature.properties.number,i+1);
    const offset=[position.x-anchor.x,position.y-anchor.y];
    assert(Object.values(feature.properties).every(value=>!Array.isArray(value)),'GeoJSON-vt properties must not carry vector arrays');
    for(const layer of labels)assert.deepEqual(evaluateStyleExpression(layer.layout['text-offset'],feature.properties),offset.map(v=>v/12));
    for(const layer of labels)assert.deepEqual(evaluateStyleExpression(layer.layout['icon-offset'],feature.properties),offset);
  }
  for(const layer of labels){assert.equal(layer.layout['text-offset'][0],'match');assert.deepEqual(evaluateStyleExpression(layer.layout['text-offset'],{id:'unknown'}),[0,0]);}
  assert.equal(numberLayer.layout['icon-offset'][0],'match');
  assert(groundUnprojects.length<count,'sky leaders are omitted while every sign remains');
  for(const source of map.sources.values())for(const feature of source.data.features){
    const points=feature.geometry.type==='LineString'?feature.geometry.coordinates:[feature.geometry.coordinates];
    for(const [lng,lat] of points)assert(lng>120.9&&lng<121.1&&lat>30.9&&lat<31.1,'no label or leader may jump behind the camera or outside the local city');
  }
  beacons.destroy();
});
