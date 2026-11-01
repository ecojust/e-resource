"""Independent actual source projection and bounded display-mask verification.

Reads independently decoded GLB/instance triangles and immutable Git-bound
feature records. Does not reuse mapper triangle payloads or model geometry.
"""
from pathlib import Path
import gzip,hashlib,json,math,sys
import numpy as np
from shapely import polygons
from shapely.geometry import shape,mapping
from shapely.ops import transform,unary_union
M,R,O=map(Path,sys.argv[1:4])
frame=json.loads((M/'initial-local-frame.json').read_text())['anchor'];decode=json.loads((R/'city-source-decode.json').read_text());clips=json.loads((M/'clip-preflight.json').read_text());table=json.loads(gzip.decompress((M/'macro-feature-table.json.gz').read_bytes()))
a=math.radians(frame['heading']);co,si=math.cos(a),math.sin(a);k=6371008.8*math.cos(math.radians(frame['lat']));psi=math.asinh(math.tan(math.radians(frame['lat'])))
def local(lng,lat,z=None):
 e=k*math.radians(lng-frame['lng']);n=k*(math.asinh(math.tan(math.radians(lat)))-psi);return co*e-si*n,si*e+co*n
sources={r['localId']:transform(local,shape(r['geometry']))for r in table['features']};masks={r['local_id']:shape(r['mask_geometry_local_enu'])for r in clips['rows']}
for row in clips['rows']:
 inverse=transform(local,shape(row['mask_geometry_wgs84']));assert inverse.symmetric_difference(masks[row['local_id']]).area<1e-5
expected_owners={'near1646':{1646},'near1816':{1816,1768,677,2225},'far':{1646,1816,1768,677,2225}}
rows=[]
for variant,owners in expected_owners.items():
 b=next(r for r in decode['variants']if r['variant']==variant);data=(R/b['output']['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==b['output']['sha256'];ts=np.frombuffer(data,dtype='<f8').reshape(-1,3,3);assert len(ts)==b['selectedTriangles'];xy=ts[:,:,:2];v=xy[:,1]-xy[:,0];w=xy[:,2]-xy[:,0];valid=np.abs(v[:,0]*w[:,1]-v[:,1]*w[:,0])>1e-10;occupied=unary_union(polygons(xy[valid]));components=list(occupied.geoms)if occupied.geom_type=='MultiPolygon'else[occupied];assert len(components)==len(owners),(variant,len(components));got=[]
 for component in components:
  scores=sorted([(component.intersection(sources[i]).area,i)for i in owners],reverse=True);area,owner=scores[0];assert area/sources[owner].area>.99999
  if len(scores)>1:assert scores[1][0]<1e-7
  intersections={str(i):component.intersection(mask).area for i,mask in masks.items()}
  outside=component.difference(masks[owner]).area if owner in masks else None
  if owner in masks:assert outside<1e-6
  else:assert all(v<1e-7 for v in intersections.values())
  got.append({'owner':owner,'area_m2':component.area,'source_area_m2':sources[owner].area,'source_coverage_fraction':area/sources[owner].area,'outside_own_display_mask_m2':outside,'all_mask_intersections_m2':intersections,'geometry_local_xy':mapping(component)})
 assert {r['owner']for r in got}==owners
 rows.append({'variant':variant,'input':b['input'],'expanded_triangles':b['expandedTriangles'],'selected_triangles':len(ts),'components':got});print(variant,len(ts),len(got),flush=True)
mask_records=[]
for owner,mask in masks.items():
 foreign=[{'owner':i,'overlap_m2':mask.intersection(source).area,'distance_m':mask.distance(source)}for i,source in sources.items()if i not in masks];nonzero=[r for r in foreign if r['overlap_m2']>1e-7];assert not nonzero
 assert sources[owner].difference(mask).area<1e-6
 mask_records.append({'owner':owner,'valid':mask.is_valid,'holes':len(mask.interiors),'vertices':len(mask.exterior.coords)-1,'source_uncovered_m2':sources[owner].difference(mask).area,'extra_area_outside_source_m2':mask.difference(sources[owner]).area,'other_source_count':len(foreign),'nonzero_other_sources':nonzero,'nearest_other_source_distance_m':min(r['distance_m']for r in foreign)})
field=unary_union([sources[i]for i in masks]);safe=field.convex_hull.difference(field).buffer(-12);overlap=safe.intersection(unary_union(list(masks.values()))).area;assert overlap<1e-7
report={'schema':'jiangwan-stadium-independent-original-city-preflight-v1','passed':True,'status':'Original city and proposed display-mask proof only; final author geometry and ground collision are separate.','baseline_commit':'96e4dfaff588222475c25a66af1c84a24b45a475','method':'Independent GLB accessor and GPU-instance decode, actual triangle-projection union, independent immutable feature-table transform and bounded source/neighbor overlap checks. No mapper triangle payload or author geometry rebuild.','bindings':{'source_decode_sha256':hashlib.sha256((R/'city-source-decode.json').read_bytes()).hexdigest(),'clip_preflight_sha256':hashlib.sha256((M/'clip-preflight.json').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'frame':frame,'actual_city_sources':rows,'display_masks':mask_records,'safe_field_display_mask_overlap_m2':overlap,'mask_separation_m':masks[1646].distance(masks[1816]),'all_macro_source_count':len(sources),'limits':'Simplified/external-offset masks clear only original owner sources; they are not new asset footprint or ground collision. Inner independent sources remain preserved. Historical source heights are CNBH estimates.'}
O.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'variants':len(rows),'source_count':len(sources),'mask_vertices':[r['vertices']for r in mask_records],'field_overlap':overlap}))
