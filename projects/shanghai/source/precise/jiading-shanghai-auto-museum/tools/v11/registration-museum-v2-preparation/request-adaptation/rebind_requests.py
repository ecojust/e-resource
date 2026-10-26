#!/usr/bin/env python3
"""Bind existing finite questions to actual v2 only after independent preservation.

This script makes questions, never geometry/contact answers. The original6102
questions and source files are read-only. Every changed question is mapped.
"""
from pathlib import Path
import argparse,copy,hashlib,json,struct

HERE=Path(__file__).resolve().parent
V11=HERE.parents[1]
OLD=V11/'independent-museum-review/requests-v1'
AUTHOR=V11/'auto-museum/geometry-v2'
MODEL='jiading-shanghai-auto-museum'
AUTHOR_SHA='5acf7f82a27d7ccfb4b7d4ca0c6e13d98cb381c8409cc3fa0a5697c01fe0a45a'
CURRENT_RAW_SHA='fcaf6c3ec778a4edc6d4c335aedea02472b8ddff24013d2e555f09e949eebd5f'
OLD_RAW_SHA='5c2f93f9b66f75771587ed532928d02dbc3d6960fc1c0804d37e498faa9a969d'
GROUPS=['01-slots-entry','02-curtain-local-seating','03-roof-finite-joints','04-stair-ramp-rails','05-louvre-chains']
OLD_COUNTS=[50,5114,10,564,364]
NEW_COUNTS=[50,5114,11,568,364,7]
WORLD={'origin_enu_m':[0.,0.,0.],'axes_enu':[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]}

def need(ok,message):
 if not ok:raise ValueError(message)
def read(p):return json.loads(Path(p).read_bytes())
def desc(p):
 p=Path(p).absolute();need(not any(q.is_symlink()for q in [p,*p.parents]),'Symlink input')
 need(p.is_file() and 0<p.stat().st_size<100000000,'Regular bounded input required')
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return {'file':str(p),'bytes':p.stat().st_size,'sha256':h}
def identity(d):return {k:d[k]for k in ['bytes','sha256']}
def bound(d):
 p=Path(d.get('file',d.get('source','')));need(p.is_absolute(),'Absolute evidence path required')
 need(identity(desc(p))==identity(d),'Evidence changed: '+str(p));return p
def qsha(q):return hashlib.sha256(json.dumps(q,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def validate_context(raw_path,structure_path,preservation_path):
 raw,structure_meta,preservation_meta=map(desc,[raw_path,structure_path,preservation_path])
 source=desc(AUTHOR/'source-freeze.json');need(source['sha256']==AUTHOR_SHA,'Wrong author revision')
 need(raw['sha256']==CURRENT_RAW_SHA,'Wrong actual v2 raw')
 structure=read(structure_path);p=read(preservation_path);source_doc=read(AUTHOR/'source-freeze.json')
 need(structure['schema']=='modern-actual-raw-structure-v1' and structure['structure_passed'] is True and
      structure['model_id']==MODEL and structure['parts']==12378,'Actual current complete structure required')
 need(identity(structure['asset_identity']['raw'])==identity(raw) and
      identity(structure['frozen_source_manifest'])==identity(source),'Structure/raw/source binding differs')
 need(p['schema']=='museum-actual-geometry-v2-preservation-v1','Wrong preservation schema')
 for flag in ['geometry_preservation_passed','all_non_allowlisted_parts_position_normals_materials_identical',
              'exact_changed_and_added_key_sets','changed_panel_bounded_bottom_only','original_materials_unchanged','global_bounds_unchanged']:
  need(p.get(flag) is True,'Actual preservation prerequisite failed: '+flag)
 need(p.get('unchanged_part_count')==12372 and p.get('changed_part_count')==1 and p.get('added_part_count')==5
      and p.get('removed_part_keys')==[] and p.get('unexpected_part_keys')==[],'Preservation inventory differs')
 for name,expected in [('raw',raw),('structure_report',structure_meta),('source_freeze',source)]:
  need(identity(p[name])==identity(expected),'Preservation current binding differs: '+name);bound(p[name])
 need(p['previous_raw']['sha256']==OLD_RAW_SHA and source_doc['baseline_rejected_raw_sha256']==OLD_RAW_SHA,
      'Historical baseline cannot be replaced')
 for name in ['previous_raw','previous_structure_report','previous_source_freeze','approved_change_plan']:bound(p[name])
 change=read(AUTHOR/'change-scope.json');approved=read(bound(p['approved_change_plan']))
 need(approved['schema']=='museum-geometry-v2-approved-independent-change-plan-v1' and
      identity(approved['source_change_scope'])==identity(desc(AUTHOR/'change-scope.json')) and
      identity(approved['source_freeze'])==identity(source) and
      identity(approved['baseline_raw'])==identity(p['previous_raw']) and
      identity(approved['baseline_structure'])==identity(p['previous_structure_report']) and
      identity(approved['baseline_source_freeze'])==identity(p['previous_source_freeze']) and
      p['previous_raw']['sha256']==change['baseline_raw']['sha256'],'Frozen bounded change plan differs')
 for name in ['source_change_scope','source_freeze','baseline_raw','baseline_structure','baseline_source_freeze']:bound(approved[name])
 compact=lambda key:json.dumps(key,ensure_ascii=False,separators=(',',':'))
 need(set(approved['allowed_changed_old_part_keys'])=={compact(k)for k in change['planned_allowed_changed_part_keys']} and
      set(approved['allowed_added_part_keys'])=={compact(k)for k in change['planned_allowed_added_part_keys']} and
      set(p['modified_old_part_keys'])==set(approved['allowed_changed_old_part_keys']) and
      set(p['added_part_keys'])==set(approved['allowed_added_part_keys']), 'Actual/independent/authored change key sets differ')
 frozen={r['file']:r for r in source_doc['files']}
 for name in ['geometry-input.json','calibration.json','change-scope.json','repair-inputs.json']:
  need(identity(desc(AUTHOR/name))==identity(frozen[name]),'Frozen dependency changed: '+name)
 binding={'structure_report_sha256':structure_meta['sha256'],'raw_sha256':raw['sha256'],
          'source_freeze_sha256':source['sha256'],'geometry_input_sha256':desc(AUTHOR/'geometry-input.json')['sha256'],
          'calibration_sha256':desc(AUTHOR/'calibration.json')['sha256']}
 need(structure['source_geometry_sha256']==binding['geometry_input_sha256'] and structure['calibration_sha256']==binding['calibration_sha256'],
      'Actual current source extras differ')
 return structure,binding,{'raw':raw,'structure':structure_meta,'preservation':preservation_meta,'source_freeze':source}

def transform(originals,parts):
 bylabel={r['label']:r for r in parts};need(len(bylabel)==len(parts)==12378,'Unique current labels required')
 def sel(label):need(label in bylabel,'Missing actual part: '+label);return {'key':bylabel[label]['key'],'expected_count':1}
 def selectors(labels):return [sel(x)for x in labels]
 replacements={
 'curtain/layer-1/bay-161/glass-pane-1':'repair/entry-small-pane-bottom-seat',
 'curtain/layer-4/bay-002/glass-pane-0':'north-spine/structural-C-segment-10',
 'curtain/layer-4/bay-003/glass-pane-0':'north-spine/structural-C-segment-10',
 'curtain/layer-4/bay-027/glass-pane-0':'north-spine/structural-C-segment-0',
 'curtain/layer-4/bay-028/glass-pane-0':'north-spine/structural-C-segment-0',
 'curtain/layer-5/bay-002/glass-pane-0':'repair/fifth-floor-west-pane-seat',
 'curtain/layer-5/bay-028/glass-pane-0':'repair/fifth-floor-east-pane-seat'}
 output=[];mapping=[];seen_replacements=set()
 for group,doc,count in zip(GROUPS,originals,OLD_COUNTS):
  need(len(doc['checks'])==count and doc['source_binding']['raw_sha256']==OLD_RAW_SHA,'Original suite/count differs')
  checks=[]
  for old in doc['checks']:
   new=copy.deepcopy(old);mapped=[new];reason='unchanged question bytes; current actual source binding only'
   pane=old['id'].removesuffix('/bottom-frame-or-floor-local-joint')
   if old['id'].endswith('/bottom-frame-or-floor-local-joint') and pane in replacements:
    new['right_selectors']=selectors([replacements[pane]]);seen_replacements.add(pane)
    reason='Explicit repaired or independently observed actual bottom support role; original pane/thresholds retained'
   if old['id']=='roof/lower-components-to-upper-deck':
    need(len(old['left_selectors'])==2,'Original roof component group differs')
    new['id']='roof/main-lower-component-to-upper-deck'
    new['left_selectors']=selectors(['roof/lower-curved-continuous-underlayer/component-1'])
    extra=copy.deepcopy(old);extra['id']='roof/north-small-component-to-new-ties'
    extra['left_selectors']=selectors(['roof/lower-curved-continuous-underlayer'])
    extra['right_selectors']=selectors(['repair/north-roof-concealed-tie-west','repair/north-roof-concealed-tie-east'])
    need({s['key']for q in [new,extra]for s in q['left_selectors']}=={s['key']for s in old['left_selectors']},'Roof partition lost a component')
    mapped=[new,extra];reason='Partition exact original two components: big to unchanged deck; north island through actual new ties'
   for flight in range(1,5):
    if old['id']==f'stair/flight-{flight}/all-rail-posts-to-stringers':
     terminals={sel(f'stair/flight-{flight}/open-rail-{side}/post-2-1')['key']for side in [0,1]}
     new['id']=f'stair/flight-{flight}/nonlanding-rail-posts-to-stringers'
     new['left_selectors']=[s for s in old['left_selectors']if s['key']not in terminals]
     extra=copy.deepcopy(old);extra['id']=f'stair/flight-{flight}/upper-terminal-rail-posts-to-own-landing'
     extra['left_selectors']=[s for s in old['left_selectors']if s['key']in terminals]
     extra['right_selectors']=selectors([f'stair/landing-{flight}'])
     need(len(new['left_selectors'])==6 and len(extra['left_selectors'])==2,'Original stair partition differs')
     mapped=[new,extra];reason='Exact eight original posts partitioned6+2; two upper terminal posts tested against own unchanged landing'
   for q in mapped:
    need({k:v for k,v in old.items()if k not in ['id','left_selectors','right_selectors']}==
         {k:v for k,v in q.items()if k not in ['id','left_selectors','right_selectors']},'Non-role policy/frame/sample mutation')
   checks.extend(mapped);mapping.append({'original_group':group,'original_id':old['id'],'original_question_sha256':qsha(old),
    'new_ids':[q['id']for q in mapped],'new_question_sha256':[qsha(q)for q in mapped],'disposition':reason})
  output.append(checks)
 need(seen_replacements==set(replacements),'Seven specific pane role corrections not complete')
 links=[('repair/entry-small-pane-bottom-seat','entry/continuous-head'),
        ('repair/fifth-floor-west-pane-seat','interior-estimate/fifth-floor-plate'),
        ('repair/fifth-floor-east-pane-seat','interior-estimate/fifth-floor-plate')]
 for side in ['west','east']:
  links.extend([(f'repair/north-roof-concealed-tie-{side}','roof/lower-curved-continuous-underlayer'),
                (f'repair/north-roof-concealed-tie-{side}','roof/upper-deep-cantilever-underlayer')])
 added=[{'id':f'new-support-chain/{i+1}/{left}/to/{right}','kind':'support_each','left_selectors':selectors([left]),
         'right_selectors':selectors([right]),'frame':copy.deepcopy(WORLD),'minimum_embed_m':1e-6,
         'maximum_cells_per_pair':20000,'contact_mode':'positive_volume'}for i,(left,right)in enumerate(links)]
 output.append(added)
 need([len(x)for x in output]==NEW_COUNTS and len(mapping)==6102,'Expected6114 question accounting differs')
 flat=[q for checks in output for q in checks];need(len(flat)==len({q['id']for q in flat})==6114,'New IDs not unique')
 return output,mapping

def frame_bounds(part,frame):
 lo,hi=part['bounds_enu_m'];corners=[[x,y,z]for x in [lo[0],hi[0]]for y in [lo[1],hi[1]]for z in [lo[2],hi[2]]]
 points=[[sum((p[i]-frame['origin_enu_m'][i])*axis[i]for i in range(3))for axis in frame['axes_enu']]for p in corners]
 return [[min(p[i]for p in points)for i in range(3)],[max(p[i]for p in points)for i in range(3)]]

def all_opaque(raw,parts,slots):
 with Path(raw).open('rb')as stream:
  magic,version,length=struct.unpack('<4sII',stream.read(12));size,kind=struct.unpack('<II',stream.read(8))
  need(magic==b'glTF' and version==2 and kind==0x4e4f534a and size<8000000,'Actual GLB JSON header differs')
  gltf=json.loads(stream.read(size))
 materials={m['name']:m for m in gltf['materials']};need(len(materials)==len(gltf['materials'])==23,'Actual material inventory differs')
 glass=[]
 for name,m in materials.items():
  need(m.get('alphaMode','OPAQUE')=='OPAQUE','Material alpha classification differs')
  factor=m.get('extensions',{}).get('KHR_materials_transmission',{}).get('transmissionFactor',0)
  if factor>0:glass.append({'material':name,'actual_transmission_factor':factor})
 need(len(glass)==4,'Intended glazing material inventory differs')
 opaque=[p for p in parts if p['material']not in {g['material']for g in glass}]
 need(all(p['material']in materials for p in parts),'Unknown actual material')
 added={p['key']for p in opaque if p['label'].startswith('repair/')};need(len(added)==5,'All five actual repair parts must enter opaque broad phase')
 checks=[];broad=[]
 for slot in range(1,6):
  q=copy.deepcopy(next(q for q in slots if q['id']==f'north-slot-{slot}/between-transoms/actual-opaque-wrapper-clear'))
  need(q['kind']=='ray_intervals' and q['expect']=='clear' and q['points_uv_m']==[[0.,24.],[0.,26.],[0.,28.],[0.,30.]],'Original20 ray stations changed')
  retained=[];excluded=[]
  for p in opaque:
   low,high=frame_bounds(p,q['frame']);hit=any(low[0]<=uv[0]<=high[0] and low[1]<=uv[1]<=high[1] and low[2]<=q['depth_range_m'][1] and high[2]>=q['depth_range_m'][0]for uv in q['points_uv_m'])
   (retained if hit else excluded).append(p['key'])
  need(retained and len(retained)+len(excluded)==len(opaque),'Broad phase coverage incomplete')
  q['id']=f'north-slot-{slot}/all-opaque-finite-false-backing-probes';q['selectors']=[{'key':k,'expected_count':1}for k in retained];checks.append(q)
  broad.append({'slot':slot,'actual_opaque_part_count':len(opaque),'selected_actual_opaque_keys':retained,'excluded_actual_opaque_keys':excluded,
                'five_new_part_keys_checked':sorted(added),'five_new_parts_selected':sorted(added&set(retained)),
                'exclusion_basis':'Conservative transformed actual current AABBs disjoint from every original finite probe segment. Selection is not a ray result.'})
 return checks,{'actual_json_chunk_bytes':size,'material_count':23,'excluded_intended_transmitting_materials':glass,'conservative_broad_phase':broad}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--structure',type=Path,required=True)
 ap.add_argument('--preservation',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 out=a.output.absolute();need(out.is_relative_to(HERE) and not out.exists(),'Use new output directory under request-adaptation')
 lock=read(HERE/'adaptation-input-lock.json')
 for d in lock['original_requests']:bound(d)
 for d in lock['mathematics_dependencies']:bound(d)
 structure,binding,context=validate_context(a.raw,a.structure,a.preservation)
 originals=[read(OLD/(name+'.requests.json'))for name in GROUPS]
 output,mapping=transform(originals,structure['part_results'])
 opaque,broad=all_opaque(a.raw,structure['part_results'],output[0])
 out.mkdir();paths={}
 def write(name,document):
  p=out/name
  with p.open('x')as stream:stream.write(json.dumps(document,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
  return desc(p)
 def document(checks,scope):return {'schema':'modern-finite-requests-v1','state':'READY_FOR_ACTUAL_AUDIT','model_id':MODEL,
   'source_binding':binding,'allowed_omitted_part_keys':[],'checks':checks,'input_descriptors':context,
   'scope':scope,'actual_mesh_queries_executed':False,'appearance_or_browser_acceptance':False}
 for name,checks in zip([*GROUPS,'06-new-support-chains'],output):
  paths[name]=write(name+'.requests.json',document(checks,'Actual v2 questions with explicit old-question role mapping; original mathematics and thresholds retained.'))
 paths['complete-6114']=write('complete-6114.requests.json',document([q for checks in output for q in checks],'All6114 finite questions; area seating supplements remain independently required.'))
 doc=document(opaque,'Twenty original finite slot rays conservatively select every potentially intersecting current opaque part, including all5 new repair parts. Not whole-aperture/global clearance.');doc.update(broad)
 paths['all-opaque-slots']=write('all-opaque-slots.requests.json',doc)
 mapping_meta=write('question-mapping.json',{'schema':'museum-v2-complete-question-mapping-v1','old_question_count':6102,'new_question_count':6114,
  'old_question_mappings':mapping,'new_support_question_ids':[q['id']for q in output[-1]],'original_failures_preserved':True})
 manifest=write('rebinding-manifest.json',{'schema':'museum-v2-request-rebinding-manifest-v1','questions_prepared':True,'actual_checks_executed':False,
  'context':context,'source_binding':binding,'old_request_lock':desc(HERE/'adaptation-input-lock.json'),'generator':desc(__file__),
  'requests':paths,'mapping':mapping_meta,'old_question_count':6102,'new_question_count':6114,'pane_boundary_questions':5114,
  'all_opaque_finite_rays':20,'model_accepted':False,'browser_accepted':False})
 print(json.dumps({'manifest':manifest,'questions':6114,'area_questions':5114,'all_opaque_rays':20,'actual_checks_executed':False}))

if __name__=='__main__':main()
