#!/usr/bin/env python3
"""Bounded source/owner freeze only; no architecture/navigation acceptance."""
from pathlib import Path
import argparse,copy,gzip,hashlib,json,math
from shapely.geometry import shape,mapping
from shapely.ops import transform
R=6378137.0;ID='xuhui-longhua-pagoda';MID='14-13719-6697';UUID='66c3a80d-8e53-4603-8a2e-3579a0caa485';KEY='building:'+UUID
HERE=Path(__file__).resolve().parent
CONFIG='bc00ae98308d26661b45dd7dab7b5098cab3ca4c7c7f9c1490122212af5e9956'
def read(p):
 b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def meta(p,project=None):
 b=p.read_bytes();d={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if project:d['project_relative_path']=str(p.relative_to(project))
 return d
def enc(d):return (json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def merc(lon,lat):return R*math.radians(lon),R*math.log(math.tan(math.pi/4+math.radians(lat)/2))
def inv(x,y):return math.degrees(x/R),math.degrees(2*math.atan(math.exp(y/R))-math.pi/2)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--project',type=Path,required=True);ap.add_argument('--research',type=Path,required=True);a=ap.parse_args();P=a.project.resolve();research=a.research.resolve()
 proof=read(research/'identity-source-proof.json');handoff=read(research/'handoff.json');D=P/'assets/city-detail/macros'/MID
 table=read(D/'feature-table.json.gz');ready=read(D/'READY.json');ownership=dict(read(D/'ownership.json.gz')['owners']);manifest=read(P/'assets/city-detail/manifest.json')
 assert ready['complete'] and ready['configuration_sha256']==CONFIG and manifest['complete'] and manifest['configuration_sha256']==CONFIG
 for f in ('feature-table.json.gz','ownership.json.gz'):
  assert meta(D/f)=={k:ready['published_files'][f][k] for k in ('bytes','sha256')}
 matches=[f for f in table['features'] if f['key']==KEY];assert len(matches)==1;f=matches[0];assert f['localId']==702 and not f['residual'] and f['roof'] is None
 rawpath=P/'data/fullcity-raw/tiles/14/13719/6697.geojson.gz';raws=read(rawpath)['features'];raw=next(x for x in raws if x['properties']['id']==UUID and x['properties']['source_layer']=='building');props=raw['properties']
 assert raw==proof['raw']['feature'] and raw['geometry']==f['geometry'] and props==f['properties'];assert meta(rawpath)=={k:proof['raw'][k] for k in ('bytes','sha256')};assert any(s['record_id']=='w47011877@11' and s['provider']=='osm' for s in props['sources'])
 assert not props['has_parts'];near=next(n for n in ready['near'] if n['id']==ownership[702]);assert near['id']==handoff['source_mapping']['near_id'];assert near['featureLocalIds']==handoff['keep_same_near_local_ids'][:8]+[702]+handoff['keep_same_near_local_ids'][8:]
 assert meta(D/near['file'])=={'bytes':near['size_bytes'],'sha256':near['sha256']};assert near['sha256']==handoff['source_mapping']['near_sha256'];neighbors=[x for x in table['features'] if x['localId'] in near['featureLocalIds'] and x['localId']!=702];assert len(neighbors)==13
 linked=[];overlap=[];scanned=[];sources={}
 geo=shape(raw['geometry']);anchor=list(geo.centroid.coords[0]);assert anchor==proof['source_shape']['centroid_lonlat']
 mx,my=merc(*anchor);scale=math.cos(math.radians(anchor[1]));local=lambda lon,lat:((merc(lon,lat)[0]-mx)*scale,(merc(lon,lat)[1]-my)*scale);lg=transform(local,geo)
 for x in range(13718,13721):
  for y in range(6696,6699):
   p=P/f'data/fullcity-raw/tiles/14/{x}/{y}.geojson.gz'
   if not p.exists():continue
   d=read(p);scanned.append(f'14-{x}-{y}');sources[f'raw:14-{x}-{y}']=meta(p,P)
   for other in d['features']:
    op=other['properties']
    if op['source_layer']!='building_part':continue
    if op.get('building_id')==UUID:linked.append(op['id'])
    if shape(other['geometry']).intersects(geo):overlap.append(op['id'])
 assert not linked and not overlap
 residuals=[x for x in table['features'] if x['residual'] and (x['properties'].get('id')==UUID or x['properties'].get('building_id')==UUID)];assert not residuals and KEY not in ready['source_roof_keys']
 current={'configuration_sha256':CONFIG,'complete_city_macro_count':manifest['model_count'],'complete_city_feature_count':manifest['feature_count'],'owner_macro_id':MID,'feature_local_id':702,'feature_id_base':1,'near_owner_id':near['id'],'far_file':'assets/city-detail/macros/'+MID+'/'+ready['far']['file'],'near_file':'assets/city-detail/macros/'+MID+'/'+near['file'],'near_asset_sha256':near['sha256'],'near_asset_size_bytes':near['size_bytes'],'near_feature_local_ids':near['featureLocalIds'],'original_macro_origin':table['origin'],'frozen_effective_feature':f,'same_near_neighbors_to_retain':[{'local_id':x['localId'],'key':x['key'],'geometry':x['geometry'],'height':x['height'],'base':x['base'],'retain':True} for x in neighbors]}
 for name,file in [('feature_table_source_file','feature-table.json.gz'),('ready_source_file','READY.json'),('ownership_source_file','ownership.json.gz')]:current[name]=meta(D/file,P);sources[name]=current[name]
 ring=list(lg.exterior.coords);winding=1 if lg.exterior.is_ccw else -1;edges=[]
 for i,(a1,b) in enumerate(zip(ring,ring[1:])):
  dx,dy=b[0]-a1[0],b[1]-a1[1];length=math.hypot(dx,dy);normal=[winding*dy/length,-winding*dx/length]
  edges.append({'edge_index':i,'endpoints_wgs84':raw['geometry']['coordinates'][0][i:i+2],'endpoints_local_east_north_m':[list(a1),list(b)],'length_m':length,'outward_normal_east_north':normal,'outward_azimuth_deg':math.degrees(math.atan2(normal[0],normal[1]))%360})
 data={'schema':'building-v6-frozen-existing-osm-geometry-input-v1','id':ID,'name_zh':'龙华塔','name_en':'Longhua Pagoda','district_id':'310104','district_name':'徐汇区','geometry_source_kind':'existing_overture_osm_footprint','is_osm_building_geometry':True,'status':'Exact existing source footprint and owner only; no model or navigation acceptance.','anchor':anchor,'origin_longitude':anchor[0],'origin_latitude':anchor[1],'anchor_method':'Planar WGS84-coordinate centroid of exact source polygon, identical to frozen identity proof; coordinate origin only, not a surveyed point.','geometry':raw['geometry'],'geographic_bbox':list(geo.bounds),'model_geometry_local_east_north_m':mapping(lg),'polygon_local_east_north':[list(x) for x in ring[:-1]],'geometry_components':1,'geometry_rings':1,'coordinate_contract':{'earth_radius_m':R,'geographic':'EPSG:4326','metre_frame':'Source-builder Web Mercator differences times cos(anchor latitude)','gltf_xyz':'[east_m,elevation_m,-north_m]','original_source_vertex_order_and_all_rings_preserved':True,'geometry_exactly_equals_existing_source':True,'no_image_retracing_or_bbox_substitution':True},'front_edge':None,'streetfront':None,'facade_frame':{'photo_face_to_geographic_edge_assignment':None,'photographic_axis_note':'No geographically calibrated entry facade. Official alternating openings do not specify a proven ground-level phase; model calibration must label its phase as estimated.'},'all_source_edges':edges,'source':{'release':'2026-10-21.0','key':KEY,'overture_id':UUID,'owner_macro_id':MID,'owner_tile':[14,13719,6697],'provider_records':props['sources'],'properties':props,'source_geometry':raw['geometry'],'frozen_raw_feature':raw,'raw_macro_source_file':meta(rawpath,P),'is_osm_geometry':True,'osm_source_comparison':proof['live_OSM_comparison']},'identity_evidence':{'file':'identity-source-proof.json',**meta(research/'identity-source-proof.json'),'scope':'Named same-provider way47011877@11/source UUID matches; not nearest-point substitution.'},'current_city_detail':current,'existing_height':{'height_m':f['height'],'base_m':f['base'],'quality':f['height_quality'],'use_for_new_model':False,'reason':'CNBH raster estimate is not tower height.'},'parts':[],'parts_audit':{'source_has_parts':False,'linked_source_parts':len(linked),'raw_linked_parts':len(linked),'related_residuals':len(residuals),'overlapping_unassociated_parts':len(overlap),'scanned_raw_macros':scanned,'scope':'Exact linked and intersecting building_parts checked in owner+8macro halo; no assumption of absent real temple annexes.'},'replacement':{'building_ids':[UUID],'building_part_ids':[],'feature_local_ids':[702],'retained_same_near_feature_local_ids':handoff['keep_same_near_local_ids'],'only_exact_ids':True,'do_not_delete_nearby_buildings_by_radius':True,'target_is_qualified_source_roof':False,'applied':False,'mask_contract':'Hide only local702 when precise model is actually visible; retain all13 original neighbor features and restore baseline on unload/failure.'},'license':['ODbL-1.0'],'attribution':'© OpenStreetMap contributors; Overture Maps2026-10-21.0','limitations':handoff['still_estimated_or_unknown']}
 out=HERE/'inputs'/ID/'geometry-input.json';assert not out.exists();out.write_bytes(enc(data));(HERE/'evidence/identity-source-proof.json').write_bytes((research/'identity-source-proof.json').read_bytes());(out.parent/'identity-source-proof.json').write_bytes((research/'identity-source-proof.json').read_bytes())
 report={'schema':'longhua-source-owner-freeze-v1','passed':True,'scope':'Existing exact source/owner/coordinate preservation only, not architectural or browser acceptance.','id':ID,'geometry_sha256':meta(out)['sha256'],'source_key':KEY,'owner_macro_id':MID,'local_id':702,'near_id':near['id'],'neighbors_retained':handoff['keep_same_near_local_ids'],'source_files':sources,'source_ring_exact':True,'raw_effective_feature_exact':True,'parts_empty_in_scanned_scope':True,'front_edge_assigned':False,'model_accepted':False,'browser_passed':False};(out.parent/'mapping-report.json').write_bytes(enc(report));print(json.dumps({'file':str(out),**meta(out),'anchor':anchor,'neighbors':len(neighbors)}))
if __name__=='__main__':main()
