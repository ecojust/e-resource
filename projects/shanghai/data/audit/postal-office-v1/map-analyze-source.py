import os
from pathlib import Path
import json,numpy as np,shapely
from shapely.geometry import shape,mapping
D=Path(os.environ.get('POSTAL_MAPPING_WORK','/workspace/shanghai-postal-mapping'));F=json.load(open(D/'initial-local-frame.json'));context=json.load(open(D/'context-features.json'));by={r['localId']:r for r in context};p=shape(F['geometry_local_enu']);nids=np.array([1780,814,3148,1959])
near=np.fromfile(D/'baseline-near-triangles.f64',dtype='f8').reshape(-1,3,3);far=np.fromfile(D/'baseline-far-triangles.f64',dtype='f8').reshape(-1,3,3);fo=np.fromfile(D/'baseline-far-owners.u32',dtype='u4')
cent=shapely.points(near[:,:,:2].mean(axis=1));dist=np.column_stack([shapely.distance(cent,shape(by[int(i)]['geometry_local_enu'])) for i in nids]);no=nids[dist.argmin(axis=1)];assert dist.min(axis=1).max()<.6;np.asarray(no,dtype='u4').tofile(D/'baseline-near-classified-owners.u32')
def profile(t):
 polygons=shapely.polygons(t[:,:,:2]);return shapely.union_all(polygons[shapely.area(polygons)>1e-10])
profiles={}
for i in nids:
 profiles[f'near_{i}']=profile(near[no==i]);profiles[f'far_{i}']=profile(far[fo==i])
rows=[{'name':name,'area_m2':q.area,'bounds':list(q.bounds),'outside_source_m2':q.difference(p).area,'intersects_source_m2':q.intersection(p).area,'distance_from_source_m':q.distance(p)} for name,q in profiles.items()]
trials=[]
for margin in [0,.02,.05,.1,.12,.2,.3,.4,.5]:
 q=p.buffer(margin,join_style=2) if margin else p
 trials.append({'margin_m':margin,'vertices':len(q.exterior.coords)-1,'triangles':len(q.exterior.coords)-3,'target_near_remaining_m2':profiles['near_1959'].difference(q).area,'target_far_remaining_m2':profiles['far_1959'].difference(q).area,'neighbor3148_near_overlap_m2':profiles['near_3148'].intersection(q).area,'neighbor3148_far_overlap_m2':profiles['far_3148'].intersection(q).area})
report={'near_classification':'Closest source polygon to each triangle centroid; full-site owner1959 and neighbors1780,814,3148','near_max_assigned_centroid_distance_m':float(dist.min(axis=1).max()),'near_owner_triangle_counts':{str(i):int(np.sum(no==i))for i in nids},'profiles':rows,'margin_trials':trials,'target_near_neighbor3148_native_overlap_m2':profiles['near_1959'].intersection(profiles['near_3148']).area}
(D/'source-profile-analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(D/'source-profiles.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','properties':{'name':k},'geometry':mapping(v)}for k,v in profiles.items()]},ensure_ascii=False)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
