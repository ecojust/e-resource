const PREFIX='shanghai-building-beacons';
const ANCHORS=`${PREFIX}-anchors`,LABELS=`${PREFIX}-labels`,LINES=`${PREFIX}-leaders`;
const LAMP=`${PREFIX}-lamp`,SIGN=`${PREFIX}-sign`,NUMBER=`${PREFIX}-number`;
const NAME_SIGNS=[[84,34],[120,34],[176,34],[176,48],[176,62]].map(([width,height],i)=>({id:`${SIGN}-${i}`,width,height}));
const GROUND={getElevationForLngLat:()=>0};
const collection=features=>({type:'FeatureCollection',features});
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));

/** Preserve every ID. When the screen can fit the cards, use separate fixed-pixel
 * cells; at extreme density all signs remain present and the directory is the
 * accessible alternative to overlapping labels. No zoom-based culling/clusters.
 */
export function layoutBeaconLabels(items,{width,height,insets={}}){
  if(!items.length)return [];
  const margin=8,x0=Math.max(margin,insets.left||0),x1=Math.min(width-margin,width-(insets.right||0));
  const y0=Math.max(margin,insets.top||0),y1=Math.min(height-margin,height-(insets.bottom||0));
  const availableWidth=Math.max(24,x1-x0),availableHeight=Math.max(20,y1-y0);
  const makeGrid=(compact,gap=compact?2:7)=>{
    const maxW=compact?24:Math.min(availableWidth,Math.max(...items.map(p=>p.width))),maxH=compact?20:Math.max(...items.map(p=>p.height));
    const columns=Math.max(1,Math.floor((availableWidth+gap)/(maxW+gap))),rows=Math.max(1,Math.floor((availableHeight+gap)/(maxH+gap))),slots=[];
    const left=x0+(availableWidth-(columns*maxW+(columns-1)*gap))/2,top=y0+(availableHeight-(rows*maxH+(rows-1)*gap))/2;
    for(let y=0;y<rows;y++)for(let x=0;x<columns;x++)slots.push({x:left+maxW/2+x*(maxW+gap),y:top+maxH/2+y*(maxH+gap)});
    return slots;
  };
  let compact=false,slots=makeGrid(false);
  if(slots.length<items.length){compact=true;slots=makeGrid(true);}
  // A tall location card on a 320×568 phone leaves only seven rows. The
  // sprite's transparent border still separates cards when grid gap is zero.
  if(compact&&slots.length<items.length)slots=makeGrid(true,0);
  const used=new Set();
  const placed=new Map();
  for(const item of [...items].sort((a,b)=>a.y-b.y||a.x-b.x||a.id.localeCompare(b.id))){
    let best=-1,cost=Infinity;
    for(let i=0;i<slots.length;i++)if(!used.has(i)){
      const slot=slots[i],distance=(slot.x-item.x)**2+(slot.y-item.y)**2;
      if(distance<cost){cost=distance;best=i;}
    }
    const cardWidth=compact?24:item.width,cardHeight=compact?20:item.height;
    const slot=best>=0?slots[best]:{x:clamp(item.x,x0+cardWidth/2,x1-cardWidth/2),y:clamp(item.y,y0+cardHeight/2,y1-cardHeight/2)};
    if(best>=0)used.add(best);
    placed.set(item.id,{...item,width:cardWidth,height:cardHeight,labelX:slot.x,labelY:slot.y,compact,overlapFallback:best<0});
  }
  return items.map(item=>placed.get(item.id));
}

/** Dynamic symbol offsets render correctly, but MapLibre's symbol query boxes
 * can retain an earlier offset. Use the same screen rectangles as the sprites. */
export function hitTestBeaconLabels(layout,point){
  if(!point||!Number.isFinite(point.x)||!Number.isFinite(point.y))return null;
  for(let i=layout.length-1;i>=0;i--){
    const card=layout[i],x=card.labelX??card.x,y=card.labelY??card.y;
    if(Math.abs(point.x-x)<=card.width/2&&Math.abs(point.y-y)<=card.height/2)return card.id;
  }
  return null;
}

export function projectBeaconAnchor(map,coordinate){
  const transform=map.transform;
  // map.project uses the centre-height plane when elevation is non-zero;
  // GeoJSON symbol anchors are on the real ground plane instead.
  return transform?.locationToScreenPoint
    ?transform.locationToScreenPoint({lng:coordinate[0],lat:coordinate[1]},GROUND)
    :map.project(coordinate);
}
export function beaconPerspectiveScale(map,[lng,lat]){
  const t=map.transform;
  if(!t?.center||!t.cameraToCenterDistance||!t.worldSize||!Number.isFinite(t.pixelsPerMeter))return 1;
  const rad=Math.PI/180,mercY=latitude=>Math.log(Math.tan(Math.PI/4+latitude*rad/2));
  const east=(lng-t.center.lng)/360*t.worldSize,north=(mercY(lat)-mercY(t.center.lat))/(2*Math.PI)*t.worldSize;
  const bearing=t.bearing*rad,pitch=t.pitch*rad;
  const depth=t.cameraToCenterDistance+(east*Math.sin(bearing)+north*Math.cos(bearing))*Math.sin(pitch)+(t.elevation||0)*t.pixelsPerMeter*Math.cos(pitch);
  // The native symbol shader scales both size and offsets by this factor even
  // with viewport alignment. Cancel it so final cards/text remain fixed pixels.
  const ratio=clamp(.5+.5*t.cameraToCenterDistance/depth,0,4);
  return ratio>0?1/ratio:1;
}
function unprojectBeaconSlot(map,point){
  const transform=map.transform;
  if(transform?.elevation&&transform.screenPointToMercatorCoordinateAtZ)
    return transform.screenPointToMercatorCoordinateAtZ(point,-transform.elevation).toLngLat();
  return map.unproject([point.x,point.y]);
}

function sprite(documentObject,kind,spec){
  const canvas=documentObject.createElement('canvas');canvas.width=kind==='lamp'?40:kind==='number'?48:spec.width*2;canvas.height=kind==='lamp'?40:kind==='number'?40:spec.height*2;
  const ctx=canvas.getContext('2d');if(!ctx)throw Error('灯牌绘图不可用');
  if(kind==='lamp'){
    const glow=ctx.createRadialGradient(20,20,2,20,20,19);glow.addColorStop(0,'#fff4bd');glow.addColorStop(.35,'#ffce6fea');glow.addColorStop(1,'#ffb33900');
    ctx.fillStyle=glow;ctx.fillRect(0,0,40,40);ctx.beginPath();ctx.arc(20,20,6,0,Math.PI*2);ctx.fillStyle='#fff5cf';ctx.fill();
  }else if(kind==='number'){
    ctx.shadowColor='#ffc776bb';ctx.shadowBlur=3;ctx.fillStyle='#173e42f5';ctx.strokeStyle='#ffd58b';ctx.lineWidth=2;
    ctx.beginPath();ctx.roundRect(2,2,44,36,8);ctx.fill();ctx.stroke();
  }else{
    ctx.shadowColor='#ffc776bb';ctx.shadowBlur=6;ctx.fillStyle='#173e42f5';ctx.strokeStyle='#ffd58b';ctx.lineWidth=2;
    ctx.beginPath();ctx.roundRect(2,2,canvas.width-4,canvas.height-4,10);ctx.fill();ctx.stroke();
    ctx.shadowBlur=0;ctx.fillStyle='#ffe1a3';ctx.fillRect(12,canvas.height/2-12,3,24);
  }
  return ctx.getImageData(0,0,canvas.width,canvas.height);
}
function labelSize(name){
  const units=[...name].reduce((sum,c)=>sum+(/[\u0000-\u007f]/.test(c)?.55:1),0);
  const spec=NAME_SIGNS[units<=4?0:units<=7?1:units<=12?2:units<=24?3:4];
  return {width:spec.width,height:spec.height,sign:spec.id};
}

/** Sprite-based screen-facing light signs above the 3D map. The GeoJSON keeps
 * all delivered model records regardless of model fetch, LOD, distance or zoom.
 */
export function createBuildingBeacons({map,records,onSelect=()=>{},documentObject=document}){
  const ids=new Set(),byId=new Map();
  for(const row of records){
    if(!row.id||ids.has(row.id)||!Number.isFinite(row.lng)||!Number.isFinite(row.lat))throw Error('建筑灯牌目录无效');
    ids.add(row.id);byId.set(row.id,row);
  }
  let destroyed=false,timer=null,layout=[],revision=0;
  const listeners=[],clickEvents=new WeakSet(),sources=[LINES,ANCHORS,LABELS],layers=[`${LINES}-line`,`${ANCHORS}-symbol`,`${LABELS}-symbol`,`${LABELS}-numbers`];
  const feature=(row,index,compact=false,inViewport=true)=>({type:'Feature',id:row.id,properties:{id:row.id,name:row.name,label:compact?String(index+1):row.name,sign:labelSize(row.name).sign,compact,inViewport,districtId:row.districtId,order:index,number:index+1},geometry:{type:'Point',coordinates:[row.lng,row.lat]}});
  const anchorData=collection(records.map((r,i)=>feature(r,i)));
  map.addImage(LAMP,sprite(documentObject,'lamp'),{pixelRatio:2});
  for(const spec of NAME_SIGNS)map.addImage(spec.id,sprite(documentObject,'sign',spec),{pixelRatio:2});
  map.addImage(NUMBER,sprite(documentObject,'number'),{pixelRatio:2});
  map.addSource(LINES,{type:'geojson',data:collection([])});
  map.addSource(ANCHORS,{type:'geojson',data:anchorData});
  map.addSource(LABELS,{type:'geojson',data:anchorData});
  map.addLayer({id:layers[0],type:'line',source:LINES,minzoom:0,paint:{'line-color':'#9d6f2f','line-width':1,'line-opacity':.72}});
  const common={'icon-allow-overlap':true,'icon-ignore-placement':true,'icon-size':1,'icon-pitch-alignment':'viewport','icon-rotation-alignment':'viewport'};
  map.addLayer({id:layers[1],type:'symbol',source:ANCHORS,minzoom:0,layout:{...common,'icon-image':LAMP,'symbol-sort-key':['get','order']}});
  map.addLayer({id:layers[2],type:'symbol',source:LABELS,minzoom:0,filter:['all',['get','inViewport'],['!', ['get','compact']]],layout:{...common,'icon-image':['get','sign'],'icon-text-fit':'none','icon-offset':[0,0],
    'text-field':['get','label'],'text-font':['Noto Sans Regular'],'text-size':12,'text-max-width':12,'text-line-height':1.17,'text-offset':[0,0],
    'text-allow-overlap':true,'text-ignore-placement':true,'text-pitch-alignment':'viewport','text-rotation-alignment':'viewport','symbol-sort-key':['get','order']},
    paint:{'text-color':'#fff1cd','text-halo-color':'#173e42','text-halo-width':.5}});
  map.addLayer({id:layers[3],type:'symbol',source:LABELS,minzoom:0,filter:['all',['get','inViewport'],['get','compact']],layout:{...common,'icon-image':NUMBER,'icon-text-fit':'none',
    'text-field':['get','label'],'text-font':['Noto Sans Regular'],'text-size':12,'text-line-height':1,'text-offset':[0,0],'icon-offset':[0,0],
    'text-allow-overlap':true,'text-ignore-placement':true,'text-pitch-alignment':'viewport','text-rotation-alignment':'viewport','symbol-sort-key':['get','order']},
    paint:{'text-color':'#fff1cd','text-halo-color':'#173e42','text-halo-width':.5}});
  const legend=documentObject.createElement('div');legend.id='building-beacon-legend';legend.setAttribute('aria-label','已建模建筑灯牌');
  const count=documentObject.createElement('span');count.textContent=`✦ 已建模 ${records.length} 处 · ${new Set(records.map(r=>r.districtId)).size} 区`;
  const link=documentObject.createElement('a');link.href='landmarks.html';link.textContent='按区目录 ↗';link.setAttribute('aria-label','打开全部已建模建筑的按区目录');
  const note=documentObject.createElement('small');note.textContent='密集时显示编号，点选查看名称';
  legend.append(count,link,note);map.getContainer().appendChild(legend);
  const style=documentObject.createElement('style');style.textContent='#building-beacon-legend{position:absolute;z-index:3;top:92px;left:50%;transform:translateX(-50%);display:grid;grid-template-columns:auto auto;gap:2px 12px;align-items:center;max-width:calc(100% - 28px);padding:7px 12px;border:1px solid #e3bd76;border-radius:8px;background:#173e42eb;color:#fff1cd;font:11px/1.3 system-ui,sans-serif;white-space:nowrap;box-shadow:0 0 14px #eeb55826}#building-beacon-legend small{grid-column:1/-1;color:#d9d4c2;font-size:9px}#building-beacon-legend a{color:#ffe0a1;text-decoration:none;padding:4px}#building-beacon-legend a:focus-visible{outline:2px solid #fff1cd}@media(max-width:760px){#building-beacon-legend{top:126px;font-size:10px;padding:6px 9px;gap:1px 9px}}';map.getContainer().appendChild(style);
  function refresh(){
    if(destroyed)return;if(timer!==null){clearTimeout(timer);timer=null;}
    const canvas=map.getCanvas(),width=canvas.clientWidth||canvas.width,height=canvas.clientHeight||canvas.height;
    const onSurface=point=>!map.transform?.isPointOnMapSurface||map.transform.isPointOnMapSurface(point);
    const visible=records.map(r=>{const coordinate=[r.lng,r.lat],p=projectBeaconAnchor(map,coordinate);return {id:r.id,x:p.x,y:p.y,perspectiveScale:beaconPerspectiveScale(map,coordinate),...labelSize(r.name)};})
      .filter(p=>p.x>=0&&p.x<=width&&p.y>=0&&p.y<=height&&onSurface(p));
    const panel=documentObject.getElementById?.('explore-panel'),panelOpen=panel&&!panel.inert&&!panel.classList.contains('closed');
    const toolRect=documentObject.querySelector?.('.map-tools')?.getBoundingClientRect();
    const cardRect=documentObject.getElementById?.('location-card')?.getBoundingClientRect();
    const legendRect=legend.getBoundingClientRect();
    const insets={left:width>760&&panelOpen?Math.min(width*.48,(panel.getBoundingClientRect().right||320)+12):12,
      right:Math.max(width>760?88:64,toolRect?width-toolRect.left+8:0),
      top:Math.max(width>760?154:182,(legendRect.bottom||0)+8),
      bottom:Math.max(width>760?152:174,cardRect?height-cardRect.top+8:0)};
    layout=layoutBeaconLabels(visible,{width,height,insets});const offsets=new Map(layout.map(p=>[p.id,p]));
    // GeoJSON vector tiles stringify array properties. Keep pixel vectors in
    // literal style expressions so the actual symbol evaluator receives vec2.
    const expression=divisor=>layout.length?['match',['get','id'],...layout.flatMap(p=>[p.id,['literal',[(p.labelX-p.x)/divisor,(p.labelY-p.y)/divisor]]]),['literal',[0,0]]]:[0,0];
    const sizeExpression=size=>layout.some(p=>Math.abs(p.perspectiveScale-1)>1e-7)?['match',['get','id'],...layout.flatMap(p=>[p.id,size*p.perspectiveScale]),size]:size;
    for(const layer of layers.slice(1))map.setLayoutProperty(layer,'icon-size',sizeExpression(1));
    for(const layer of layers.slice(2))map.setLayoutProperty(layer,'text-size',sizeExpression(12));
    map.setLayoutProperty(layers[2],'text-offset',expression(12));
    map.setLayoutProperty(layers[2],'icon-offset',expression(1));
    map.setLayoutProperty(layers[3],'text-offset',expression(12));
    map.setLayoutProperty(layers[3],'icon-offset',expression(1));
    const labelData=[],leaders=[];
    records.forEach((row,index)=>{
      const point=offsets.get(row.id),slot=point?{x:point.labelX,y:point.labelY}:null;
      const coordinate=slot&&onSurface(slot)?unprojectBeaconSlot(map,slot):null;
      const target=coordinate?[coordinate.lng,coordinate.lat]:[row.lng,row.lat];
      // Keep label geometry at its real anchor. Pixel offsets work above the
      // ground-plane horizon, where unproject would jump behind the camera.
      labelData.push(feature(row,index,Boolean(point?.compact),Boolean(point)));
      leaders.push({type:'Feature',id:row.id,properties:{id:row.id},geometry:{type:'LineString',coordinates:[[row.lng,row.lat],target]}});
    });
    map.getSource(LABELS)?.setData(collection(labelData));map.getSource(LINES)?.setData(collection(leaders));revision++;map.triggerRepaint();
  }
  function schedule(){if(!destroyed&&timer===null)timer=setTimeout(refresh,80);}
  function hitTest(point){
    if(!point||!Number.isFinite(point.x)||!Number.isFinite(point.y))return null;
    const card=hitTestBeaconLabels(layout,point);if(card)return card;
    // The original lamp has no dynamic offset and retains its native hit box.
    const hit=map.queryRenderedFeatures(point,{layers:[layers[1]]})[0];
    const id=hit?.properties?.id??hit?.id;return byId.has(id)?id:null;
  }
  const click=event=>{if(event.originalEvent&&clickEvents.has(event.originalEvent))return;
    const row=byId.get(hitTest(event.point));
    if(row){if(event.originalEvent)clickEvents.add(event.originalEvent);event.originalEvent?.preventDefault?.();onSelect(row);}};
  // A displaced card takes precedence over an original lamp underneath it.
  map.on('click',click);listeners.push(['click',click]);
  const hover=event=>{map.getCanvas().style.cursor=hitTest(event.point)?'pointer':'';};
  const leave=()=>{map.getCanvas().style.cursor='';};
  map.on('mousemove',hover);listeners.push(['mousemove',hover]);
  map.on('mouseout',leave);listeners.push(['mouseout',leave]);
  for(const event of ['move','zoom','rotate','pitch']){map.on(event,schedule);listeners.push([event,schedule]);}
  for(const event of ['moveend','zoomend','resize']){map.on(event,refresh);listeners.push([event,refresh]);}
  refresh();
  return {refresh,hitTest,getState:()=>({count:records.length,ids:[...ids],districtCount:new Set(records.map(r=>r.districtId)).size,zoom:map.getZoom(),revision,
    labelPixelSize:12,anchorPixelSize:20,sourceIds:sources,layerIds:layers,spriteIds:[LAMP,...NAME_SIGNS.map(s=>s.id),NUMBER],viewportLabelCount:layout.length,
    labelMode:layout.some(p=>p.compact)?'numbers':'names',overlapFallbackCount:layout.filter(p=>p.overlapFallback).length,labelPositions:layout.map(p=>({id:p.id,number:records.findIndex(r=>r.id===p.id)+1,x:p.labelX,y:p.labelY,width:p.width,height:p.height,compact:p.compact}))}),
    destroy(){if(destroyed)return;destroyed=true;if(timer!==null)clearTimeout(timer);for(const args of listeners)map.off(...args);
      for(const id of [...layers].reverse())if(map.getLayer(id))map.removeLayer(id);for(const id of sources)if(map.getSource(id))map.removeSource(id);
      for(const id of [LAMP,...NAME_SIGNS.map(s=>s.id),NUMBER])if(map.hasImage(id))map.removeImage(id);legend.remove();style.remove();map.getCanvas().style.cursor='';}};
}
