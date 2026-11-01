"""Final museum placement; independent triangles and immutable source geometry.
Usage: review-dir immutable-city-input placement-contract.json output.json
"""
from pathlib import Path
import gzip,hashlib,json,math,sys
from shapely.geometry import shape,mapping,Polygon,Point
from shapely.ops import transform,unary_union
R,M,C,O=map(Path,sys.argv[1:5]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
document=json.loads(C.read_text());contract=document.get('proposed_placement_contract',document);report=json.loads((R/'independent-geometry-review.json').read_text());package=json.loads((R/'independent-packaging-binding.json').read_text());original=json.loads((R/'independent-original-city-projection.json').read_text());frame=json.loads((M/'initial-local-frame.json').read_text())['anchor']
assert contract['id']==report['modelId']=='yangpu-former-shanghai-city-museum'
assert [contract[k]for k in ['heading','scale','altitude']]==[0,1,0]
assert [contract['lng'],contract['lat']]==[frame['lng'],frame['lat']]
assert contract['model_geometry_sha256']=={key:report['assets'][role]['sha256']for key,role in [('raw','raw'),('web','full'),('lod','lod')]}
assert contract['model_manifest_sha256']==package['final_manifest']['sha256']
k=6371008.8*math.cos(math.radians(frame['lat']));psi=math.asinh(math.tan(math.radians(frame['lat'])))
def local(lng,lat,z=None):return k*math.radians(lng-frame['lng']),k*(math.asinh(math.tan(math.radians(lat)))-psi)
table=json.loads(gzip.decompress((M/'macro-feature-table.json.gz').read_bytes()));sources={r['localId']:transform(local,shape(r['geometry']))for r in table['features']};assert len(sources)==2324;targets={1860,1931};main=sources[1860]
masks={1860:transform(local,shape(contract['replacement_geometry'])),1931:transform(local,shape(contract['site_replacement']['geometry']))};mask=unary_union(list(masks.values()))
assert contract['owner']['feature_local_id']==1860 and contract['site_replacement']['owner']['feature_local_id']==1931
for i,m in masks.items():assert m.is_valid
clip=json.loads((M/'clip-candidate.json').read_text());assert sha(M/'clip-candidate.json')==original['bindings']['clip_candidate_sha256']
for i,key in [(1860,'main'),(1931,'site')]:assert masks[i].symmetric_difference(shape(clip[key+'_mask_geometry_local_enu'])).area<1e-5
collision=transform(local,shape(contract['collision_geometry']));assert collision.is_valid
parts=list(collision.geoms)if collision.geom_type=='MultiPolygon'else[collision];counts=[[len(p.exterior.coords),*[len(r.coords)for r in p.interiors]]for p in parts];assert len(parts)<=32 and max(map(len,counts))<=32 and max(n for r in counts for n in r)<=256 and sum(map(sum,counts))<=4096
occupancies={};assetrows=[]
for role in ['raw','full','lod']:
 a=report['assets'][role];p=R/'independent-occupancy'/(a['sha256']+'.json');o=json.loads(p.read_text());assert o['asset_sha256']==a['sha256'] and o['triangle_payload_sha256']==a['actualTrianglesENU']['sha256'];f=shape(o['full_projection']['geometry_local_xy']);low=shape(o['standing_slab']['geometry_local_xy']);assert f.is_valid and low.is_valid;occupancies[role]=(f,low);missed=low.difference(collision).area;assert missed<1e-5,(role,missed)
 overlap=[]
 for i,s in sources.items():
  if i in targets:continue
  x=f.intersection(s).area;y=low.intersection(s).area
  if max(x,y)>1e-7:overlap.append({'owner':i,'full_m2':x,'low_m2':y})
 assert not overlap,overlap
 assetrows.append({'role':role,'asset_sha256':a['sha256'],'occupancy_sha256':sha(p),'full_area_m2':f.area,'low_area_m2':low.area,'low_outside_collision_m2':missed,'source1860_uncovered_by_full_m2':main.difference(f).area,'foreign_sources_checked':2322,'nonzero_foreign_model_overlap':overlap})
lowunion=unary_union([v[1]for v in occupancies.values()]);lowparts=list(lowunion.geoms)if lowunion.geom_type=='MultiPolygon'else[lowunion]
holes=[Polygon(r)for p in lowparts for r in p.interiors if Polygon(r).area>100];assert len(holes)==1 and holes[0].difference(main).area<1e-5
enclosed=unary_union(holes);filled=lowunion.union(enclosed);padding=filled.buffer(.03,join_style=2).simplify(.025,preserve_topology=True);protected=unary_union([sources[510],sources[1262]]);expected=padding.difference(protected);difference=expected.symmetric_difference(collision).area;assert difference<1e-4,difference
assert lowunion.intersection(protected).area<1e-7 and lowunion.difference(expected).area<1e-5
assert enclosed.difference(collision).area<1e-5
foreign_collision=[]
for i,s in sources.items():
 if i in targets:continue
 x=collision.intersection(s).area;y=mask.intersection(s).area
 if max(x,y)>1e-7:foreign_collision.append({'owner':i,'collision_m2':x,'display_mask_m2':y})
assert not foreign_collision,foreign_collision
controls=[]
for label,point,closed in [('north courtyard left',[-4,16],False),('north courtyard east',[12,16],False),('south courtyard left',[-4,-16],False),('south courtyard east',[12,-16],False),('retained north connector',[3,16],False),('retained south connector',[3,-16],False),('central enclosed room',[-14,0],True),('north wing enclosed room',[20,28],True),('rear hall enclosed room',[15,0],True),('west entry exterior',[-22,-.8],False)]:
 p=Point(point);a=lowunion.covers(p);b=collision.covers(p);c=any(f.covers(p)for f,l in occupancies.values());assert not a and b==closed and c==closed,(label,a,b,c);controls.append({'label':label,'point_local_xy':point,'actual_low_covered':a,'collision_covered':b,'full_projection_covered':c})
neighbors=[]
for context in json.loads((R/'independent-neighbor-context.json').read_text())['records']:
 fr=context['frame'];assert[fr[x]for x in ['heading','scale','altitude']]==[0,1,0];kk=6371008.8*math.cos(math.radians(fr['lat']));ps=math.asinh(math.tan(math.radians(fr['lat'])))
 def convert(x,y,z=None):return local(fr['lng']+math.degrees(x/kk),math.degrees(math.atan(math.sinh(ps+y/kk))))
 env=transform(convert,Polygon(context['actual_full_projection_convex_hull']));overlap=max(f.intersection(env).area for f,l in occupancies.values());assert overlap<1e-7 and collision.intersection(env).area<1e-7;neighbors.append({'id':context['id'],'old_full_asset_sha256':context['old_full_asset_sha256'],'full_distance_to_actual_containing_hull_m':min(f.distance(env)for f,l in occupancies.values()),'collision_distance_m':collision.distance(env),'full_overlap_m2':overlap})
roadcontext=json.loads((R/'independent-road-context.json').read_text());assert roadcontext['frame']==frame;roads=[]
for w in roadcontext['records']:
 line=shape(w['geometry_local_xy']);length=line.intersection(collision).length;shoulder=line.buffer(.38).intersection(collision).area;assert length<1e-7 and shoulder<1e-7;roads.append({'id':w['id'],'highway':w['tags']['highway'],'actual_low_distance_m':lowunion.distance(line),'collision_distance_m':collision.distance(line),'centerline_overlap_length_m':length,'shoulder038_overlap_m2':shoulder})
assert len(roads)==3
assert[contract[x]for x in ['expected_replacement_triangle_count','expected_global_clip_triangle_count','expected_global_clip_capacity']]==[40,258,288]
roof_contacts=[]
for r in original['near_roof_projections']:
 if r['owner']in targets:continue
 roof=shape(r['geometry_local_xy']);area=max(f.intersection(roof).area for f,l in occupancies.values());roof_contacts.append({'owner':r['owner'],'actual_high_roof_projected_overlap_m2':area,'source_roof_elevation_estimate_m':r['source_height_estimate_m'],'new_model_max_elevation_m':max(a['actualBoundsModelENU']['max'][2]for a in report['assets'].values()if'actualBoundsModelENU'in a),'note':'High original roof projection can overlap new low contact details. This is not a ground/source-footprint intrusion or a claim to recover original structural face ownership.'})
contact_doc=json.loads((R/'independent-near-contacts.json').read_text());assert contact_doc['passed'];low_contacts=[]
for r in contact_doc['records']:
 env=shape(r['possible_low_geometry_local_xy']);low_contacts.append({'owner':r['owner'],'compatible_owner_triangles':r['compatible_triangle_count'],'ambiguous_compatible_triangles':r['compatible_but_ambiguous_triangles'],'new_low_overlap_with_possible_original_low_m2':lowunion.intersection(env).area,'new_full_overlap_with_possible_original_low_m2':max(f.intersection(env).area for f,l in occupancies.values()),'collision_overlap_with_possible_original_low_m2':collision.intersection(env).area,'scope':'Conservative upper bound at shared interfaces, not a proven recovered foreign-face owner. This low-level contact is distinct from high roof projection and is explicitly retained.'})
out={'schema':'city-museum-independent-final-placement-v1','passed':True,'candidate_id':contract['id'],'method':'Actual independent full/LOD triangles, exact z0..2 clipping/union, separate source-contained conservative interior fill, precisely reviewed collision padding with only retained-source padding removed. Display masks checked independently from collision.','bindings':{'contract_sha256':sha(C),'geometry_report_sha256':sha(R/'independent-geometry-review.json'),'packaging_binding_sha256':sha(R/'independent-packaging-binding.json'),'original_city_review_sha256':sha(R/'independent-original-city-projection.json'),'neighbor_context_sha256':sha(R/'independent-neighbor-context.json'),'road_context_sha256':sha(R/'independent-road-context.json'),'script_sha256':sha(Path(__file__))},'frame':frame,'assets':assetrows,'collision':{'area_m2':collision.area,'polygons':len(parts),'closed_ring_point_counts':counts,'total_ring_points':sum(map(sum,counts)),'actual_low_union_m2':lowunion.area,'conservative_enclosed_room_hole_gross_m2':enclosed.area,'conservative_enclosed_room_fill_net_m2':enclosed.difference(lowunion).area,'fill_count':len(holes),'fill_geometry_local_xy':mapping(enclosed),'buffer_m':.03,'simplify_m':.025,'protected_source_padding_removed_m2':padding.intersection(protected).area,'physical_low_geometry_removed_m2':lowunion.difference(expected).area,'independent_policy_symmetric_difference_m2':difference,'foreign_sources_checked':2322,'nonzero_foreign_overlap':foreign_collision},'ground_controls':controls,'retained_detailed_neighbors':neighbors,'road_centerlines_and_shoulders':roads,'high_original_roof_contacts':roof_contacts,'possible_original_low_contacts':low_contacts,'possible_original_low_contacts_report_sha256':sha(R/'independent-near-contacts.json'),'display_mask':{'new_triangles':40,'global_triangles':258,'capacity':288,'original_source1860_residual_m2':main.difference(masks[1860]).area,'original_source1931_residual_m2':sources[1931].difference(masks[1931]).area,'residual_interfaces_intentional_for_neighbor_preservation':True},'limits':'Complete b2-012 historical reconstruction, exact rear-hall fabric and connector identity are not certified. No indoor walkthrough. Source city heights are estimates. Shared near interfaces have nonzero conservative possible low contact envelopes and require separate final browser views; no zero-residual or zero-original-low-contact claim.'}
O.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'collision_points':sum(map(sum,counts)),'low_m2':lowunion.area,'closed_fill_m2':enclosed.area,'roads':len(roads),'neighbors':len(neighbors)}))
