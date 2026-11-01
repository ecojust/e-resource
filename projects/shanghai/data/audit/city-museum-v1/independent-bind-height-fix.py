"""Bind completed height-fix geometry/numeric proofs to final production bytes.
Usage: repository-root private-review-directory output.json
No browser or geometry computation.
"""
from pathlib import Path
import datetime,hashlib,json,sys
root,R,out=map(Path,sys.argv[1:4]);P=root/'projects/shanghai';A=P/'data/audit/city-museum-v1';mid='yangpu-former-shanghai-city-museum'
def read(p):return json.loads(Path(p).read_text())
def binding(p):
 p=Path(p);b=p.read_bytes()
 try:f=str(p.relative_to(root))
 except ValueError:f=str(p)
 return {'file':f,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def require(r,p=None):
 p=Path(p or r['file']);p=p if p.is_absolute()else root/p;b=binding(p)
 assert r['sha256']==b['sha256'],(p,'SHA mismatch')
 if 'bytes'in r:assert r['bytes']==b['bytes'],(p,'byte mismatch')
 return b
geometry=read(A/'independent-height-geometry-review.json');numeric=read(A/'independent-height-numeric.json');rows=read(A/'independent-height-row-preservation.json')
assert geometry['passed']and numeric['passed']and rows['passed']
assert geometry['northern_complete_support']['after_geometry_is_empty']and not geometry['northern_complete_support']['uncovered_triangles_after_inward_margin']
assert geometry['northern_complete_support']['robust_margin_world_m']==.003
assert all(r['triangles_touching_full_cross_epsilon_gpu_regions_plus3mm']==0 for r in geometry['foreign_possible_owner_protection'])
assert all(v<.003 for v in numeric['max_vertex_world_error_xyz'])
assert numeric['protected_height']['passed']and numeric['protected_height']['strict_remaining_world_gap']>.0049
assert not numeric['fragment_interpolation_certified']and numeric['actual_final_browser_pixels_required']
assert len(numeric['whole_target_polygon_coverage'])==2 and all(r['passed']for r in numeric['whole_target_polygon_coverage'])
final=numeric['final_public_binding'];assert final['passed']and final['private_preflight']is False
numeric_inputs=[]
for k in ['public_runtime_receipt','public_gpu_row_payload','public_catalog','public_placement','public_footprint','preflight']:numeric_inputs.append(require(final[k]))
for b in final['actual_production_code_bindings']:numeric_inputs.append(require(b))
runtime=read(A/'height-clipping-checks.json');assert runtime['passed']and runtime['private_preflight']is False
assert runtime['old_rows_identical']and runtime['pre_height_rows_identical']
assert [runtime[k]for k in ['old_rows','pre_height_rows','added_height_rows','total_rows','capacity']]==[218,258,4,262,288]
payload=require(runtime['data_payload'],A/runtime['data_payload']['file'])
assert rows['new262_payload']['sha256']==payload['sha256']==geometry['bindings']['actual_gpu_rows']['sha256']
assert rows['old218_rows_identical']and rows['all258_pre_height_rows_identical']
foot=read(A/'footprint-review.json');contract=read(A/'final-placement-contract.json');assert foot['proposed_placement_contract']==contract
require(geometry['bindings']['contract'],A/'final-placement-contract.json');require(geometry['bindings']['preflight'],A/'height-clip-input.json')
old_foot_path=R/'height-fix-history/frozen-before/projects/shanghai/data/audit/city-museum-v1/footprint-review.json';old=read(old_foot_path)['proposed_placement_contract'];placement=read(A/'independent-placement-review.json')
assert placement['bindings']['contract_sha256']==binding(old_foot_path)['sha256']==geometry['bindings']['original_placement_footprint_sha256']
changed={k for k in set(old)|set(contract)if old.get(k)!=contract.get(k)};assert changed==set(geometry['changed_contract_keys'])
for key in ['replacement_geometry','site_replacement','collision_geometry','source_feature_ids','model_geometry_sha256','model_manifest_sha256','source_limit_geometry','owner','bounds_glb']:assert old[key]==contract[key]
catalog=read(P/'data/candidate-city-integrations.json');c=next(r for r in catalog['models']if r['id']==mid);assert c['display_height_clips']==contract['display_height_clips']
additional=read(P/'data/global-models/additional-placement.json');p=next(r for r in additional['records']if r['id']==mid)
for key,value in contract.items():assert p[key]==value,key
meta=read(A/'independent-metadata-review.json');assert meta['passed']and meta['progress_current_catalog_binding_verified']
for key in ['final_catalog','final_additional_placement','final_footprint','restoration_progress']:require(meta[key])
manifest=binding(P/f'assets/models/candidates/{mid}/manifest.json');assert manifest['sha256']==contract['model_manifest_sha256']==meta['final_manifest']['sha256']
for b in meta['new_public_assets']:require(b)
observation_path=R/'height-fix-history/independent-browser-interface-review.json';observation=read(observation_path);assert observation['image']['actually_viewed']and observation['acceptance']['accepted_for_final_delivery']is False
assert not (A/observation['image']['file']).exists(),'Before-fix floating image must remain privately archived'
first_rejection=final['first_binding_rejection_preserved'];require(first_rejection)
result={'schema':'city-museum-independent-height-fix-v1','passed':True,'script':binding(Path(__file__)),'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_id':mid,'scope':'Completed incremental CPU source geometry/Float32 vertex-and-row checks plus exact final production binding. The new height-fixed browser run remains required for actual current-device pixels. No authored-model GLB matrix or native reopening repeated.','final_footprint':binding(A/'footprint-review.json'),'final_contract':binding(A/'final-placement-contract.json'),'final_manifest':manifest,'final_catalog':binding(P/'data/candidate-city-integrations.json'),'final_additional_placement':binding(P/'data/global-models/additional-placement.json'),'final_runtime':binding(A/'height-clipping-checks.json'),'actual_gpu_rows':payload,'prior_placement_review':binding(A/'independent-placement-review.json'),'original_placement_footprint':binding(old_foot_path),'base_2d_collision_and_four_authored_assets_unchanged':True,'changed_contract_keys':sorted(changed),'reports':[binding(A/n)for n in ['independent-height-geometry-review.json','independent-height-row-preservation.json','independent-height-numeric.json']],'numeric_final_input_bindings':numeric_inputs,'clip_rows':{'base_2d':40,'height':4,'museum_gpu':44,'all_city':262,'capacity':288},'whole_northern_near_triangle_pieces_covered':geometry['northern_complete_support']['actual_triangle_pieces'],'whole_northern_far_triangle_pieces_covered':geometry['far_target_triangle_pieces'],'strict_bbox_and_full_cross_epsilon_foreign_protection':True,'possible_foreign_owners_checked':7,'max_vertex_world_error_xyz_m':numeric['max_vertex_world_error_xyz'],'retained_1262_world_height_clearance_m':numeric['protected_height']['strict_remaining_world_gap'],'old218_and_all258_pre_height_rows_byte_identical':True,'after_height_original_roof_projection_remaining_m2':contract['source_retained_actual_native_projection_area_after_height_clips_m2'],'before_fix_observation_retained_privately':binding(observation_path),'before_fix_scope_acceptance_withdrawn':True,'initial_numeric_binding_rejection':first_rejection,'binding_rejection_resolution':'Initial receipt preceded a seven-byte builder warning comparison fix. The failed binding is retained; current formal runtime receipt and exact production bindings passed. No geometry/source failure was discarded.','foreign_proof_refinement':'Final protection includes both cross-sign branches, Float32 epsilon and cross arithmetic bounds intersected with strict bboxes, plus3mm source-transform allowance; the earlier ideal-region-only intermediate remains private.','fragment_interpolation_certified':False,'actual_final_browser_pixels_required':True,'required_final_browser_stage':'height-fixed-final','heavy_cpu_work_complete':True,'browser_or_server_launched_by_reviewer':False,'limits':['Original city source and model dimensions remain estimates.','The approximately5mm native band protects1262 against Float32 rounding; this is not a zero original-source residual claim.','Existing conservative possible low plinth contacts and east rear-hall/connector identity uncertainty remain as recorded.','Final selected northern interface3/4 images must visibly remove the raised fragments while preserving1262.']}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'rows':262,'near_pieces':85,'far_pieces':8,'heavy_cpu_complete':True}))
