#!/usr/bin/env python3
"""Freeze this reviewed actual source component; never construct an online ID from OSM/GERS."""
from pathlib import Path
import hashlib,json,math
from shapely.geometry import shape
from shapely.ops import transform
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;V=HERE.parent;P=HERE/'actual-main24'
def read(p):return json.loads(p.read_bytes())
def meta(p):b=p.read_bytes();return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(p,d):assert not p.exists(),p;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def ringkey(r):
 r=[tuple(x) for x in r]
 if r[0]==r[-1]:r.pop()
 return min(tuple(q[i:]+q[:i]) for q in (r,list(reversed(r))) for i in range(len(q)))
def polykey(c):return ringkey(c[0]),tuple(sorted(ringkey(r) for r in c[1:]))
obs=read(P/'observation.json');snapshot=read(P/'actual-source-snapshot.json');matched=read(P/'component-matches.json');g=read(V/'longhua-integration/inputs/xuhui-longhua-pagoda/geometry-input.json')
assert obs['completed'] and not obs.get('error') and not obs['page_errors'];assert snapshot['sourceLoaded'] and snapshot['sourceLayer']=='building'
assert meta(P/'actual-source-snapshot.json')==obs['actual_source_snapshot'];assert meta(P/'component-matches.json')==obs['component_report']
assert len(matched['matches'])==1
m=matched['matches'][0];assert m['source_id']==96537940 and m['component_original_index']==245
assert m['iou']>.9999 and m['target_fraction']>.9999 and m['component_fraction']>.9999
feature=snapshot['features'][m['feature_snapshot_index']];assert feature['id']==m['source_id'] and feature['geometry']['type']=='MultiPolygon';assert feature['geometry']['coordinates'][245]==m['geometry']['coordinates']
components=feature['geometry']['coordinates'];unique={};indices={}
for i,c in enumerate(components):
 k=polykey(c);unique.setdefault(k,shape({'type':'Polygon','coordinates':c}));indices.setdefault(k,[]).append(i)
keys=list(unique);geoms=list(unique.values());target_key=polykey(m['geometry']['coordinates']);ti=keys.index(target_key);tree=STRtree(geoms);edges=[];adj={i:set() for i in range(len(geoms))}
for i,p in enumerate(geoms):
 assert p.is_valid and not p.is_empty
 for x in tree.query(p,predicate='intersects'):
  j=int(x)
  if j>i:edges.append([i,j]);adj[i].add(j);adj[j].add(i)
seen={ti};todo=[ti]
while todo:
 i=todo.pop()
 for j in adj[i]-seen:seen.add(j);todo.append(j)
R=6378137.;lon,lat=g['anchor'];cs=math.cos(math.radians(lat));mx=R*math.radians(lon);my=R*math.log(math.tan(math.pi/4+math.radians(lat)/2))
def project(x,y):return ((R*math.radians(x)-mx)*cs,(R*math.log(math.tan(math.pi/4+math.radians(y)/2))-my)*cs)
t=transform(project,geoms[ti]);others=[(t.distance(transform(project,p)),i) for i,p in enumerate(geoms) if i!=ti];others.sort()
assert seen=={ti},'Actual target is connected to another source component; do not freeze until component group is reviewed'
neighbor_checks=[]
for n in g['current_city_detail']['same_near_neighbors_to_retain']:
 ng=transform(project,shape(n['geometry']));neighbor_checks.append({'local_id':n['local_id'],'key':n['key'],'target_component_intersection_m2':t.intersection(ng).area,'target_component_distance_m':t.distance(ng)})
assert all(n['target_component_intersection_m2']==0 for n in neighbor_checks)
fixture={'schema':'actual-osm-component-qa-v1','landmark_id':g['id'],'source_id':m['source_id'],'source_layer':snapshot['sourceLayer'],'height':m['properties']['render_height'],'component_original_index':m['component_original_index'],'geometry':m['geometry'],'origin':'Actual current MAIN Longhua source observation via MapLibre querySourceFeatures, source openmaptiles/building. Unique positive-area component match to frozen tower: IoU0.9999601436055049. No bbox-only identification, clipping, buffering, nearest-ID guess or prior-building evidence. See observation-provenance bindings.','observation_provenance':{'snapshot':meta(P/'actual-source-snapshot.json'),'run':meta(P/'observation.json'),'component_matches':meta(P/'component-matches.json'),'geometry_input':meta(V/'longhua-integration/inputs/xuhui-longhua-pagoda/geometry-input.json')},'identity_scope':'Source-geometry correspondence only; source height5m is not tower height; this is not browser/model acceptance.'}
write(HERE/'longhua-osm-target-evidence.json',fixture)
review={'schema':'longhua-actual-component-review-v1','passed':True,'scope':'Actual source-component identity/connectedness and retained source-neighbor relations only. No precise model or browser acceptance.','fixture':meta(HERE/'longhua-osm-target-evidence.json'),'observation_provenance':fixture['observation_provenance'],'source_id':m['source_id'],'component_index':245,'original_components':len(components),'unique_components':len(keys),'target_occurrences':indices[target_key],'target_connected_original_indices':sorted(i for k in seen for i in indices[keys[k]]),'overlap_touch_pairs_all_groups':len(edges),'target_is_independent_component':True,'nearest_other_components':[{'original_indices':indices[keys[i]],'distance_m':d} for d,i in others[:5]],'retained_13_neighbors':neighbor_checks,'all_other_original_component_geometry_properties_preserved':True,'mutated_source_features':0,'model_accepted':False,'browser_passed':False}
write(HERE/'longhua-component-review.json',review)
print(json.dumps({'fixture':meta(HERE/'longhua-osm-target-evidence.json'),'review':meta(HERE/'longhua-component-review.json'),'component_count':len(components),'unique_components':len(keys),'target_connected':review['target_connected_original_indices'],'nearest':review['nearest_other_components'][0]}))
