"""Narrow registrar guards. Synthetic delivery fixtures are NOT model evidence."""
from pathlib import Path
import sys,json,copy,tempfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;V11=ROOT.parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'toolchain/registration'))
from contracts import Inputs,descriptor
from geometry_supplements import validate_raw_supplements,validate_decoded_supplement_transfer

def main():
 source=V11/'pao-yue-kong-library/geometry-v2';review=V11/'independent-modern-review/library-geometry-v2'
 raw=V11/'pao-yue-kong-library-run-geometry-v2/raw/minhang-baoyugang-library.glb'
 request={'source_freeze':descriptor(source/'source-freeze.json'),'source_geometry':descriptor(source/'geometry-input.json'),
          'source_roles':{'calibration':descriptor(source/'calibration.json')}}
 target={'id':'minhang-baoyugang-library','status':'pending','registration_allowed':False,'actual':{
   'source_structure_report':descriptor(review/'actual-raw-structure.json'),'geometry_supplements':{
    'bounded_revision_preservation':descriptor(review/'actual-revision-preservation.json'),
    'horizontal_pane_seating':descriptor(review/'actual-horizontal-pane-seating-v2.json'),
    'colonnade_cap_clearance':descriptor(review/'actual-colonnade-cap-clearance-v2.json')}}}
 package={'assets':{'raw':descriptor(raw)}};structure=json.loads((review/'actual-raw-structure.json').read_bytes())
 results=[]
 def record(name,action,reject=False):
  try:action()
  except (ValueError,KeyError,TypeError,AttributeError) as exc:
   if not reject:raise
   results.append({'control':name,'expected':'reject','observed':'rejected','reason':str(exc)});return
  if reject:raise AssertionError('Invalid control accepted: '+name)
  results.append({'control':name,'expected':'valid narrow contract','observed':'passed control, not registration'})
 with tempfile.TemporaryDirectory(prefix='supplement-controls-',dir=HERE) as tmp:
  tmp=Path(tmp);counter=0
  def save(obj):
   nonlocal counter
   counter+=1;p=tmp/f'SYNTHETIC-CONTROL-{counter}.json';p.write_text(json.dumps(obj,allow_nan=False)+'\n');return descriptor(p)
  def raw_call(t=None,r=None):return validate_raw_supplements(r or request,t or target,package,structure,Inputs())
  valid=raw_call();record('actual existing raw three-proof validation only',raw_call)
  def mutate_raw(name,fn):
   t=copy.deepcopy(target);key=name;obj=json.loads(Path(t['actual']['geometry_supplements'][key]['source']).read_bytes());fn(obj)
   t['actual']['geometry_supplements'][key]=save(obj);return lambda:raw_call(t)
  missing=copy.deepcopy(target);del missing['actual']['geometry_supplements']['colonnade_cap_clearance']
  record('missing distinct cap proof',lambda:raw_call(missing),True)
  wrong=copy.deepcopy(target);wrong['actual']['geometry_supplements']['horizontal_pane_seating']=target['actual']['source_structure_report']
  record('structure PASS cannot replace seating proof',lambda:raw_call(wrong),True)
  for value in [False,1]:record('seating true domain '+str(value),mutate_raw('horizontal_pane_seating',lambda x,v=value:x.update(horizontal_seating_passed=v)),True)
  record('stale old raw seating',mutate_raw('horizontal_pane_seating',lambda x:x['asset_identity'].update(raw=descriptor(V11/'pao-yue-kong-library-run-v1/raw/minhang-baoyugang-library.glb'))),True)
  req=copy.deepcopy(request);req['source_freeze']=descriptor(V11/'pao-yue-kong-library/source-freeze.json')
  record('wrong frozen source revision',lambda:raw_call(r=req),True)
  record('missing one actual pane',mutate_raw('horizontal_pane_seating',lambda x:x['pane_results'].pop()),True)
  record('positive label with air-gap witness',mutate_raw('horizontal_pane_seating',lambda x:x['pane_results'][0]['largest_actual_joint_witness'].update(actual_endpoint_separation_m=.02)),True)
  record('cap remains coplanar',mutate_raw('colonnade_cap_clearance',lambda x:x['actual_columns'][0].update(actual_vertical_clearance_m=0)),True)
  record('cap contact lacks positive area',mutate_raw('colonnade_cap_clearance',lambda x:x['actual_columns'][0]['actual_column_deck_contact'].update(witness_cell_area_m2=0)),True)
  record('revision count changed',mutate_raw('bounded_revision_preservation',lambda x:x.update(actual_changed_parts=264)),True)
  alternate=tmp/'SYNTHETIC-NOT-A-MODEL-OLD-RAW.txt';alternate.write_text('synthetic internally coherent wrong historical baseline')
  alt_desc=descriptor(alternate);revision=json.loads((review/'actual-revision-preservation.json').read_bytes())
  old_structure=json.loads(Path(revision['old_structure_report']['file']).read_bytes());old_structure['asset_identity']['raw']=alt_desc
  alt_structure=save(old_structure);revision['old_asset_identity']['raw']=alt_desc;revision['old_structure_report']=alt_structure
  allow=json.loads(Path(revision['repair_allowlist']['file']).read_bytes());allow['old_raw_sha256']=alt_desc['sha256'];allow['independently_selected_from_actual_structure']=alt_structure
  revision['repair_allowlist']=save(allow);alt=copy.deepcopy(target);alt['actual']['geometry_supplements']['bounded_revision_preservation']=save(revision)
  record('internally coherent but wrong frozen historical baseline',lambda:raw_call(alt),True)
  record('unbound supplement checker bytes',mutate_raw('colonnade_cap_clearance',lambda x:x['checker_files'][0].update(sha256='0'*64)),True)
  corrupted=copy.deepcopy(target);obj=json.loads((review/'actual-colonnade-cap-clearance-v2.json').read_bytes());d=save(obj);Path(d['source']).write_text('{}\n');corrupted['actual']['geometry_supplements']['colonnade_cap_clearance']=d
  record('file bytes differ from descriptor',lambda:raw_call(corrupted),True)
  # Synthetic decoded contract controls only: no GLB/decoder/native is run,
  # no ready target or package record exists, and fixture files are deleted.
  t=copy.deepcopy(target);p=copy.deepcopy(package);r=copy.deepcopy(request)
  for role in ['web','lod','authored_lod']:
   f=tmp/f'SYNTHETIC-NOT-GLB-{role}.txt';f.write_text('synthetic decoder guard only '+role)
   if role=='authored_lod':t['actual']['authored_lod']=descriptor(f)
   else:p['assets'][role]=descriptor(f)
  material_names={row['material'] for row in structure['part_results']};mats={name:{'opacity':1.0,'roughness':.5} for name in material_names}
  protected_material=next(row['material'] for row in structure['part_results'] if row['key']==valid['required_retained_part_keys'][0])
  comparisons=[{'key':x['key'],'triangles':x['triangles'],'actual_oriented_position_sha256':x['oriented_position_triangles_sha256']} for x in structure['part_results']]
  decoded={'passed':True,'web_exact_oriented_position_material_triangle_multiset':True,'modern_material_properties_preserved':True,
    'assets':{role:{**p['assets'][role],'triangles':structure['triangles'],'materials':copy.deepcopy(mats)} for role in ['raw','web','lod']},
    'authored_lod':{**t['actual']['authored_lod'],'triangles':structure['triangles'],'materials':copy.deepcopy(mats)},
    'raw_web':{'triangle_copies':structure['triangles'],'normal_angle_tolerance_degrees':.05,'maximum_normal_angle_degrees':.01},
    'authored_to_compressed_lod':{'triangle_copies':structure['triangles'],'normal_angle_tolerance_degrees':.05,'maximum_normal_angle_degrees':.01}}
  roles={};suite={'passed':True,'roles':roles}
  for role in ['raw','web','lod','authored_lod']:
   asset=t['actual']['authored_lod'] if role=='authored_lod' else p['assets'][role]
   f={'passed':True,'actual_finite_result':{'finite_checks_passed':True,'actual_structure_carryforward':{
     'all_present_parts_position_identical':True,'source_raw_sha256':p['assets']['raw']['sha256'],
     'actual_current_asset':asset,'actual_part_comparisons':copy.deepcopy(comparisons),'omitted_source_part_keys':[]}}}
   roles[role]={'current_asset':asset,'finite_report':save(f),'array_manifest':save({'SYNTHETIC_ONLY':True})}
  decoded['finite_actual_decoded_report']=save(suite);r['decoded_report']=save({'SYNTHETIC_ONLY':True})
  def transfer(d=None):return validate_decoded_supplement_transfer(valid,d or decoded,r,t,p,structure,Inputs())
  record('synthetic exact four-role retained geometry transfer control',transfer)
  for name,fn in [
    ('normal drift exceeds independent delivery policy',lambda d:d['raw_web'].update(maximum_normal_angle_degrees=.06)),
    ('normal tolerance relaxed',lambda d:d['authored_to_compressed_lod'].update(normal_angle_tolerance_degrees=.1)),
    ('material changes despite position equality',lambda d:d['assets']['web']['materials'][protected_material].update(opacity=.2)),
    ('global actual triangle material equality absent',lambda d:d.update(web_exact_oriented_position_material_triangle_multiset=False))]:
   d=copy.deepcopy(decoded);fn(d);record(name,lambda d=d:transfer(d),True)
  def suite_variant(fn):
   d=copy.deepcopy(decoded);s=copy.deepcopy(suite);fn(s);d['finite_actual_decoded_report']=save(s);return lambda:transfer(d)
  record('missing actual LOD role',suite_variant(lambda s:s['roles'].pop('lod')),True)
  protected=valid['required_retained_part_keys'][0]
  def role_variant(fn):
   def mutate(s):
    data=json.loads(Path(s['roles']['lod']['finite_report']['source']).read_bytes());fn(data)
    s['roles']['lod']['finite_report']=save(data)
   return suite_variant(mutate)
  def remove_part(data):
   carry=data['actual_finite_result']['actual_structure_carryforward'];carry['actual_part_comparisons']=[x for x in carry['actual_part_comparisons'] if x['key']!=protected];carry['omitted_source_part_keys'].append(protected)
  record('protected supplement-dependent part removed',role_variant(remove_part),True)
  record('actual decoded finite failure',role_variant(lambda d:d['actual_finite_result'].update(finite_checks_passed=False)),True)
  record('stale decoded current asset',role_variant(lambda d:d['actual_finite_result']['actual_structure_carryforward']['actual_current_asset'].update(sha256='0'*64)),True)
 out={'schema':'modern-supplement-registration-guard-controls-v1','controls_passed':True,'controls':results,
      'actual_registration_performed':False,'synthetic_decoded_fixtures_are_not_acceptance':True,'temporary_fixtures_deleted':True,
      'native_accepted':False,'browser_accepted':False,'files':[descriptor(Path(__file__)),descriptor(ROOT/'toolchain/registration/geometry_supplements.py')]}
 output=HERE/'supplement-guard-results.json';output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'controls':len(results),'output':str(output),'actual_registration_performed':False}))

if __name__=='__main__':main()
