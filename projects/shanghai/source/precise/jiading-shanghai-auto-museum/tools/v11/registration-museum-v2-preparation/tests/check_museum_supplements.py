#!/usr/bin/env python3
"""Bounded evidence gate controls; synthetic decoder rows are not acceptance."""
from pathlib import Path
import copy,json,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parents[1];V11=HERE.parent
sys.path.insert(0,str(HERE/'toolchain/registration'))
import contracts as c
import museum_supplements as m

def desc(p):return {'source':str(p),**c.meta(p)}
def load(p):return json.loads(Path(p).read_bytes())
results=[]
def check(name,call,reject=False):
 try:call()
 except (ValueError,KeyError,TypeError,AssertionError)as e:
  assert reject,(name,str(e));results.append({'control':name,'expected':'rejected','observed_expected':True,'reason':str(e)})
 else:
  assert not reject,'Unexpected acceptance: '+name
  results.append({'control':name,'expected':'bounded gate accepted','observed_expected':True})

review=V11/'independent-museum-review/geometry-v2-review'
structure_path=V11/'independent-museum-review/checker-v2/run-geometry-v2/actual-raw-structure.json'
structure=load(structure_path);p=load(review/'actual-preservation.json');e=load(review/'actual-repair-envelope.json')
current=c.identity(p['raw']);request={'source_freeze':desc(V11/'auto-museum/geometry-v2/source-freeze.json'),
 'source_geometry':desc(V11/'auto-museum/geometry-v2/geometry-input.json')}
target={'actual':{'source_structure_report':desc(structure_path)}}
chosen={'bounded_revision_preservation':desc(review/'actual-preservation.json')}
def preservation(v):return m.validate_preservation(v,current,structure,request,target,c.Inputs())
check('actual current preservation binding only',lambda:preservation(p))
plan,changed,added=preservation(p)
check('actual current five-part envelope binding only',lambda:m.validate_envelope(e,p,chosen,current,structure,request,target,c.Inputs(),added))
for field in ['geometry_preservation_passed','changed_panel_bounded_bottom_only','original_materials_unchanged','global_bounds_unchanged']:
 bad=copy.deepcopy(p);bad[field]=False;check('reject false '+field,lambda bad=bad:preservation(bad),True)
bad=copy.deepcopy(p);bad['previous_raw']['sha256']='0'*64;check('reject alternate historical raw',lambda:preservation(bad),True)
bad=copy.deepcopy(p);bad['actual_old_part_comparisons'][0]['new_oriented_positions_sha256']='0'*64;check('reject mismatched actual per-part position hash',lambda:preservation(bad),True)
bad=copy.deepcopy(p);bad['changed_panel_actual_comparison']['columns'][0]['actual_downward_extension_m']=.1;check('reject overextended panel underside',lambda:preservation(bad),True)
bad=copy.deepcopy(e);bad['slot_slab_clearance_results'].pop();check('reject incomplete25 slot slab pairs',lambda:m.validate_envelope(bad,p,chosen,current,structure,request,target,c.Inputs(),added),True)
bad=copy.deepcopy(e);bad['added_part_results'][0]['retained_neighbors'][0]['actual_new_part_overlap_m2']=.01;check('reject new neighbor overlap despite summary true',lambda:m.validate_envelope(bad,p,chosen,current,structure,request,target,c.Inputs(),added),True)

oldarea=load(V11/'independent-museum-review/checker-v2/run-v1/actual-pane-area-seating-v2.json')
w=copy.deepcopy(oldarea['boundary_results'][0]['actual_candidates'][0]);boundary=w['boundary']
check('old actual positive seat as numerical control only',lambda:c.need(m.valid_seat(w,boundary),'Valid old fixture rejected'))
for field,value in [('actual_joint_cell_xy_area_m2',0),('pane_facing_vertical_cosine',.01),('actual_interval_overlap_m',float('nan'))]:
 bad=copy.deepcopy(w);bad[field]=value;check('reject invalid seat '+field,lambda bad=bad:c.need(m.valid_seat(bad,boundary),'Expected numerical rejection'),True)
bad=copy.deepcopy(w);bad['actual_ordered_end_extensions_m']=[0,0];check('reject wrong support side/zero end extension',lambda:c.need(m.valid_seat(bad,boundary),'Expected support direction rejection'),True)
bad=copy.deepcopy(w);bad.pop('actual_four_facet_planes');check('reject absent actual four-facet witness',lambda:c.need(m.valid_seat(bad,boundary),'Expected missing facet rejection'),True)
bad=copy.deepcopy(w);bad['witness_xy_m']=[float('nan'),0];check('reject nonfinite actual witness coordinate',lambda:c.need(m.valid_seat(bad,boundary),'Expected nonfinite witness rejection'),True)
binding_request={**request,'source_roles':{'calibration':desc(V11/'auto-museum/geometry-v2/calibration.json')}}
actual_binding={'raw_sha256':current['sha256'],'source_freeze_sha256':request['source_freeze']['sha256'],
 'geometry_input_sha256':request['source_geometry']['sha256'],'calibration_sha256':binding_request['source_roles']['calibration']['sha256'],
 'structure_report_sha256':target['actual']['source_structure_report']['sha256']}
check('current master/area/request/rebinding source dictionaries match exact actual inputs',lambda:m.current_bindings([actual_binding]*4,current,binding_request,target))
wrong_binding={**actual_binding,'raw_sha256':'0'*64}
check('reject internally consistent wrong area/request/rebinding with current master/context',lambda:m.current_bindings([actual_binding,wrong_binding,wrong_binding,wrong_binding],current,binding_request,target),True)

# Isolated decoder-gate fixtures use actual source inventory keys/hashes but no
# GLB decode or model acceptance is inferred. All descriptors are test strings.
parts=structure['part_results'];comparisons=[{'key':r['key'],'triangles':r['triangles'],'actual_oriented_position_sha256':r['oriented_position_triangles_sha256']}for r in parts]
raw={'bytes':100,'sha256':'1'*64};assets={role:{'bytes':100,'sha256':str(i)*64}for i,role in enumerate(['raw','web','lod'],1)}
current_docs={};suite={'passed':True,'roles':{}}
for role in assets:
 report={'passed':True,'actual_finite_result':{'finite_checks_passed':True,'actual_structure_carryforward':{
  'all_present_parts_position_identical':True,'source_raw_sha256':raw['sha256'],'actual_current_asset':assets[role],
  'omitted_source_part_keys':[],'actual_part_comparisons':comparisons}}}
 current_docs[role]=report;suite['roles'][role]={'passed':True,'current_asset':assets[role],'finite_report':{'source':role},'array_manifest':{'source':role+'-array'}}
current_docs['suite']=suite
decoded={'passed':True,'web_exact_oriented_position_material_triangle_multiset':True,'modern_material_properties_preserved':True,'authored_lod':None,
 'raw_web':{'triangle_copies':528396,'normal_angle_tolerance_degrees':.05,'maximum_normal_angle_degrees':.01},
 'authored_to_compressed_lod':{'triangle_copies':528396,'normal_angle_tolerance_degrees':.05,'maximum_normal_angle_degrees':.01},
 'finite_actual_decoded_report':{'source':'suite'},'assets':{role:{**d,'materials':{'material':{'roughness':.5}}}for role,d in assets.items()}}
validated={'raw_supplemental_geometry_passed':True,'current_raw':raw,'source_freeze':{},'source_structure_report':{},'proofs':{}}
class SyntheticInputs:
 def __init__(self,docs):self.docs=docs
 def json(self,row):return self.docs[row['source']]
def transfer(docs=current_docs,dec=decoded):return m.validate_decoded_supplement_transfer(validated,dec,{'decoded_report':{}},{'lod_policy':{'mode':'compression-only'}},{'assets':assets},structure,SyntheticInputs(docs))
check('synthetic complete12378-position three-role transfer guard',lambda:transfer())
bad=copy.deepcopy(current_docs);bad['web']['passed']=False;check('reject web role false even with global decoded pass',lambda:transfer(bad),True)
bad=copy.deepcopy(current_docs);bad['lod']['actual_finite_result']['actual_structure_carryforward']['all_present_parts_position_identical']=False;check('reject LOD position carryforward false',lambda:transfer(bad),True)
bad=copy.deepcopy(current_docs);bad['lod']['actual_finite_result']['actual_structure_carryforward']['omitted_source_part_keys']=[comparisons[0]['key']];check('reject any Museum LOD omission',lambda:transfer(bad),True)
bad=copy.deepcopy(decoded);bad['raw_web']['maximum_normal_angle_degrees']=.2;check('reject decoded normal drift',lambda:transfer(dec=bad),True)
bad=copy.deepcopy(decoded);bad['assets']['web']['materials']['material']['roughness']=.6;check('reject changed decoded actual material',lambda:transfer(dec=bad),True)

baseline=V11/'registration-evidence-revision-v2/toolchain'
for rel in ['decode_core.mjs','check_decoded_modern.mjs','run_decoded_finite.py','package_modern.py','modern_contract.py',
 'registration/report_adapters.py','registration/contracts.py','registration/geometry_supplements.py','registration/public_dependency_compat.py',
 'engine/finite_checks.py','engine/audit_raw_structure.py','engine/modern_mesh.py','engine/run_finite_checks.py']:
 assert (HERE/'toolchain'/rel).read_bytes()==(baseline/rel).read_bytes(),rel
report={'schema':'museum-supplement-evidence-gate-controls-v1','controls_passed':True,'control_count':len(results),'controls':results,
 'current_actual_preservation':desc(review/'actual-preservation.json'),'current_actual_envelope':desc(review/'actual-repair-envelope.json'),
 'unchanged_core_math_decoder_bridge_library_bytes':True,'actual_model_registration_performed':False,'actual_current_area_or_decoded_executed':False,
 'synthetic_decoder_fixture_is_not_actual_evidence':True,'native_accepted':False,'browser_accepted':False}
with(HERE/'tests/museum-supplement-control-results-v2.json').open('x')as f:f.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({'controls':len(results),'passed_in_gate_scope':True,'actual_model_registration':False}))
