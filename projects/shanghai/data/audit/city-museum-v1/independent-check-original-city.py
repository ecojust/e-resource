"""Museum original city proof; no invented owner labels on shared near faces.
Usage: immutable-input decoded-triangle-directory clip-candidate.json output.json
"""
from pathlib import Path
import gzip,hashlib,json,math,sys
import numpy as np
from shapely.geometry import shape,mapping,Polygon,MultiPoint
from shapely.ops import transform,unary_union
M,R,C,O=map(Path,sys.argv[1:5]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frame=json.loads((M/'initial-local-frame.json').read_text())['anchor'];decode=json.loads((R/'city-source-decode.json').read_text());clip=json.loads(C.read_text());table=json.loads(gzip.decompress((M/'macro-feature-table.json.gz').read_bytes()));ready=json.loads((M/'macro-READY.json').read_text())
k=6371008.8*math.cos(math.radians(frame['lat']));psi=math.asinh(math.tan(math.radians(frame['lat'])));assert frame['heading']==0
def local(lng,lat,z=None):return k*math.radians(lng-frame['lng']),k*(math.asinh(math.tan(math.radians(lat)))-psi)
features={r['localId']:r for r in table['features']};sources={i:transform(local,shape(r['geometry']))for i,r in features.items()};assert len(sources)==2324
near=[r for r in ready['near']if 1860 in r['featureLocalIds']];assert len(near)==1;owners=set(near[0]['featureLocalIds']);assert owners=={1262,1860,1931,510,958,1061,169,1697};targets={1860,1931}
assert features[1860]['properties']['id']=='cdc86c9b-dee5-4342-a7ee-e962fa0d030e';assert features[1931]['properties']['id']=='d54de774-0952-43c1-98a0-c9cbeaf207b1'
masks={1860:shape(clip['main_mask_geometry_local_enu']),1931:shape(clip['site_mask_geometry_local_enu'])}
for i,key in [(1860,'main'),(1931,'site')]:
 assert masks[i].is_valid;assert transform(local,shape(clip[key+'_mask_geometry_wgs84'])).symmetric_difference(masks[i]).area<1e-5
mask=unary_union(list(masks.values()));decoded={}
for row in decode['variants']:
 data=(R/row['output']['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['output']['sha256'];ts=np.frombuffer(data,dtype='<f8').reshape(-1,3,3);ids=np.fromfile(R/row['ownerOutput']['file'],dtype='<i4');assert len(ts)==row['selectedTriangles']==len(ids);decoded[row['variant']]=(ts,ids,row)
def projection(ts):
 xy=ts[:,:,:2];cross=(xy[:,1,0]-xy[:,0,0])*(xy[:,2,1]-xy[:,0,1])-(xy[:,1,1]-xy[:,0,1])*(xy[:,2,0]-xy[:,0,0]);return unary_union([Polygon(p)for p in xy[np.abs(cross)>1e-10]])
far,fids,frow=decoded['far'];assert set(fids)==owners;farrows=[]
for i in sorted(owners):
 ts=far[fids==i];g=projection(ts);farrows.append({'owner':i,'actual_owner_attribute':True,'triangles':len(ts),'area_m2':g.area,'target_projection_retained_by_mask_m2':g.difference(masks[i]).area if i in targets else None,'foreign_fragments_eligible_by_owner_rule':False if i not in targets else None,'geometry_local_xy':mapping(g)})
ts,nids,nrow=decoded['near1860'];assert len(ts)==122780 and np.all(nids==-1);flat=np.ptp(ts[:,:,2],axis=1)<1e-6;heights=ts[:,:,2].mean(1);roofs={};roofrows=[]
for i in sorted(owners):
 h=float(features[i]['height']);selected=ts[flat&(abs(heights-h)<2e-5)];g=projection(selected);assert len(selected)>0 and sources[i].difference(g).area<1e-5;assert all(abs(h-float(features[j]['height']))>.05 for j in owners if j!=i);roofs[i]=g;overlap=g.intersection(mask).area
 if i not in targets:assert overlap<1e-7,(i,overlap)
 roofrows.append({'owner':i,'source_height_estimate_m':h,'actual_roof_triangles':len(selected),'actual_roof_area_m2':g.area,'source_uncovered_by_roof_m2':sources[i].difference(g).area,'roof_intersection_with_near_mask_m2':overlap,'roof_retained_m2':g.difference(mask).area,'geometry_local_xy':mapping(g)})
ginfo=nrow['groupOutput'];assert sha(R/ginfo['file'])==ginfo['sha256'];groups=json.loads((R/ginfo['file']).read_text());summary={i:{'instances':0,'max_outside_roof_margin_m2':0.,'mask_overlap_area_sum_m2':0.,'actual_max_instance_z_m':0.}for i in owners};instance_count=0
assert features[1860]['family']=='unknown';assert all(features[i]['family']=='apartment'for i in owners-{1860})
for group in groups:
 if not group['instanced']:continue
 t=ts[group['firstTriangle']:group['firstTriangle']+group['triangleCount']];v=np.unique(t.reshape(-1,3),axis=0);env=MultiPoint(v[:,:2]).convex_hull
 if group['instanceCount']in[1152,1]:owner=1860
 else:
  assert group['instanceCount']in[686,6];scores=sorted((env.centroid.distance(sources[i]),i)for i in owners if i!=1860);assert scores[0][0]<.25 and scores[1][0]>.5,scores[:2];owner=scores[0][1]
 outside=env.difference(roofs[owner].buffer(.025,join_style=2)).area;assert outside<1e-7,(owner,outside);overlap=env.intersection(mask).area
 if owner not in targets:assert overlap<1e-7,(owner,overlap)
 r=summary[owner];r['instances']+=1;r['max_outside_roof_margin_m2']=max(r['max_outside_roof_margin_m2'],outside);r['mask_overlap_area_sum_m2']+=overlap;r['actual_max_instance_z_m']=max(r['actual_max_instance_z_m'],float(v[:,2].max()));instance_count+=1
assert instance_count==5528
foreign=[]
for i,g in sources.items():
 if i in targets:continue
 overlap=g.intersection(mask).area;assert overlap<1e-7,(i,overlap);foreign.append({'source':i,'overlap_m2':overlap,'distance_m':g.distance(mask)})
structgroups=[g for g in groups if not g['instanced']];structural=np.concatenate([ts[g['firstTriangle']:g['firstTriangle']+g['triangleCount']]for g in structgroups]);sg=projection(structural);allroofs=unary_union(list(roofs.values()));outside=sg.difference(allroofs.buffer(.025,join_style=2)).area;assert outside<1e-6,outside
output={'schema':'city-museum-independent-original-city-preflight-v1','passed':True,'baseline_commit':'93e3cb2d0ddeba1a7db7d435bf66c2f61492326e','method':'Independent GLB accessor, Meshopt and Float32 instance decode. Near top planes tied to unique source heights and full source coverage. Actual instances independently bounded; main-only unknown family and uniquely closest apartment-source geometry used for instance inference. Shared structural faces retain missing owner IDs.','bindings':{'decode_sha256':sha(R/'city-source-decode.json'),'clip_candidate_sha256':sha(C),'feature_table_sha256':sha(M/'macro-feature-table.json.gz'),'ready_sha256':sha(M/'macro-READY.json'),'script_sha256':sha(Path(__file__))},'frame':frame,'target_ids':sorted(targets),'near_owner_ids':sorted(owners),'far_actual_owner_projections':farrows,'near_roof_projections':roofrows,'near_instance_summary':summary,'near_instance_count':instance_count,'unique_structural_batches':structgroups,'structural_triangles':len(structural),'structural_projection_outside_all_roofs_plus0025_m2':outside,'near_structural_owner_limit':'Shared structural batches do not carry owner IDs. Combined actual extent is bounded; source-local preservation is conservative and does not recover absent face attribution.','all_original_sources_checked':len(sources),'foreign_sources_checked':len(foreign),'foreign_source_polygons_clipped':[],'retained_target_source_areas_m2':{str(i):sources[i].difference(masks[i]).area for i in targets},'main_interface_residual_is_intentional':True,'near_main_interface_height_estimate_m':features[1860]['height'],'limits':'Residual main interfaces remain to protect touching510/1262. No zero-remnant or complete near-face ownership claim. Source heights are predicted city-model values, not architectural measurements. Final model occupancy, collision and browser interface checks are separate.'}
O.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'passed':True,'source_count':len(sources),'near_roof_sets':len(roofs),'instances':instance_count,'retained_source_areas':output['retained_target_source_areas_m2']}))
