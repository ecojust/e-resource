"""Incremental height-clip geometry proof from independently decoded original sources.
Usage: review-dir preflight.json final-contract.json gpu-rows.f32 output.json
No GLB, model or native reconstruction. GPU numerical error is a separate proof.
"""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
import shapely
from shapely.geometry import shape,Polygon,MultiPoint,box,mapping
from shapely.ops import transform,unary_union
R,P,C,G,O=map(Path,sys.argv[1:6]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads(P.read_text());contract=json.loads(C.read_text());orig=json.loads((R/'independent-original-city-projection.json').read_text());dec=json.loads((R/'city-triangles/city-source-decode.json').read_text());frame=dec['frame']
before_path=R/'height-fix-history/frozen-before/projects/shanghai/data/audit/city-museum-v1/footprint-review.json';before=json.loads(before_path.read_text())['proposed_placement_contract']
changed={k for k in set(before)|set(contract)if before.get(k)!=contract.get(k)}
allowed={'display_height_clips','expected_display_height_triangle_count','expected_global_clip_triangle_count','expected_model_gpu_clip_triangle_count','registration_note','source_retained_actual_native_projection_area_after_height_clips_m2','source_retained_actual_native_projection_scope'}
assert changed==allowed,changed
assert contract['display_height_clips']==spec['display_height_clips'] and len(contract['display_height_clips'])==2
assert [contract[k]for k in ['expected_replacement_triangle_count','expected_display_height_triangle_count','expected_model_gpu_clip_triangle_count','expected_global_clip_triangle_count','expected_global_clip_capacity']]==[40,4,44,262,288]
rows=np.frombuffer(G.read_bytes(),dtype='<f4').astype(float).reshape(-1,16);assert rows.shape==(262,16)
def fhash(s):
 h=2166136261
 for c in s:h=((h^ord(c))*16777619)&0xffffffff
 return h%16777215
macro_id='14-13722-6690';macro_hash=fhash(macro_id)
assert all(int(r[12])==1860 and int(r[13])==macro_hash for r in rows[258:])
assert all(r[6]<r[7]for r in rows)
for r in rows[:258]:assert list(r[6:8])==[-100,1000]
origin=[121.4737,31.2304];rad=math.pi/180;K=6371008.8*math.cos(origin[1]*rad);kf=6371008.8*math.cos(frame['lat']*rad)
psi=lambda a:math.asinh(math.tan(a*rad))
offx=K*(frame['lng']-origin[0])*rad;offz=K*(psi(origin[1])-psi(frame['lat']));scale=K/kf
world=lambda x,y,z=None:(offx+scale*x,offz-scale*y)
def row_poly(r):return Polygon([[r[0],r[1]],[r[2],r[3]],[r[4],r[5]]]).intersection(box(*r[8:12]))
new_clip=unary_union([row_poly(r)for r in rows[258:]])
assert new_clip.is_valid
# candidateInside accepts either three nonnegative or three nonpositive cross
# products with epsilon. A short exterior edge can expand beyond 3mm while
# remaining inside the strict bbox, so foreign protection uses the full region.
def cross_region(r):
 vertices=[np.array(r[0:2]),np.array(r[2:4]),np.array(r[4:6])]
 corners=[np.array([r[8],r[9]]),np.array([r[10],r[9]]),np.array([r[10],r[11]]),np.array([r[8],r[11]])]
 unit=2**-24;gamma3=3*unit/(1-3*unit);error=0.0
 for a,b in zip(vertices,vertices[1:]+vertices[:1]):
  d=b-a
  # Stored row values and bbox-contained binary32 fragments satisfy Sterbenz
  # exact subtraction at this local map scale. Three rounded product/difference
  # operations (or FMA) are bounded by gamma3 times absolute product magnitudes.
  assert all(min(abs(a[j]),abs(b[j]),abs(r[8+j]),abs(r[10+j]))*2>=max(abs(a[j]),abs(b[j]),abs(r[8+j]),abs(r[10+j]))for j in [0,1])
  error=max(error,max(gamma3*(abs(d[0]*(q[1]-a[1]))+abs(d[1]*(q[0]-a[0])))for q in corners))
 epsilon=float(np.float32(.001))+error
 def trim(poly,a,b,sign):
  d=b-a;value=lambda q:sign*(d[0]*(q[1]-a[1])-d[1]*(q[0]-a[0]))+epsilon
  out=[]
  for u,v in zip(poly,poly[1:]+poly[:1]):
   du,dv=value(u),value(v);ui,vi=du>=0,dv>=0
   if ui:out.append(u)
   if ui!=vi:out.append(u+(v-u)*(du/(du-dv)))
  return out
 pieces=[]
 for sign in [1,-1]:
  poly=corners.copy()
  for a,b in zip(vertices,vertices[1:]+vertices[:1]):
   if poly:poly=trim(poly,a,b,sign)
  if poly:pieces.append(MultiPoint(poly).convex_hull)
 return unary_union(pieces),error
expanded_rows=[cross_region(r)for r in rows[258:]]
foreign_gpu_region=unary_union([r[0]for r in expanded_rows])
assert new_clip.difference(foreign_gpu_region).area<1e-12

owners=orig['near_owner_ids'];base_rows=[r for r in rows[:258]if int(r[12])in owners and int(r[13])==macro_hash];assert len(base_rows)==40
base_clip=unary_union([row_poly(r)for r in base_rows]);final_clip=base_clip.union(new_clip)
new_native=unary_union([shape(r['geometry_local_enu'])for r in spec['patches']]);domain=transform(world,new_native.buffer(.1,join_style=2))
low,high=spec['display_height_clips'][0]['min_height'],spec['display_height_clips'][0]['max_height'];assert [low,high]==[28.705,30.11]
ref=spec['display_height_clips'][0]['height_reference'];yscale=math.cos(origin[1]*rad)/math.cos(ref[1]*rad)
expected_y=np.array([low*yscale,high*yscale],dtype=np.float32).astype(float)
assert all(np.array_equal(r[6:8],expected_y)for r in rows[258:])
def load_variant(name):
 row=next(r for r in dec['variants']if r['variant']==name);p=R/'city-triangles'/row['output']['file'];assert sha(p)==row['output']['sha256'];b=p.read_bytes();ts=np.frombuffer(b,dtype='<f8').reshape(-1,3,3)
 return row,ts
near_binding,ts=load_variant('near1860');assert len(ts)==122780
projected=shapely.convex_hull(shapely.polygons(ts[:,:,:2]));zmax=ts[:,:,2].max(1);matches={}
for r in orig['near_roof_projections']:
 env=shape(r['geometry_local_xy']).buffer(.005,join_style=2)
 matches[r['owner']]=shapely.covers(env,projected)&(zmax<=r['source_height_estimate_m']+.005)
counts=np.stack(list(matches.values())).sum(0);assert counts.min()>0
assert int(matches[1262].sum())==7314 and int(matches[510].sum())==8264
index_path=O.with_name('possible-owner-indices.json');index_path.write_text(json.dumps({'original_near_payload_sha256':near_binding['output']['sha256'],'indices':{str(k):np.flatnonzero(v).tolist()for k,v in matches.items()}},separators=(',',':'))+'\n')
def cut(poly,h,above):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ai=a[2]>=h if above else a[2]<=h;bi=b[2]>=h if above else b[2]<=h
  if ai:out.append(a)
  if ai!=bi:out.append(a+(b-a)*((h-a[2])/(b[2]-a[2])))
 return out
upper={}
for i in np.flatnonzero((ts[:,:,2].min(1)<=high)&(zmax>=low)):
 v=cut(list(ts[i]),low,True)
 if v:v=cut(v,high,False)
 if v:upper[int(i)]=transform(world,MultiPoint([p[:2]for p in v]).convex_hull)
# Buffer is a conservative whole-geometry margin, not area-only acceptance.
# The separate numerical review must prove actual Float32 displacement below it.
robust_margin=.003;robust_final=final_clip.buffer(-robust_margin,join_style=2)
targets=[];uncovered=[];robust_uncovered=[]
for i,g in upper.items():
 if not matches[1860][i]:continue
 clipped=g.intersection(domain)
 if clipped.is_empty:continue
 targets.append((i,clipped))
 if not clipped.difference(final_clip).is_empty:uncovered.append(i)
 if not clipped.difference(robust_final).is_empty:robust_uncovered.append(i)
assert targets and not uncovered,uncovered
assert not robust_uncovered,robust_uncovered
union=unary_union([g for _,g in targets]);before_residue=union.difference(base_clip);after_residue=union.difference(final_clip)
assert after_residue.is_empty
foreign=[]
for owner in owners:
 if owner==1860:continue
 selected=[(i,g)for i,g in upper.items()if matches[owner][i]]
 bad=[i for i,g in selected if not g.intersection(foreign_gpu_region.buffer(robust_margin,join_style=2)).is_empty]
 assert not bad,(owner,bad[:12])
 foreign.append({'owner':owner,'possible_original_triangles':int(matches[owner].sum()),'native_max_z':float(zmax[matches[owner]].max()),'height_slab_triangles':len(selected),'triangles_touching_full_cross_epsilon_gpu_regions_plus3mm':len(bad),'protection':'all vertices below lower threshold'if not selected else'full height-clipped triangle support spatially separate from expanded new GPU regions'})
far_binding,far=load_variant('far');op=R/'city-triangles'/far_binding['ownerOutput']['file'];assert sha(op)==far_binding['ownerOutput']['sha256'];far_ids=np.frombuffer(op.read_bytes(),dtype='<i4');assert len(far_ids)==len(far)
far_clip=unary_union([row_poly(r)for r in rows if int(r[12])==1860 and int(r[13])==macro_hash]);far_robust=far_clip.buffer(-robust_margin,join_style=2);far_targets=[]
for i,t in enumerate(far):
 if far_ids[i]!=1860:continue
 v=cut(list(t),low,True)
 if v:v=cut(v,high,False)
 if not v:continue
 g=transform(world,MultiPoint([p[:2]for p in v]).convex_hull).intersection(domain)
 if g.is_empty:continue
 assert g.difference(far_robust).is_empty,('far uncovered geometry',i)
 far_targets.append(i)
assert far_targets
result={'schema':'city-museum-independent-height-geometry-v1','passed':True,'scope':'Incremental original-source geometry proof; no authored model reconstruction, no browser, and no claim of exact GPU rasterization. Numerical error bounds and actual final pixels require separately bound reviews.','bindings':{'preflight':{'file':str(P),'sha256':sha(P)},'contract':{'file':str(C),'sha256':sha(C)},'actual_gpu_rows':{'file':str(G),'bytes':G.stat().st_size,'sha256':sha(G)},'original_near_triangle_payload_sha256':near_binding['output']['sha256'],'original_far_triangle_payload_sha256':far_binding['output']['sha256'],'original_placement_footprint_sha256':sha(before_path),'original_city_review_sha256':sha(R/'independent-original-city-projection.json'),'script_sha256':sha(Path(__file__))},'changed_contract_keys':sorted(changed),'all_other_contract_fields_exactly_equal':True,'all_model_assets_and_2d_vector_collision_fields_unchanged':True,'clip_rows':{'base_2d':40,'new_height':4,'museum_gpu':44,'all_city_gpu':262,'capacity':288},'near_possible_owners_complete':True,'ambiguous_triangles':int((counts>1).sum()),'possible_owner_index_payload':{'file':str(index_path),'sha256':sha(index_path)},'world_y':{'source_anchor':ref,'analytic_scale':yscale,'actual_float32_range':expected_y.tolist(),'native_interval':[low,high],'neighbor1262_max_native':float(zmax[matches[1262]].max()),'raw_world_y_margin_before_roundoff_bound':float(expected_y[0]-zmax[matches[1262]].max()*yscale)},'northern_complete_support':{'actual_triangle_pieces':len(targets),'before_projection_m2_world':before_residue.area,'before_projection_boundary_or_line_length_world':before_residue.length,'after_geometry_is_empty':after_residue.is_empty,'uncovered_triangles':uncovered,'robust_margin_world_m':robust_margin,'uncovered_triangles_after_inward_margin':robust_uncovered,'method':'Every selected actual height-clipped triangle, including degenerate projected lines/points, is intersected with the two northern patch neighborhoods and proved contained in union of actual Float32 triangle polygons intersected with their strict GPU bboxes; 3mm inward margin remains. No area-only zero criterion.'},'foreign_gpu_acceptance_region':{'shader_cross_literal_float32':float(np.float32(.001)),'per_row_cross_arithmetic_error_bounds': [r[1]for r in expanded_rows],'method':'Union of both three-half-plane sign branches with epsilon plus binary32/FMA cross error, intersected with each strict GPU bbox; foreign support is tested against this full region plus3mm source-transform displacement.','expanded_region_area_world':foreign_gpu_region.area,'ideal_triangle_region_area_world':new_clip.area},'foreign_possible_owner_protection':foreign,'far_target_triangle_pieces':len(far_targets),'far_actual_feature_ids_prevent_foreign_eligibility':True,'numeric_boundary_limitation':'A native band of about5mm above1262 is deliberately below the new threshold to preserve original geometry under Float32 error. Do not claim zero original-source residual or a measured building height.'}
O.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'near_north_pieces':len(targets),'far_north_pieces':len(far_targets),'foreign_owners':len(foreign),'total_rows':262}))
