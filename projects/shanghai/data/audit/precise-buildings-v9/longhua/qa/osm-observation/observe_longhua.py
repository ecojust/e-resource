#!/usr/bin/env python3
"""Root-only, one-browser actual MVT observation. No model or identity acceptance."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
import argparse,hashlib,json,math,os,time
from shapely.geometry import shape
from shapely.ops import transform
HERE=Path(__file__).resolve().parent
DEFAULT_GEOMETRY=HERE.parent/'longhua-integration/inputs/xuhui-longhua-pagoda/geometry-input.json'
PIN='4f9a76d03074049132d50a856bdb892e7f8e76bc3e9172e57dff7d3bacb5e47a'
def meta(p):
 b=p.read_bytes();return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def proxy():
 name=next((k for k in ('HTTPS_PROXY','HTTP_PROXY') if os.environ.get(k)),None)
 if not name:raise ValueError('Requested proxy environment is absent')
 u=urlsplit(os.environ[name]);assert u.scheme in ('http','https') and u.hostname and u.path in ('','/') and not u.query and not u.fragment
 host=('['+u.hostname+']') if ':' in u.hostname else u.hostname
 value={'server':u.scheme+'://'+host+(':'+str(u.port) if u.port else ''),'bypass':'localhost,127.0.0.1'}
 if u.username:value['username']=unquote(u.username)
 if u.password:value['password']=unquote(u.password)
 return value,{'source_environment':name,'host':u.hostname,'port':u.port,'bypass':value['bypass'],'credentials_supplied':bool(u.username or u.password)}
PROBE=r'''async()=>{
 const app=window.__SHANGHAI_APP__,map=app.scene.map;
 const {OSMBuildingSuppressor}=await import(new URL('src/osm-building-suppression.js',document.baseURI));
 const original=OSMBuildingSuppressor.prototype.getState;let source;
 try {OSMBuildingSuppressor.prototype.getState=function(...args){source=this;return original.apply(this,args)};app.scene.getRealismState();}
 finally {OSMBuildingSuppressor.prototype.getState=original;}
 if(!source)throw Error('Actual source suppressor is unavailable');
 const events=[];const error=e=>events.push({sourceId:e.sourceId,message:String(e.error?.message||e.message||e.error||'')});map.on('error',error);
 const summary=()=>({source:source.source,sourceLayer:source.sourceLayer,sourceLoaded:Boolean(map.getSource(source.source))&&map.isSourceLoaded(source.source),
   osm:app.scene.getRealismState().osmFallback,camera:{center:map.getCenter().toArray(),zoom:map.getZoom(),pitch:map.getPitch(),bearing:map.getBearing()},errors:events.slice()});
 const detail=()=>({...summary(),features:map.querySourceFeatures(source.source,{sourceLayer:source.sourceLayer}).map(f=>({type:'Feature',id:f.id,properties:{...f.properties},geometry:JSON.parse(JSON.stringify(f.geometry)),actualState:f.id==null?null:map.getFeatureState({source:source.source,sourceLayer:source.sourceLayer,id:f.id})}))});
 window.__LONGHUA_SOURCE__={summary,detail,cleanup(){map.off('error',error)}};
 return {source:source.source,sourceLayer:source.sourceLayer,prototypes_restored:OSMBuildingSuppressor.prototype.getState===original,feature_states_not_modified:true};
}'''
def analyze(snapshot,g,out):
 target=shape(g['geometry']);R=6378137.;cx,cy=g['anchor'];scale=math.cos(math.radians(cy));mx=R*math.radians(cx);my=R*math.log(math.tan(math.pi/4+math.radians(cy)/2))
 def project(x,y):return ((R*math.radians(x)-mx)*scale,(R*math.log(math.tan(math.pi/4+math.radians(y)/2))-my)*scale)
 tp=transform(project,target);matches=[];matched_groups=[];nearby=[]
 neighbors=g['current_city_detail']['same_near_neighbors_to_retain']
 for fi,f in enumerate(snapshot['features']):
  ge=f['geometry'];components=[ge['coordinates']] if ge['type']=='Polygon' else ge['coordinates'] if ge['type']=='MultiPolygon' else []
  hit=False
  for ci,coords in enumerate(components):
   component={'type':'Polygon','coordinates':coords};s=shape(component)
   if not s.is_valid:continue
   intersects=s.intersects(target)
   if not intersects and s.distance(target)>.001:continue
   p=transform(project,s);area=p.intersection(tp).area
   if area>0:
    hit=True;matches.append({'feature_snapshot_index':fi,'source_id':f.get('id'),'component_original_index':ci,'component_area_m2':p.area,'intersection_area_m2':area,'target_fraction':area/tp.area,'component_fraction':area/p.area if p.area else None,'iou':area/p.union(tp).area,'properties':f['properties'],'actual_state':f['actualState'],'geometry':component})
   if intersects or p.distance(tp)<=25:
    relationships=[{'local_id':n['local_id'],'key':n['key'],'intersection_area_m2':p.intersection(transform(project,shape(n['geometry']))).area} for n in neighbors if s.intersects(shape(n['geometry']))]
    nearby.append({'feature_snapshot_index':fi,'source_id':f.get('id'),'component_original_index':ci,'target_intersection_area_m2':area,'target_distance_m':p.distance(tp),'preserved_neighbor_intersections':relationships,'geometry':component,'properties':f['properties']})
  if hit:matched_groups.append(f)
 write(out/'matching-aggregate-features.geojson',{'type':'FeatureCollection','features':matched_groups})
 report={'schema':'longhua-actual-mvt-component-observation-v1','observation_only':True,'model_accepted':False,'fixture_approved':False,'frozen_source_geometry':meta(DEFAULT_GEOMETRY),'source_id':snapshot['source'],'source_layer':snapshot['sourceLayer'],'source_loaded':snapshot['sourceLoaded'],'source_features':len(snapshot['features']),'target_area_m2':tp.area,'matches':matches,'nearby_components':nearby,'all_original_matching_aggregate_components_retained':True,'scope':'Actual MapLibre querySourceFeatures from current MAIN at Longhua. Exact positive polygon intersection, not aggregate bbox. No clipping, buffering, state changes, model replacement or identity acceptance.'}
 write(out/'component-matches.json',report)
 return {'positive_component_matches':len(matches),'matching_aggregate_features':len(matched_groups),'largest_matches':[{k:m[k] for k in ('source_id','component_original_index','iou','target_fraction','component_fraction')} for m in sorted(matches,key=lambda m:m['intersection_area_m2'],reverse=True)[:5]],'fixture_approved':False}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--url',required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--timeout-ms',type=int,default=240000);ap.add_argument('--use-env-proxy',action='store_true');a=ap.parse_args()
 assert not a.output.exists(),'Use a new output directory';assert meta(DEFAULT_GEOMETRY)['sha256']==PIN
 g=json.loads(DEFAULT_GEOMETRY.read_bytes());a.output.mkdir(parents=True);report={'schema':'longhua-actual-osm-observation-run-v1','completed':False,'model_accepted':False,'browser_model_test':False,'source_geometry':meta(DEFAULT_GEOMETRY),'script':meta(Path(__file__)),'url':a.url,'events':[],'page_errors':[],'requests_failed':[],'blocked':[],'runtime_or_disk_modified':False}
 def save():write(a.output/'observation.json',report)
 def log(name,**detail):report['events'].append({'at':time.time(),'stage':name,**detail});print(name,flush=True);save()
 from playwright.sync_api import sync_playwright
 browser=None;page=None
 try:
  with sync_playwright() as pw:
   opts={'viewport':{'width':1040,'height':760},'device_scale_factor':1}
   if a.use_env_proxy:opts['proxy'],report['network']=proxy()
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
   context=browser.new_context(**opts);page=context.new_page();page.set_default_timeout(a.timeout_ms)
   page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
   page.on('requestfailed',lambda r:report['requests_failed'].append({'url':r.url,'failure':r.failure}))
   cdp=context.new_cdp_session(page);cdp.send('Network.enable');patterns=['https://tiles.overturemaps.org/*','https://stac.overturemaps.org/*'];cdp.send('Network.setBlockedURLs',{'urls':patterns})
   cdp.on('Network.loadingFailed',lambda e:report['blocked'].append(e) if e.get('blockedReason') else None)
   report['outage_injection']={'method':'Chromium Network.setBlockedURLs','patterns':patterns,'playwright_routes_installed':False,'cache_disabled':False}
   log('navigate');page.goto(a.url,wait_until='domcontentloaded');page.wait_for_function('()=>window.__SHANGHAI_APP__?.scene?.map&&window.__SHANGHAI_APP__?.controller',timeout=a.timeout_ms)
   page.evaluate("p=>{const a=__SHANGHAI_APP__;a.syncMode('overview');a.scene.map.jumpTo({center:p,zoom:20,pitch:45,bearing:0})}",g['anchor'])
   report['probe']=page.evaluate(PROBE);log('Longhua source view installed')
   page.wait_for_function('()=>{const s=__LONGHUA_SOURCE__.summary();return s.osm?.active&&s.sourceLoaded}',timeout=a.timeout_ms)
   snapshot=page.evaluate('()=>__LONGHUA_SOURCE__.detail()');write(a.output/'actual-source-snapshot.json',snapshot)
   log('Actual source snapshot saved',feature_count=len(snapshot['features']))
   report['analysis']=analyze(snapshot,g,a.output);report['actual_source_snapshot']=meta(a.output/'actual-source-snapshot.json');report['component_report']=meta(a.output/'component-matches.json')
   try:page.screenshot(path=str(a.output/'observed-map-context.png'),timeout=60000)
   except Exception as e:report['context_screenshot_error']=str(e)
   report['completed']=True;log('Observation complete; fixture requires actual identity review')
   page.evaluate('()=>__LONGHUA_SOURCE__.cleanup()');browser.close();browser=None
 except Exception as e:report['error']={'type':type(e).__name__,'message':str(e)};save();raise
 finally:
  report['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save()
  if browser:browser.close()
if __name__=='__main__':main()
