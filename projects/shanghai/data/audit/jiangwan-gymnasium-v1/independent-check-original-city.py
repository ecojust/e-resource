"""Independent original gym source geometry and proposed display correction review.
Inputs are immutable Git bytes and the reviewer's own direct accessor/instance decode.
"""
from pathlib import Path
import gzip,hashlib,json,math,sys
import numpy as np
from shapely import polygons
from shapely.geometry import shape,mapping
from shapely.ops import transform,unary_union
M,R,O=map(Path,sys.argv[1:4]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frame=json.loads((M/'initial-local-frame.json').read_text())['anchor'];decode=json.loads((R/'city-source-decode.json').read_text());clip=json.loads((M/'clip-preflight.json').read_text());table=json.loads(gzip.decompress((M/'macro-feature-table.json.gz').read_bytes()));ready=json.loads((M/'macro-READY.json').read_text())
a=math.radians(frame['heading']);co,si=math.cos(a),math.sin(a);k=6371008.8*math.cos(math.radians(frame['lat']));psi=math.asinh(math.tan(math.radians(frame['lat'])))
def local(lng,lat,z=None):
 e=k*math.radians(lng-frame['lng']);n=k*(math.asinh(math.tan(math.radians(lat)))-psi);return co*e-si*n,si*e+co*n
sources={r['localId']:transform(local,shape(r['geometry']))for r in table['features']};source=sources[1558];mask=shape(clip['mask_geometry_local_enu']);assert mask.is_valid and not mask.interiors;assert transform(local,shape(clip['mask_geometry_wgs84'])).symmetric_difference(mask).area<1e-5
near=[r for r in ready['near']if 1558 in r['featureLocalIds']];assert len(near)==1;owners=set(near[0]['featureLocalIds']);assert len(owners)==12
features={r['localId']:r for r in table['features']};identity=features[1558];assert '体育馆' in json.dumps(identity,ensure_ascii=False)
rows=[]
for variant in ['near1558','far']:
 b=next(r for r in decode['variants']if r['variant']==variant);data=(R/b['output']['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==b['output']['sha256'];ts=np.frombuffer(data,dtype='<f8').reshape(-1,3,3);assert len(ts)==b['selectedTriangles'];xy=ts[:,:,:2];v=xy[:,1]-xy[:,0];w=xy[:,2]-xy[:,0];valid=np.abs(v[:,0]*w[:,1]-v[:,1]*w[:,0])>1e-10;occupied=unary_union(polygons(xy[valid]));components=list(occupied.geoms)if occupied.geom_type=='MultiPolygon'else[occupied];assert len(components)==len(owners),(variant,len(components));got=[]
 for component in components:
  scores=sorted([(component.intersection(sources[i]).area,i)for i in owners],reverse=True);area,owner=scores[0];assert area/sources[owner].area>.99999;assert scores[1][0]<1e-7
  intersection=component.intersection(mask).area;outside=component.difference(mask).area if owner==1558 else None
  if owner==1558:assert outside<1e-6
  else:assert intersection<1e-7
  got.append({'owner':owner,'area_m2':component.area,'source_area_m2':sources[owner].area,'source_coverage_fraction':area/sources[owner].area,'outside_display_mask_m2':outside,'display_mask_intersection_m2':intersection,'geometry_local_xy':mapping(component)})
 assert {r['owner']for r in got}==owners
 rows.append({'variant':variant,'input':b['input'],'expanded_triangles':b['expandedTriangles'],'selected_triangles':len(ts),'components':got});print(variant,len(ts),len(got),flush=True)
foreign=[{'owner':i,'overlap_m2':mask.intersection(s).area,'distance_m':mask.distance(s)}for i,s in sources.items()if i!=1558];nonzero=[r for r in foreign if r['overlap_m2']>1e-7];assert len(foreign)==2323 and not nonzero;assert source.difference(mask).area<1e-6
report={'schema':'jiangwan-gymnasium-independent-original-city-preflight-v1','passed':True,'status':'Original city and proposed display-mask proof only; final author geometry and ground collision are separate.','baseline_commit':'a47e69e9cbde689266855d573aa8d1f25b02944d','method':'Independent GLB accessor and GPU-instance decode, actual triangle-projection union, independent immutable feature-table transform and source/neighbor overlap checks. No mapper triangle payload or author geometry rebuild.','bindings':{'source_decode_sha256':sha(R/'city-source-decode.json'),'clip_preflight_sha256':sha(M/'clip-preflight.json'),'script_sha256':sha(Path(__file__)),'feature_table_sha256':sha(M/'macro-feature-table.json.gz'),'ready_sha256':sha(M/'macro-READY.json')},'frame':frame,'actual_city_sources':rows,'display_mask':{'owner':1558,'valid':True,'vertices':len(mask.exterior.coords)-1,'source_area_m2':source.area,'source_uncovered_m2':source.difference(mask).area,'extra_area_outside_source_m2':mask.difference(source).area,'other_source_count':len(foreign),'nonzero_other_sources':nonzero,'nearest_other_source_distance_m':min(r['distance_m']for r in foreign),'specific_retained_sources':{str(i):{'source_area_m2':sources[i].area,'display_mask_overlap_m2':mask.intersection(sources[i]).area,'display_mask_distance_m':mask.distance(sources[i])}for i in [1646,1816,1666]}},'all_macro_source_count':len(sources),'limits':'Display mask removes only original gym1558 source, not new model footprint or ground collision. Stadium1646/1816, pool1666 and all other sources remain separate. Source height is an estimate, not current surveyed barrel roof height.'}
O.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'variants':len(rows),'source_count':len(sources),'mask_vertices':report['display_mask']['vertices']}))
