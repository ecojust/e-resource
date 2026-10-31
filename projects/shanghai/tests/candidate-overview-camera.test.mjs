import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {candidateOverviewCamera,OVERVIEW_CAMERA_RESET} from '../src/candidate-overview-camera.js';
import {WalkController} from '../src/walk-controller.js';

const candidates=JSON.parse(readFileSync(new URL('../data/candidate-city-integrations.json',import.meta.url),'utf8')).models.map(row=>({...row,city_integration:true}));
const legacy=JSON.parse(readFileSync(new URL('../data/landmarks.json',import.meta.url),'utf8'));
const context={module:{exports:{}},console,URL,Blob,TextDecoder,TextEncoder,setTimeout,clearTimeout,performance};
context.exports=context.module.exports;context.self=context;context.globalThis=context;
vm.runInNewContext(readFileSync(new URL('../vendor/maplibre-gl.js',import.meta.url),'utf8'),context);
const maplibre=context.module.exports;

function actualTransform(camera,{width,height}){
  // Obtain the shipped Mercator transform through Style's projection factory;
  // none of the perspective, padding or coordinate projection is mocked.
  let transform;
  const style=Object.create(maplibre.Style.prototype);
  style.map={migrateProjection(next){transform=next;}};style.tileManagers={};
  style._setProjectionInternal('mercator');
  transform.resize(width,height);transform.setFov(36.87);
  // At zoom zero the real transform constrains the target to the world extent.
  transform.setZoom(camera.zoom);transform.setCenter(maplibre.LngLat.convert(camera.center));
  transform.setElevation(camera.elevation);transform.setPadding(camera.padding);
  transform.setPitch(camera.pitch);transform.setBearing(camera.bearing);
  return transform;
}

function worldCorners(place){
  const anchor=maplibre.MercatorCoordinate.fromLngLat([place.lng,place.lat],place.altitude||0);
  const unit=anchor.meterInMercatorCoordinateUnits(),scale=place.scale||1;
  const angle=(place.heading||0)*Math.PI/180,c=Math.cos(angle),s=Math.sin(angle),corners=[];
  for(const x of [place.bounds_glb.min[0],place.bounds_glb.max[0]])
    for(const y of [place.bounds_glb.min[1],place.bounds_glb.max[1]])
      for(const z of [place.bounds_glb.min[2],place.bounds_glb.max[2]]){
        // Match the global GLB matrix: Y up, Z south, rotationY=-heading.
        const east=(c*x-s*z)*scale,south=(s*x+c*z)*scale;
        corners.push(new maplibre.MercatorCoordinate(anchor.x+east*unit,anchor.y+south*unit,anchor.z+y*scale*unit));
      }
  return corners;
}

const viewports=[
  {width:1200,height:800,insets:{left:376,right:88,top:154,bottom:152}},
  {width:390,height:844,insets:{left:16,right:65,top:182,bottom:190}},
  {width:320,height:568,insets:{left:16,right:65,top:182,bottom:190}},
];

for(const viewport of viewports)test(`${viewport.width} by ${viewport.height}: all delivered candidate bounds fit the real MapLibre camera outside the interface`,()=>{
  assert(candidates.length>=30);
  for(const place of candidates){
    const camera=candidateOverviewCamera(place,viewport);assert(camera,place.id);
    assert(camera.zoom>=8&&camera.zoom<=24);assert(Number.isFinite(camera.elevation));
    assert.deepEqual(camera.padding,viewport.insets);
    const transform=actualTransform(camera,viewport),corners=worldCorners(place);
    assert.equal(corners.length,8);
    for(const corner of corners){
      const pixel=transform.coordinatePoint(corner,corner.toAltitude(),transform._pixelMatrix3D);
      assert(Number.isFinite(pixel.x)&&Number.isFinite(pixel.y),`${place.id}: finite projection`);
      const {left,right,top,bottom}=viewport.insets,tolerance=.5;
      assert(pixel.x>=left-tolerance&&pixel.x<=viewport.width-right+tolerance,`${place.id}: x ${pixel.x} outside ${left}..${viewport.width-right}`);
      assert(pixel.y>=top-tolerance&&pixel.y<=viewport.height-bottom+tolerance,`${place.id}: y ${pixel.y} outside ${top}..${viewport.height-bottom}`);
    }
  }
});

test('candidate camera uses the verified approach bearing and the low Lu Xun view',()=>{
  const fixture={...candidates[0],bearing:231,navigation:{bearing:17}};
  assert.equal(candidateOverviewCamera(fixture,viewports[0]).bearing,17);
  assert.equal(candidateOverviewCamera({...fixture,overviewBearing:49},viewports[0]).bearing,49);
  assert.equal(candidateOverviewCamera({...fixture,navigation:undefined},viewports[0]).bearing,231);
  assert.equal(candidateOverviewCamera({...fixture,navigation:undefined,bearing:undefined},viewports[0]).bearing,35);
  const luxun=candidates.find(row=>row.id==='hongkou-luxun-residence-facade');assert(luxun);
  assert.equal(candidateOverviewCamera(luxun,viewports[0]).pitch,16);
  assert.equal(candidateOverviewCamera({...luxun,overviewPitch:22},viewports[0]).pitch,22);
});

test('all forty legacy entries preserve their established overview route',()=>{
  assert.equal(legacy.length,40);
  for(const place of legacy)assert.equal(candidateOverviewCamera(place,viewports[0]),null,place.id);
  assert.equal(candidateOverviewCamera({...candidates[0],bounds_glb:undefined},viewports[0]),null);
});

test('leaving a candidate overview clears the real vendor padding and elevation',()=>{
  const viewport=viewports[2],camera=candidateOverviewCamera(candidates[0],viewport);
  const transform=actualTransform({...camera,elevation:18},viewport);
  const center=()=>[transform.centerPoint.x,transform.centerPoint.y];
  const asymmetricCenter=center();
  assert.notDeepEqual(asymmetricCenter,[viewport.width/2,viewport.height/2]);
  assert.equal(transform.elevation,18);
  // Regression control: MapLibre accepts this value but retains every inset.
  transform.setPadding(0);
  assert.deepEqual(center(),asymmetricCenter);
  assert.deepEqual({...transform.padding},camera.padding);
  transform.setPadding(OVERVIEW_CAMERA_RESET.padding);
  transform.setElevation(OVERVIEW_CAMERA_RESET.elevation);
  assert.deepEqual(center(),[viewport.width/2,viewport.height/2]);
  assert.equal(transform.elevation,0);
  assert.deepEqual({...transform.padding},{top:0,bottom:0,left:0,right:0});
});

test('walk, legacy overview and city overview each apply the complete camera reset',()=>{
  const app=readFileSync(new URL('../src/app.js',import.meta.url),'utf8');
  assert.equal([...app.matchAll(/\.jumpTo\(OVERVIEW_CAMERA_RESET\)/g)].length,3);
  assert(!/padding\s*:\s*0\b/.test(app),'numeric padding silently retains the candidate framing');
});

test('production overview navigation preserves candidate height through rendering and restores legacy ground clamping',()=>{
  const viewport=viewports[2],place=candidates.find(row=>row.id==='chongming-stele-corridors');
  const camera=candidateOverviewCamera(place,viewport),transform=actualTransform(camera,viewport),calls=[];
  let clamped=true;
  const map={
    getCanvas:()=>({clientWidth:viewport.width,clientHeight:viewport.height}),
    setCenterClampedToGround(value){clamped=value;calls.push(['clamp',value]);},
    setCenterElevation(value){transform.setElevation(value);calls.push(['elevation',value]);},
    setVerticalFieldOfView(value){transform.setFov(value);},triggerRepaint(){},
    jumpTo(options){
      calls.push(['jump',options]);
      if(options.zoom!==undefined)transform.setZoom(options.zoom);
      if(options.center)transform.setCenter(maplibre.LngLat.convert(options.center));
      if(options.elevation!==undefined)transform.setElevation(options.elevation);
      if(options.padding!==undefined)transform.setPadding(options.padding);
      if(options.pitch!==undefined)transform.setPitch(options.pitch);
      if(options.bearing!==undefined)transform.setBearing(options.bearing);
    },
    flyTo(options){calls.push(['fly',options]);this.jumpTo(options);},
  };
  // Model the next MapLibre render's ground update; all matrix/elevation state
  // still belongs to the actual vendored transform, not a camera arithmetic mock.
  const render=()=>{if(clamped)transform.setElevation(0);};
  map.jumpTo(camera);assert(camera.elevation>0);render();
  assert.equal(transform.elevation,0,'control: an otherwise correct fit loses its height while ground clamping is enabled');
  calls.length=0;
  const scene={map,setDistrictVisibility(){},refreshBuildingBeacons(){calls.push(['beacons']);}};
  const sceneSource=readFileSync(new URL('../src/map-scene.js',import.meta.url),'utf8');
  const avatarSource=sceneSource.slice(sceneSource.indexOf('    setAvatarVisible(visible){'),sceneSource.indexOf('    // Manual refresh still respects geographic range;'));
  scene.setAvatarVisible=new Function('map','setWalkModeLabels','walker','updateStreetBasemap','updateLocalModels',
    `let explicitCamera=null;return ({${avatarSource}}).setAvatarVisible;`)(map,()=>{},{group:{visible:true}},()=>{},()=>{});
  // Use the production controller method, including its same-mode early return.
  const controller=Object.assign(Object.create(WalkController.prototype),{scene,mode:'walk',enabled:false,position:{lng:place.lng,lat:place.lat},
    _clearInput(){},_applyMapInteraction(){},_emitUpdate(){}});
  const rects={'explore-panel':{right:300},'location-card':{top:viewport.height-182},'building-beacon-legend':{bottom:174}};
  const element=id=>({classList:{toggle(){}},setAttribute(){},getBoundingClientRect:()=>rects[id]||{}});
  const document={body:{classList:{toggle(){}}},querySelector:()=>({getBoundingClientRect:()=>({left:viewport.width-57})})};
  const app=readFileSync(new URL('../src/app.js',import.meta.url),'utf8');
  const navigationSource=app.slice(app.indexOf('function syncMode('),app.indexOf('async function selectPlace('));
  const navigate=new Function('scene','controller','$','document','mobile','candidateOverviewCamera','OVERVIEW_CAMERA_RESET',
    `let mode='walk',activePlace,panelOpen=false;const location={hash:''},history={},walkingPose=()=>null,updateLocation=()=>{},togglePanel=()=>{},toast=()=>{};
    ${navigationSource}
    return place=>{activePlace=place;showOverview(place);};`)(scene,controller,element,document,()=>true,candidateOverviewCamera,OVERVIEW_CAMERA_RESET);
  for(const candidate of [place,candidates.find(row=>row.id==='chongming-pan-pool-bridge')]){
    calls.length=0;navigate(candidate);
    const jumpIndex=calls.findIndex(([name,options])=>name==='jump'&&options.elevation>0);
    assert(jumpIndex>0);assert.deepEqual(calls[jumpIndex-1],['clamp',false],'disable clamping before installing the elevated candidate camera');
    const elevation=transform.elevation;assert(elevation>0);render();render();
    assert.equal(transform.elevation,elevation,'rendering must retain the fitted half-height target');
    assert.equal(controller.mode,'overview');assert.equal(clamped,false);
  }
  calls.length=0;navigate(legacy[0]);
  assert.equal(controller.mode,'overview');assert.equal(clamped,true,'candidate-to-legacy overview must restore clamping even when controller mode is already overview');
  render();assert.equal(transform.elevation,0);
  assert.deepEqual({...transform.padding},{top:0,bottom:0,left:0,right:0});
  assert.deepEqual([transform.centerPoint.x,transform.centerPoint.y],[viewport.width/2,viewport.height/2]);
  assert(calls.some(([name])=>name==='fly'),'legacy route still uses its established fly camera');
});
