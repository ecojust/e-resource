import os,argparse,hashlib
from pathlib import Path
import json,numpy as np,shapely,time
from shapely.geometry import shape,Polygon,mapping
D=Path(os.environ.get('POSTAL_MAPPING_WORK','/workspace/shanghai-postal-mapping'))
ap=argparse.ArgumentParser(description='Project actual Postal model geometry and exclude only the semantic courtyard floor');ap.add_argument('--reuse-full-projection',type=Path);args=ap.parse_args();prior=json.loads(args.reuse_full_projection.read_text()) if args.reuse_full_projection else None;prior_by_sha={r['asset_binding']['sha256']:r for r in prior['records']} if prior else {}
binds=json.load(open(D/'delivered-decode.json'))
contexts={r['localId']:shape(r['geometry_local_enu']) for r in json.load(open(D/'context-features.json'))}
source=contexts[1959]
contract=json.load(open(D/'footprint-contract.json'));court=shape(contract['courtyard_canopy_plan_local_enu'])
contexts={i:q for i,q in contexts.items() if i!=1959}
profiles=json.load(open(D/'source-profiles.geojson'))['features']
native={r['properties']['name']:shape(r['geometry']) for r in profiles}
def cut(poly,height,above):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ia=a[2]>=height-1e-12 if above else a[2]<=height+1e-12
  ib=b[2]>=height-1e-12 if above else b[2]<=height+1e-12
  if ia:out.append(a)
  if ia!=ib:
   f=(height-a[2])/(b[2]-a[2]);p=a+(b-a)*f;p[2]=height;out.append(p)
 return out
records=[]
for bind in binds:
 started=time.time()
 tri=np.fromfile(bind['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*np.array([1,-1,1])
 xy=tri[:,:,:2];a=xy[:,1]-xy[:,0];b=xy[:,2]-xy[:,0];cross=a[:,0]*b[:,1]-a[:,1]*b[:,0]
 # Union bounded batches so final three-asset checks can coexist with a
 # separately scheduled low-thread native render without retaining hundreds
 # of thousands of GEOS triangle objects at once.
 prior_record=prior_by_sha.get(bind['sha256'])
 if prior_record:
  assert prior_record['asset_binding']['bytes']==bind['bytes'] and prior_record['asset_binding']['triangles']==bind['triangles']
  full=shape(prior_record['full_projection_local_enu'])
 else:
  projected=xy[np.abs(cross)>1e-9]
  batches=[shapely.union_all(shapely.polygons(projected[i:i+8192])) for i in range(0,len(projected),8192)]
  full=shapely.union_all(batches)
 material_ids=np.fromfile(bind['triangle_material_ids_file'],dtype='u2');assert len(material_ids)==len(tri)
 dark=bind['material_names'].index('dark stone');low_mask=(tri[:,:,2].min(1)<=2)&(tri[:,:,2].max(1)>=0)
 floor_candidates=(material_ids==dark)&(tri[:,:,2].min(1)>=-1e-5)&(tri[:,:,2].max(1)<=.16001)
 floor_indices=np.flatnonzero(floor_candidates);floor_mask=np.zeros(len(tri),dtype=bool)
 for idx in floor_indices:
  if all(court.buffer(1e-5).covers(shapely.Point(p[:2]))for p in tri[idx]):floor_mask[idx]=True
 assert int(floor_mask.sum())==12,('Unexpected courtyard floor identity',bind['variant'],int(floor_mask.sum()))
 floor_projection=shapely.union_all(shapely.polygons(tri[floor_mask,:,:2]));assert floor_projection.symmetric_difference(court).area<.001
 low=tri[low_mask&~floor_mask];polys=[]
 for t in low:
  p=cut(list(t),0,True)
  if len(p)<3:continue
  p=cut(p,2,False)
  if len(p)<3:continue
  q=Polygon([x[:2] for x in p])
  if q.area>1e-10:polys.append(q)
 ground=shapely.union_all(polys)
 foreign=[{'owner_local_id':i,'model_overlap_m2':q.intersection(full).area,'low_overlap_m2':q.intersection(ground).area,'model_distance_m':q.distance(full)} for i,q in contexts.items()]
 nativechecks=[{'profile':i,'model_overlap_m2':q.intersection(full).area,'low_overlap_m2':q.intersection(ground).area,'model_distance_m':q.distance(full)} for i,q in native.items() if i in ['near_3148','near_1780','near_814']]
 records.append({'full_projection_reused_from':{'file':str(args.reuse_full_projection),'sha256':hashlib.sha256(args.reuse_full_projection.read_bytes()).hexdigest(),'matching_asset_sha256':bind['sha256']} if prior_record else None,'variant':bind['variant'],'asset_binding':bind,'bounds_glb':{'min':[float(tri[:,:,0].min()),float(tri[:,:,2].min()),float(-tri[:,:,1].max())],'max':[float(tri[:,:,0].max()),float(tri[:,:,2].max()),float(-tri[:,:,1].min())]},'full_projection_local_enu':mapping(full),'full_projection_area_m2':full.area,'ground_geometry_local_enu':mapping(ground),'ground_area_m2':ground.area,'walkable_courtyard_floor_exclusion':{'material':'dark stone','triangle_count':int(floor_mask.sum()),'z_range_m':[float(tri[floor_mask,:,2].min()),float(tri[floor_mask,:,2].max())],'plan_area_m2':floor_projection.area,'plan_vs_author_court_symmetric_difference_m2':floor_projection.symmetric_difference(court).area,'rule':'Actual indexed material dark stone triangles entirely at z0..0.16001m and wholly inside authored courtyard plan buffered0.00001m for Float32 coordinate precision; exactly12 box faces match the documented courtyard floor. U base extends to0.18m and remains structural.','ground_union_including_floor_area_m2':ground.union(floor_projection).area,'floor_is_not_building_collision':True},'ground_candidate_triangles':len(low),'ground_projected_polygons':len(polys),'source_area_not_covered_by_model_m2':source.difference(full).area,'model_projection_beyond_source_m2':full.difference(source).area,'retained_source_checks':foreign,'retained_actual_near_checks':nativechecks,'elapsed_seconds':round(time.time()-started,3)})
 print(json.dumps({'variant':bind['variant'],'triangles':bind['triangles'],'full_area':full.area,'low_area':ground.area,'source_uncovered':source.difference(full).area,'beyond_source':full.difference(source).area,'overlapping_foreign':[r for r in foreign+nativechecks if r['model_overlap_m2']>1e-8]},ensure_ascii=False),flush=True)
json.dump({'schema':'postal-delivered-projection-v1','method':'Actual GLTFLoader indices/material IDs after complete node/instance transforms; exclude only the12 verified courtyard-floor triangles, then exactly clip all remaining triangles to local z=[0,2] for structural ground projection. U base, columns and walls retained. No convex hull, source footprint, or canopy projection substitutes.','records':records},open(D/'delivered-projection-preflight.json','w'),ensure_ascii=False,indent=2)
