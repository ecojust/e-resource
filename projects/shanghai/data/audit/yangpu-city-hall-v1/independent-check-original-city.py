import json,hashlib,gzip,math,sys
from pathlib import Path
import numpy as np
from shapely import polygons
from shapely.geometry import shape,box,mapping
from shapely.ops import unary_union,transform
M=Path(sys.argv[1]);R=Path(sys.argv[2]);j=json.loads((M/'preflight.json').read_text());d=json.loads((R/'city-source-decode.json').read_text())
source=shape(j['source_geometry_local_xy']);sources={525:source,**{r['local_id']:shape(r['source_geometry_local_xy']) for r in j['context_sources']}}
table=json.loads(gzip.decompress((M/'macro-feature-table.json.gz').read_bytes()))
frame=j['provisional_frame'];ang=math.radians(frame['heading']);co,si=math.cos(ang),math.sin(ang);scale=6371008.8*math.cos(math.radians(frame['lat']));psi=math.asinh(math.tan(math.radians(frame['lat'])))
def local(lng,lat,z=None):
 e=math.radians(lng-frame['lng'])*scale;n=(math.asinh(math.tan(math.radians(lat)))-psi)*scale;return co*e-si*n,si*e+co*n
all_sources={row['localId']:transform(local,shape(row['geometry'])) for row in table['features']}
for owner in [239,525,534,1005,1047,1850,2006]:sources[owner]=all_sources[owner]
assert source.symmetric_difference(sources[525]).area<1e-6
rows=[];road=box(-70,-19.5,70,-15.7)
assert all(s.intersection(road).area<1e-7 for s in all_sources.values())
for variant in ['near','far']:
 binding=next(r for r in d['variants'] if r['variant']==variant);file=R/binding['output']['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==binding['output']['sha256']
 ts=np.fromfile(file,dtype='<f8').reshape(-1,3,3);xy=ts[:,:,:2];a=xy[:,1]-xy[:,0];b=xy[:,2]-xy[:,0];mask=np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])>1e-10;occupied=unary_union(polygons(xy[mask]));cs=list(occupied.geoms);assert len(cs)==7
 result=[]
 for p in cs:
  hits=sorted([(p.intersection(s).area,k) for k,s in sources.items()],reverse=True);v,owner=hits[0];assert v/sources[owner].area>.9999;assert hits[1][0]<1e-7
  result.append({'owner':owner,'area_m2':p.area,'source_coverage_fraction':v/sources[owner].area,'road_corridor_overlap_m2':p.intersection(road).area,'geometry_local_xy':mapping(p)})
  assert p.intersection(road).area<1e-7
  if owner==525:
   assert p.difference(source.buffer(.12,join_style=2)).area<1e-7
   own=p
 assert {r['owner'] for r in result}=={239,525,534,1005,1047,1850,2006}
 rows.append({'variant':variant,'input':binding['input'],'expanded_triangles':binding['expandedTriangles'],'selected_triangles':len(ts),'projection_components':result,'own_area_m2':own.area,'own_outside_source_m2':own.difference(source).area,'own_outside_provisional_0_12m_buffer_m2':own.difference(source.buffer(.12,join_style=2)).area})
report={'schema':'yangpu-city-hall-independent-source-preflight-v1','status':'Original city source proof; authored geometry and final placement are certified separately','passed':True,'method':'Reviewer direct indexed/instanced GLB decode and actual triangle union; no GLTFLoader or mapper triangle payload reuse','source_area_m2':source.area,'provisional_road_corridor':list(road.bounds),'all_macro_sources_checked_for_road_void':len(all_sources),'rows':rows}
Path(sys.argv[3]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'source_area':source.area,'rows':[{k:r[k] for k in ['variant','selected_triangles','own_area_m2','own_outside_source_m2']} for r in rows]}))
