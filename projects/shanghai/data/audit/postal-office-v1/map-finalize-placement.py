"""Derive Postal placement/collision from the frozen final GLBs; writes only scratch.

Run map-decode-delivered.mjs and map-analyze-delivered.py for raw,web,lod first.
The12 verified thin courtyard-floor triangles are walkable paving, not obstacles.
"""
import argparse,datetime,hashlib,importlib.util,json,math,os
from pathlib import Path
import shapely
from shapely.geometry import shape,mapping,Point
from shapely.ops import transform

P=Path(os.environ.get('POSTAL_REPO','/workspace/e-resource')).resolve()/'projects/shanghai'
D=Path(os.environ.get('POSTAL_MAPPING_WORK','/workspace/shanghai-postal-mapping')).resolve()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest',type=Path,required=True)
args=parser.parse_args()
def read(name):
 path=D/name
 if not path.exists():path=P/'data/audit/postal-office-v1'/name
 return json.loads(path.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
author=read('footprint-contract.json');a=author['anchor']
rows=read('delivered-projection-preflight.json')['records']
assert {r['variant'] for r in rows}=={'raw','web','lod'}
manifest=json.loads(args.manifest.read_text());assert manifest['id']==author['model_id']
for row in rows:
 asset=manifest['assets']['full' if row['variant']=='web' else row['variant']]
 assert all(asset[key]==row['asset_binding'][key] for key in ['sha256','bytes','triangles'])
 actual_path=args.manifest.parent/asset['file']
 assert actual_path.stat().st_size==asset['bytes'] and sha(actual_path)==asset['sha256'],'Delivered asset changed after actual projection'
 assert row['walkable_courtyard_floor_exclusion']['triangle_count']==12
 assert row['full_projection_reused_from'] is None,'Final acceptance must freshly project final assets'
full=shapely.union_all([shape(r['full_projection_local_enu']) for r in rows])
ground=shapely.union_all([shape(r['ground_geometry_local_enu']) for r in rows])
court=shape(author['courtyard_canopy_plan_local_enu'])
contexts={r['localId']:r for r in read('context-features.json') if r['localId']!=1959}
protected=[shape(r['geometry_local_enu']) for r in contexts.values()]
native={r['properties']['name']:shape(r['geometry']) for r in read('source-profiles.geojson')['features'] if r['properties']['name'] in ['near_3148','near_814','near_1780']}
source_profiles={r['properties']['name']:shape(r['geometry']) for r in read('source-profiles.geojson')['features']}
float_mask=shape(read('clip-geometry-review.json')['source_mask_float32_union_geometry_local_enu'])
for name in ['near_1959','far_1959']:native['retained_joint_'+name]=source_profiles[name].difference(float_mask)
protected+=list(native.values())
trials=[];candidates=[]
# Simplify first, then restore a modest conservative wall/column margin.
# Every trial must cover actual geometry, not just pass a vertex count.
for tolerance,padding in [(0.125,.12),(.13,.12),(.14,.12),(.16,.14),(.16,.16),(.20,.18)]:
 collision=ground.simplify(tolerance,preserve_topology=True).buffer(padding,join_style=2)
 parts=[collision] if collision.geom_type=='Polygon' else list(collision.geoms)
 ring_counts=[[len(p.exterior.coords),*[len(h.coords) for h in p.interiors]] for p in parts]
 missing=ground.difference(collision).area
 overlap=max(collision.intersection(p).area for p in protected)
 beyond=collision.difference(ground.buffer(.35,join_style=2)).area
 passes=collision.is_valid and collision.geom_type=='Polygon' and all(max(c)<=256 and len(c)<=32 for c in ring_counts) and sum(map(sum,ring_counts))<=4096 and missing<1e-9 and overlap<1e-9 and beyond<1e-9
 trials.append({'simplify_before_padding_m':tolerance,'padding_m':padding,'closed_ring_point_counts':ring_counts,'valid':collision.is_valid,'uncovered_actual_structure_m2':missing,'maximum_retained_source_overlap_m2':overlap,'outside_035m_structural_margin_m2':beyond,'area_m2':collision.area,'passed':passes})
 if passes:candidates.append((collision.area,tolerance,padding,collision))
assert candidates,'No valid conservative collision fits existing production limits; revise geometry independently rather than relaxing validators'
_,tolerance,padding,collision=min(candidates,key=lambda x:x[0])
assert collision.covers(ground)
k=6371008.8*math.cos(math.radians(a['lat']));log0=math.log(math.tan(math.pi/4+math.radians(a['lat'])/2))
def wgs(x,y,z=None):return a['lng']+math.degrees(x/k),math.degrees(2*math.atan(math.exp(log0+y/k))-math.pi/2)
geometry=mapping(transform(wgs,collision))
spec=importlib.util.spec_from_file_location('postal_production_catalog_builder',P/'tools/build_candidate_city_integrations.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
builder.checked_geometry(geometry,'Postal final structural collision',collision=True)
checks=[]
for owner,row in contexts.items():
 p=shape(row['geometry_local_enu']);entry={'owner_local_id':owner,'source_id':row['source_id'],'full_model_overlap_m2':p.intersection(full).area,'collision_overlap_m2':p.intersection(collision).area,'full_model_distance_m':p.distance(full),'collision_distance_m':p.distance(collision)}
 assert entry['full_model_overlap_m2']<1e-8 and entry['collision_overlap_m2']<1e-8
 checks.append(entry)
nativechecks=[]
for name,p in native.items():
 entry={'profile':name,'full_model_overlap_m2':p.intersection(full).area,'collision_overlap_m2':p.intersection(collision).area,'full_model_distance_m':p.distance(full),'collision_distance_m':p.distance(collision)}
 assert entry['full_model_overlap_m2']<1e-8 and entry['collision_overlap_m2']<1e-8
 nativechecks.append(entry)
f=author['facade_uv_frame'];o=f['origin_enu_m'];u=f['u_axis_enu'];v=f['v_axis_enu']
def enu(x,y):return o[0]+u[0]*x+v[0]*y,o[1]+u[1]*x+v[1]*y
probes=[]
for name,x,y,expected in [('south-wing',35,10,True),('north-wing',35,53,True),('east-wing',84,32,True),('tower-base',85,8,True),('covered-courtyard-center',32,32,False),('covered-courtyard-west',6,32,False),('south-street',35,-3,False)]:
 point=Point(*enu(x,y));assert collision.covers(point)==expected,(name,'collision')
 if not expected:assert not any(p.covers(point) for p in protected),(name,'retained source')
 probes.append({'name':name,'local_uv_m':[x,y],'local_xy_m':[point.x,point.y],'wgs84':list(wgs(point.x,point.y)),'expected':'building' if expected else None,'actual_collision_contains':expected,'method':'Final structural collision; verified12-triangle courtyard paving excluded, walls/columns/U base retained.','not_public_access_certification':True})
point=Point(55,20);assert not collision.covers(point) and not any(p.covers(point) for p in protected)
probes.append({'name':'east-street','local_xy_m':[55,20],'wgs84':list(wgs(55,20)),'expected':None,'actual_collision_contains':False,'not_public_access_certification':True})
clip=read('clip-preflight.json');clipgeometry=read('clip-geometry-review.json');scope=read('source-scope-verification.json')
source=shape(author['source_geometry_local_enu']);sourceclip=shape(author['provisional_display_clip']['geometry_local_enu'])
bounds={'min':[min(r['bounds_glb']['min'][i] for r in rows) for i in range(3)],'max':[max(r['bounds_glb']['max'][i] for r in rows) for i in range(3)]}
method=f'Actual final indexed raw/web/LOD triangles with complete transforms and material ownership. Exclude only12 dark-stone courtyard-floor box triangles per asset, z0..0.16m; preserve U base z0..0.18m, facade/column geometry. Clip all remaining triangles to z[0,2], union their structural projections, simplify{tolerance:g}m then pad{padding:g}m with mitre joins. Final valid polygon covers every actual structural projection and stays within0.35m of actual structure; no source footprint, canopy or full-site hull fallback.'
contract={'id':author['model_id'],'lng':a['lng'],'lat':a['lat'],'heading':0,'scale':1,'altitude':0,'local_axes':author['author_axes']+'; GLB east/up/south','owner':author['owner'],'source_feature_ids':author['source_feature_ids'],'source_limit_geometry':author['source_geometry_wgs84'],'replacement_geometry':clip['replacement_geometry'],'collision_geometry':geometry,'bounds_glb':bounds,'model_geometry_sha256':{r['variant']:r['asset_binding']['sha256'] for r in rows},'model_manifest_sha256':sha(args.manifest),'height_m':bounds['max'][1],'height_estimated':True,'overviewBearing':-45,'overviewPitch':45,'overviewZoom':18.4,'maxDistance':450,'lod_switch_in_m':550,'lod_switch_out_m':700,'navigation':{'listed':False,'status':'Overview-only bounded main-building exterior; no accepted interior route.'},'placement':{'status':'estimated','note':'按邮政总局主楼源定位；南东柱廊、钟塔与北侧红砖外观按照片规整，院内弧罩依据2010照片作估计，非现状测绘。'},'partial_model':True,'listed_place_scope_is_partial':True,'model_scope':'上海邮政总局地图主源1959内的历史主楼与东南钟塔，含依据2010内院照片估计的弧形网罩；西侧相接源3148、完整院内陈设和未核完整名录范围不并入。','registration_note':'Only owner1959 is locally clipped. Retain the western source3148 and a narrow1959 joint strip because shared near meshes lack per-vertex IDs. The neighboring source is not assigned an unsupported construction date. Canopy dimensions/position are estimates from2010 reference and undated private aerial form; no present-day survey claim.','collision_method':method,'collision_navigability_limit':'Courtyard paving is visible ground and excluded from building obstacles; structural low walls/columns remain. A free collision probe does not certify a public or indoor walking route.','ground_collision_excludes_overhead_projection':True,'ground_collision_excludes_walkable_courtyard_floor':True,'near_group_owner_isolation_required':True,'expected_replacement_triangle_count':6,'expected_global_clip_triangle_count':307,'expected_global_clip_capacity':scope['state']['triangleLimit'],'source_retained_area_runtime_m2':source.difference(sourceclip).area,'source_retained_fraction':source.difference(sourceclip).area/source.area,'source_retained_shader_float32_area_m2':clipgeometry['source1959_retained_joint_area_m2'],'source_retained_actual_native_projection_area_m2':next(r['remaining_m2'] for r in clipgeometry['rows'] if r['profile']=='near_1959'),'source_retained_actual_native_projection_scope':'Thin shared western joint intentionally retained; whole3148 is protected in near/far/Standard/Depth/Distance scope. See actual source-mask Float32 geometry audit.'}
summary={'schema':'postal-final-structural-placement-v1','status':'final_actual_raw_web_lod_verified','method':method,'actual_structural_low_union_area_m2':ground.area,'collision_area_m2':collision.area,'padding_area_m2':collision.difference(ground).area,'uncovered_actual_structural_low_area_m2':ground.difference(collision).area,'walkable_floor_exclusions':[{ 'variant':r['variant'],**r['walkable_courtyard_floor_exclusion']} for r in rows],'authored_courtyard_plan_area_m2':court.area,'actual_structural_projection_inside_courtyard_area_m2':ground.intersection(court).area,'collision_inside_courtyard_area_m2':collision.intersection(court).area,'courtyard_added_collision_padding_m2':collision.difference(ground).intersection(court).area,'courtyard_free_of_structural_collision_area_m2':court.difference(collision).area,'collision_beyond_actual_structure_035m_collar_m2':collision.difference(ground.buffer(.35,join_style=2)).area,'collision_geometry_local_enu':mapping(collision),'closed_ring_point_counts':[[len(collision.exterior.coords),*[len(h.coords) for h in collision.interiors]]],'collision_trials':trials,'model_ground_bindings':[{k:v for k,v in r.items() if k not in ['full_projection_local_enu','ground_geometry_local_enu']} for r in rows],'retained_source_checks':checks,'retained_actual_near_checks':nativechecks,'ground_probes':probes,'production_checked_geometry_collision_passed':True,'limits':'Authored dimensions/hidden details remain estimates. Courtyard floor is a simple unexhibited surface; not an indoor tour or survey.'}
qa=read('qa-map-input.json');qa['ground_collision_status']=summary['status'];qa['ground_probes']=probes
clip['status']='final_source_scope_and_actual_model_geometry_verified';clip['remaining']='Browser pixels and public HTTP verification recorded separately.'
references=[]
for name in ['source-register.json','documentary-review.json','photo-review.json','footprint-contract.json']:
 p=P/'source/precise/hongkou-general-post-office'/name
 references.append({'repository_path':'projects/shanghai/'+p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
evidence=[]
for name in ['source-bindings.json','source-scope-verification.json','clip-geometry-review.json','source-profiles.geojson','source-replay.json','delivered-projection-preflight.json','final-projection-execution.json','map-decode-delivered.mjs','map-analyze-delivered.py','map-finalize-placement.py','map-verify-collision.mjs']:
 p=P/'data/audit/postal-office-v1'/name
 evidence.append({'repository_path':'projects/shanghai/'+p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
report={'schema':'postal-map-and-ground-contract-v1','candidate_id':author['model_id'],'baseline_commit':author['baseline_commit'],'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':summary['status'],'source_bindings':[{k:v for k,v in r.items() if k!='private_path'} for r in read('source-bindings.json')],'reference_context_bindings':references,'mapping_evidence_bindings':evidence,'identity_crosscheck':read('osm-identity-crosscheck.json'),'source_clip_review':clip,'source_scope_verification':'data/audit/postal-office-v1/source-scope-verification.json','float32_clip_geometry_verification':'data/audit/postal-office-v1/clip-geometry-review.json','coordinate_frame':read('initial-local-frame.json'),'authoring_footprint_contract':'source/precise/hongkou-general-post-office/footprint-contract.json','actual_geometry_and_collision':summary,'camera_obstruction_precheck':read('camera-plan-preflight.json'),'runtime_validation':{'ground_probes':probes,'native_roof_probes':qa['actual_source_roof_probes'],'retained_joint_roof_probe':qa['source_joint_retained_roof_probe'],'near_groups':scope['state']['ownerScopedSources'],'final_model_geometry_verified':True,'production_collision_validation_passed':True},'proposed_placement_contract':contract,'third_party_photo_content_embedded':False}
for name,value in [('final-placement-contract.json',contract),('final-model-placement-review.json',summary),('ground-probes.json',{'ground_probes':probes,'status':summary['status']}),('qa-map-input.json',qa),('clip-preflight.json',clip),('footprint-review.json',report)]:
 (D/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'structural_ground_m2':ground.area,'collision_m2':collision.area,'ring_counts':summary['closed_ring_point_counts'],'floor_triangles_excluded_per_asset':12,'ground_probes':len(probes),'model_height_m':bounds['max'][1]},ensure_ascii=False))
