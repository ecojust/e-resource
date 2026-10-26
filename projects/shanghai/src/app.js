import { createShanghaiScene } from './map-scene.js';
import { WalkController } from './walk-controller.js';
import { districtAt } from './geography.js';

const $ = id => document.getElementById(id);
const mobile = () => matchMedia('(max-width:760px)').matches;
const BUND = {id:'bund', name:'外滩历史建筑群', districtId:'310101', walkStart:[121.48582997998342,31.2404532310156], bearing:265.447};
let scene, controller, districts=[], landmarks=[], boundaries, activePlace=BUND;
let mode='overview', category='landmarks', activeDistrict='310101', toastTimer, navigation=0;
let districtPaths = new Map();
let panelOpen=!mobile();
const loadingProgress = value => $('loading-progress').style.width=`${value}%`;

function toast(message, duration=3300) {
  if(!message) return;
  $('toast').textContent=String(message); $('toast').classList.add('show');
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').classList.remove('show'),duration);
}
function togglePanel(force) {
  panelOpen=typeof force==='boolean'?force:!panelOpen;
  $('explore-panel').classList.toggle('closed',!panelOpen);
  document.body.classList.toggle('panel-collapsed',!panelOpen);
  $('explore-panel').inert=!panelOpen;
  $('panel-toggle').setAttribute('aria-expanded',String(panelOpen));
}
function updateLocation(place) {
  const district=districts.find(d=>d.id===(place.districtId||place.id));
  $('location-name').textContent=place.name;
  $('location-district').textContent=(district?.name||'上海市')+(place.height_m?' · 城市地标':' · 城市探索');
  $('start-walk').innerHTML=mode==='walk'?'正在漫游 <span>↗</span>':'进入漫游 <span>↗</span>';
  activeDistrict=district?.id||activeDistrict;
  $('reference-button').hidden=!place.reference;
  districtPaths.forEach((p,id)=>p.classList.toggle('active',id===activeDistrict));
  renderPlaces();
}
function syncMode(next, announce=true) {
  mode=next;
  if(location.hash){const hash=new URLSearchParams(location.hash.slice(1));hash.set('mode',next);history.replaceState(null,'',`#${hash}`);}
  if(scene?.map.setVerticalFieldOfView)scene.map.setVerticalFieldOfView(next==='walk'?64:36.87);
  controller?.setMode(next);
  scene?.setDistrictVisibility(next==='overview');
  document.body.classList.toggle('walking',next==='walk');
  $('walk-mode').classList.toggle('active',next==='walk');
  $('overview-mode').classList.toggle('active',next==='overview');
  $('walk-mode').setAttribute('aria-pressed',String(next==='walk'));
  $('overview-mode').setAttribute('aria-pressed',String(next==='overview'));
  $('mode-label').textContent=next==='walk'?'第三人称漫游':'城市俯瞰';
  $('hint-text').textContent=next==='walk'
    ?(mobile()?'左侧摇杆行走 · 拖动场景转向':'WASD 行走 · Shift 加速 · 拖动转向 · 滚轮远近')
    :'拖动平移 · 滚轮缩放 · 双击地图选择漫游起点';
  $('mobile-controls').hidden=!(next==='walk'&&(mobile()||matchMedia('(pointer:coarse)').matches));
  updateLocation(activePlace);
  if(next==='walk') {
    togglePanel(false);
    if(announce) toast(mobile()?'已进入第三人称漫游，拖动左侧摇杆行走':'已进入第三人称漫游，使用 WASD 或方向键行走');
  }
}
function showOverview(place=activePlace) {
  if(!scene) return;
  syncMode('overview',false);
  const center=place.lng?[place.lng,place.lat]:(place.walkStart||place.center);
  scene.map.flyTo({center,zoom:place.overviewZoom??(place.custom?16.4:place.id==='bund'?17.3:place.height_m?16.4:14.8),pitch:60,bearing:place.bearing??35,duration:1000,essential:true});
}
async function selectPlace(place) {
  if(!controller) return;
  const ticket=++navigation;
  activePlace=place;
  updateLocation(place);
  const [lng,lat]=place.walkStart||place.center||[place.lng,place.lat];
  controller.teleport({lng,lat,bearing:place.bearing??45});
  if(mode==='overview') showOverview(place);
  if(mobile()) togglePanel(false);
  const hash=place.custom?`lng=${lng.toFixed(6)}&lat=${lat.toFixed(6)}`:`${place.height_m?'landmark':'district'}=${encodeURIComponent(place.id)}`;
  history.replaceState(null,'',`#${hash}&mode=${mode}`);
  $('live-status').textContent='加载当前区域';
  try {
    await scene.waitForData(10000);
    if(ticket===navigation) $('live-status').textContent='全域地图已连接';
  } catch { if(ticket===navigation) toast('当前区域的地图仍在加载，请稍候。'); }
}
function mapPlace(lng,lat) {
  const district=districtAt(boundaries,lng,lat);
  if(!district)return null;
  return {id:'selected-location',name:'自选街区',districtId:String(district.id),walkStart:[lng,lat],bearing:scene.map.getBearing(),custom:true};
}
function renderPlaces() {
  const query=$('place-search').value.trim().toLowerCase();
  const list=$('place-list'); list.replaceChildren();
  const items=(query?[...districts,...landmarks]:category==='districts'?districts:landmarks)
    .filter(p=>p.name.toLowerCase().includes(query));
  list.classList.toggle('districts',category==='districts'&&!query);
  if(!items.length) {const empty=document.createElement('div');empty.className='empty-list';empty.textContent='没有找到匹配的区域或地标';list.append(empty);return;}
  items.forEach((p,index)=>{
    const button=document.createElement('button');button.type='button';
    button.className=`place-button${p.height_m?' landmark-item':''}${(p.id===activePlace.id||(!p.height_m&&p.id===activeDistrict))?' selected':''}`;
    button.dataset.place=p.id;
    button.setAttribute('aria-label',`前往${p.name}`);
    const icon=document.createElement('span');icon.className=p.height_m?'landmark-icon':'place-number';icon.textContent=p.height_m?'▥':String(districts.findIndex(d=>d.id===p.id)+1).padStart(2,'0');
    const words=document.createElement('span');
    const label=document.createElement('span');label.className='place-name';label.textContent=p.name;words.append(label);
    if(p.height_m){const small=document.createElement('small');small.className='landmark-description';small.textContent=p.bund_number?`外滩 ${p.bund_number} 号 · ${p.architecture_style||'历史建筑'}`:`${p.height_m} m · 陆家嘴`;words.append(small);}
    const arrow=document.createElement('span');arrow.className='place-arrow';arrow.textContent='↗';
    button.append(icon,words,arrow);button.addEventListener('click',()=>selectPlace(p));list.append(button);
  });
}
function setCategory(value){
  category=value;
  for(const [id,cat] of [['district-tab','districts'],['landmark-tab','landmarks']]){
    $(id).classList.toggle('active',cat===value);$(id).setAttribute('aria-selected',String(cat===value));
  }
  renderPlaces();
}

function miniProject(lng,lat) {
  const bounds=[120.8,30.6,122.25,31.95];
  const sx=Math.cos(31.2*Math.PI/180), width=(bounds[2]-bounds[0])*sx,height=bounds[3]-bounds[1];
  const scale=Math.min(250/width,128/height),ox=(270-width*scale)/2,oy=(140-height*scale)/2;
  return [ox+(lng-bounds[0])*sx*scale,oy+(bounds[3]-lat)*scale];
}
function drawMiniMap() {
  const svg=$('district-map');svg.replaceChildren();
  for(const feature of boundaries.features){
    const polygons=feature.geometry.type==='Polygon'?[feature.geometry.coordinates]:feature.geometry.coordinates;
    let d='';
    for(const polygon of polygons) for(const ring of polygon){
      // Keep local outline readable without duplicating the high-resolution map.
      const simplified=ring.filter((_,i)=>i%3===0||i===ring.length-1);
      d+=simplified.map((p,i)=>{const[x,y]=miniProject(...p);return`${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`;}).join('')+'Z';
    }
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('d',d);path.setAttribute('class','district-shape');path.setAttribute('fill-rule','evenodd');
    const id=String(feature.properties.id||feature.properties.adcode);path.dataset.district=id;
    const title=document.createElementNS('http://www.w3.org/2000/svg','title');title.textContent=feature.properties.name;path.append(title);
    path.addEventListener('click',()=>{const item=districts.find(d=>d.id===id);if(item)selectPlace(item);});
    svg.append(path);districtPaths.set(id,path);
  }
  const point=document.createElementNS('http://www.w3.org/2000/svg','circle');point.id='mini-player';point.setAttribute('r','2.6');point.setAttribute('class','mini-position');svg.append(point);
}
function updateHud(state) {
  $('coordinate-readout').textContent=`${state.lat.toFixed(5)}° N · ${state.lng.toFixed(5)}° E`;
  $('distance-readout').textContent=Math.round(state.distance).toLocaleString('zh-CN');
  const point=$('mini-player');if(point){const[x,y]=miniProject(state.lng,state.lat);point.setAttribute('cx',x);point.setAttribute('cy',y);}
  $('compass-needle').style.transform=`rotate(${-(scene?.map.getBearing()||0)}deg)`;
}
function installUi() {
  $('panel-toggle').addEventListener('click',()=>togglePanel());
  const showInfo=()=>{
    const reference=activePlace.reference;
    $('building-reference').hidden=!reference;
    if(reference){
      $('reference-title').textContent=activePlace.name;
      $('reference-image').src=reference.image;
      $('reference-image').alt=`${activePlace.name}实景参考照片`;
      $('reference-credit').textContent=`${reference.author} · ${reference.license}`;
      $('reference-source').href=reference.source;
      $('reference-note').textContent=activePlace.detail_note||'按照片重建立面结构；缺少测绘资料的尺寸和侧后立面仍有推定。';
    }
    controller?.setEnabled(false);$('info-dialog').showModal();
  };
  $('info-button').addEventListener('click',showInfo);
  $('reference-button').addEventListener('click',showInfo);
  $('bund-start').addEventListener('click',()=>{setCategory('landmarks');selectPlace(BUND);syncMode('walk',false);});
  $('info-dialog').addEventListener('close',()=>controller?.setEnabled(true));
  $('info-dialog').addEventListener('click',e=>{if(e.target===$('info-dialog'))$('info-dialog').close();});
  $('district-tab').addEventListener('click',()=>setCategory('districts'));
  $('landmark-tab').addEventListener('click',()=>setCategory('landmarks'));
  $('place-search').addEventListener('input',renderPlaces);
  $('overview-mode').addEventListener('click',()=>showOverview());
  $('walk-mode').addEventListener('click',()=>syncMode('walk'));
  $('start-walk').addEventListener('click',()=>{if(mode!=='walk')syncMode('walk');else controller?.resetCamera();});
  $('reset-place').addEventListener('click',()=>selectPlace(activePlace));
  $('compass').addEventListener('click',()=>{if(mode==='walk')controller?.resetCamera();else scene?.map.easeTo({bearing:0,pitch:45,duration:600});});
  $('zoom-in').addEventListener('click',()=>{if(mode==='walk')controller?._wheel({deltaY:-160,preventDefault(){}});else scene?.map.zoomIn({duration:300});});
  $('zoom-out').addEventListener('click',()=>{if(mode==='walk')controller?._wheel({deltaY:160,preventDefault(){}});else scene?.map.zoomOut({duration:300});});
  $('fit-city').addEventListener('click',()=>{
    syncMode('overview',false);
    scene?.map.fitBounds([[120.85,30.65],[122.05,31.90]],{padding:mobile()?60:{left:360,right:90,top:120,bottom:100},bearing:0,pitch:0,duration:1400});
    toast('上海全市 16 个区，选择区域即可继续探索');
  });
  document.addEventListener('keydown',e=>{if(e.key==='/'&&!/INPUT|TEXTAREA/.test(e.target.tagName)){e.preventDefault();togglePanel(true);$('place-search').focus();}});
  window.addEventListener('resize',()=>{$('mobile-controls').hidden=!(mode==='walk'&&(mobile()||matchMedia('(pointer:coarse)').matches));});
  const stick=$('joystick'),knob=$('joystick-knob');let pointer=null;
  const moveStick=e=>{if(e.pointerId!==pointer)return;const r=stick.getBoundingClientRect();let x=(e.clientX-r.left-r.width/2)/32,y=(e.clientY-r.top-r.height/2)/32;const len=Math.hypot(x,y);if(len>1){x/=len;y/=len;}knob.style.transform=`translate(${x*27}px,${y*27}px)`;controller?.setMoveVector(x,-y);};
  stick.addEventListener('pointerdown',e=>{e.preventDefault();pointer=e.pointerId;stick.setPointerCapture(pointer);moveStick(e);});
  stick.addEventListener('pointermove',moveStick);
  const stopStick=()=>{pointer=null;knob.style.transform='';controller?.setMoveVector(0,0);};
  stick.addEventListener('pointerup',stopStick);stick.addEventListener('pointercancel',stopStick);
  const run=$('touch-run');run.addEventListener('pointerdown',e=>{run.setPointerCapture(e.pointerId);run.classList.add('active');controller?.setRun(true);});
  for(const event of ['pointerup','pointercancel','lostpointercapture'])run.addEventListener(event,()=>{run.classList.remove('active');controller?.setRun(false);});
  $('retry-button').addEventListener('click',()=>location.reload());
  togglePanel(panelOpen);
}

async function main(){
  if(location.protocol==='file:') return;
  installUi();loadingProgress(18);
  const startWalking=!location.hash || new URLSearchParams(location.hash.slice(1)).get('mode')==='walk';
  try{
    const responses=await Promise.all(['data/districts.json','data/districts-display.geojson','data/landmarks.json','data/scene-props.json','data/precise-buildings-v6.json'].map(name=>fetch(new URL(`../${name}`,import.meta.url)).then(r=>{if(!r.ok)throw new Error(`无法读取 ${name}`);return r.json();})));
    districts=responses[0].districts.map(d=>({...d,id:String(d.id)}));boundaries=responses[1];landmarks=responses[2];
    $('landmark-count').textContent=landmarks.length;setCategory('landmarks');drawMiniMap();updateLocation(BUND);loadingProgress(35);
    scene=await createShanghaiScene({container:$('map'),start:{lng:BUND.walkStart[0],lat:BUND.walkStart[1],bearing:BUND.bearing},zoom:startWalking?20.0:17.3,landmarks:[...landmarks,...responses[3]],preciseBuildingOverrides:responses[4],
      onStatus:status=>{
        if(status.message)$('loading-message').textContent=status.message;
        if(status.kind==='streaming')$('live-status').textContent=status.loading?'加载附近建筑':status.visible?'附近建筑已加载':'全域地图已连接';
        else if(status.kind==='models')$('live-status').textContent=status.loaded<status.total?'建筑模型加载中':'建筑模型已加载';
        else if(status.message)$('live-status').textContent='全域地图已连接';
      },
      onLoadError:error=>{console.warn('[Shanghai map]',error);$('live-status').textContent='地图连接稍慢';}});
    scene.map.dragRotate.enable();scene.setDistricts(boundaries);scene.setDistrictVisibility(true);
    scene.map.doubleClickZoom.disable();
    scene.map.on('dblclick',event=>{
      if(mode!=='overview')return;
      event.preventDefault();
      const place=mapPlace(event.lngLat.lng,event.lngLat.lat);
      if(place){selectPlace(place);toast('已选择街区，点击“进入漫游”出发。');}
      else toast('请在上海行政区范围内选择起点。');
    });
    const cityState=await scene.setCityManifest('assets/city-detail/manifest.json');
    if(cityState.fallback)await scene.setCityManifest('assets/city/manifest.json');
    controller=new WalkController(scene,{container:scene.map.getCanvas(),onUpdate:updateHud,onNotice:toast});
    controller.setMode('overview');controller.setEnabled(true);controller.teleport({lng:BUND.walkStart[0],lat:BUND.walkStart[1],bearing:BUND.bearing});
    if(startWalking)syncMode('walk',false);
    else scene.map.jumpTo({center:[121.48552,31.23845],zoom:17.3,pitch:60,bearing:285});
    loadingProgress(78);$('loading-message').textContent='正在铺开道路、建筑与城市地标…';
    const tilesReady=await scene.waitForData(16000);loadingProgress(100);
    if(!tilesReady)toast('部分地图数据仍在加载，请保持网络连接。',5000);
    $('live-status').textContent='全域地图已连接';$('loading').classList.add('loaded');
    scene.map.on('rotate',()=>$('compass-needle').style.transform=`rotate(${-scene.map.getBearing()}deg)`);
    window.__SHANGHAI_APP__={scene,controller,districts,landmarks,get mode(){return mode;},selectPlace,syncMode};
    const hash=new URLSearchParams(location.hash.slice(1));
    const destination=districts.find(d=>d.id===hash.get('district'))||landmarks.find(p=>p.id===hash.get('landmark'))
      ||(hash.has('lng')&&hash.has('lat')?mapPlace(Number(hash.get('lng')),Number(hash.get('lat'))):null);
    if(destination)await selectPlace(destination);
    if(hash.get('mode')==='walk' || !location.hash)syncMode('walk',false);
  }catch(error){
    console.error(error);$('loading-message').textContent=`场景暂时未能加载：${error.message}`;$('retry-button').hidden=false;
    $('live-status').textContent='连接需要重试';loadingProgress(0);
  }
}
main();
