#!/usr/bin/env python3
"""Freeze an explicit public source allowlist; never generate or accept models."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent

PUBLIC_FILES=[
 'README.md','DESIGN.md','LICENSE-CODE.txt','MODEL-LICENSE.md','requirements.txt',
 'build_model.py','curves.py','solids.py','render_previews.py','run_root.py',
 'source_preflight.py','prepare_sign_outlines.py','prepare_audit_questions.py','freeze_author_source.py',
 'common/photo_architecture.py','geometry-input.json','calibration.json','semantic-contract.json',
 'references/photo-register.json','references/source-register.json','references/ATTRIBUTION.md',
 'references/root-photo-inspection.json','references/identity-source-proof.json',
 'references/mapping-report.json','references/independent-source-review-record.json',
 'references/museum-sign-outlines.json','references/SIGN-FONT-LICENSE.txt',
 'references/commons-57659417.jpg','references/commons-57659421.jpg','references/commons-57659431.jpg',
 'references/commons-21052347.jpg','references/commons-20856157.jpg',
 'orientation-review/orientation-review.json','orientation-review/osm-orientation-context.png',
 'orientation-review/osm-water-context-retrieval.json','orientation-review/osm-water-context.osm',
 'orientation-review/research-lock.json','design/plot_design.py',
 'design/plan-elevation-v2.png','design/curve-input-report-v2.json','design/audit-question-inputs.json',
 'design/math-development-log.json','design/source-preflight-attempt-1.json',
 'design/source-preflight-attempt-2-error.json','design/source-preflight-attempt-3.json',
 'design/source-preflight-final.json',
 'prepare_repairs_from_v1.py','check_local_repairs.py','repair-inputs.json','change-scope.json','REPAIR-DESIGN.md',
 'design/source-preflight-geometry-v2.json','design/local-repair-preflight.json',
 'history/source-freeze-v1.json','history/repair-inputs-attempt-1.json','history/repair-inputs-attempt-2.json',
 'history/local-repair-preflight-attempt-1.json','history/local-repair-preflight-attempt-2.json',
 'design/full-camera-source-review.json',
]

def descriptor(name):
 p=HERE/name
 if p.is_symlink() or not p.is_file():raise ValueError('Missing or linked public dependency: '+name)
 data=p.read_bytes()
 if len(data)>=100_000_000:raise ValueError('Single-file limit exceeded: '+name)
 return {'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def main():
 output=HERE/'source-freeze.json'
 if output.exists():raise ValueError('Source is already frozen; create a new revision for changes')
 qa=json.loads((HERE/'design/source-preflight-geometry-v2.json').read_text())
 if not qa['passed_in_source_math_scope'] or qa['full_model_generated']:raise ValueError('Wrong source check scope/status')
 if qa['calibration_sha256']!=descriptor('calibration.json')['sha256']:raise ValueError('Source check does not bind current calibration')
 for row in qa['source_files_syntax_checked']:
  if descriptor(row['file'])['sha256']!=row['sha256']:raise ValueError('Source changed since preflight: '+row['file'])
 local=json.loads((HERE/'design/local-repair-preflight.json').read_text())
 if not local['source_scope_passed'] or local['full_model_generated']:raise ValueError('Wrong local repair evidence scope')
 for field,name in [('builder_sha256','build_model.py'),('calibration_sha256','calibration.json'),('repair_inputs_sha256','repair-inputs.json')]:
  if local[field]!=descriptor(name)['sha256']:raise ValueError('Local repair evidence source drift: '+name)
 files=[descriptor(n) for n in PUBLIC_FILES]
 c=json.loads((HERE/'calibration.json').read_text())
 data={'schema':'shanghai-auto-museum-raw-source-freeze-v11','id':'jiading-shanghai-auto-museum',
  'revision':'raw-source-geometry-v2','author':'agent','model_revision':c['model_revision'],'files':files,
  'public_source_total_bytes':sum(d['bytes'] for d in files),
  'largest_public_file_bytes':max(d['bytes'] for d in files),
  'source_only':True,'full_model_generated':False,'native_visual_passed':False,'browser_passed':False,
  'raw_generation_entry':'run_root.py --raw-output NEW_DIRECTORY',
  'native_entry':'Blender4.3.2 -b -t2 --python render_previews.py -- --glb ACTUAL_RAW --output NEW_DIRECTORY',
  'runtime_dependencies':{'python':'3.12','numpy':'2.3.5','shapely':'2.2.0','native_blender':'4.3.2','optional_design_plot':'matplotlib','optional_sign_source_regeneration':'fonttools plus sourcefonthash inoutlineJSON'},
  'raw_runtime_requires_network_or_MAIN_or_system_font':False,
  'excluded_from_public_payload':['root-concept-v1-snapshot historicalrootreview','Allrun/output/native/browser folders','Unlicensed official/manufacturer/TJAD fullHTML,PDF,photos','Uncurated researchimages','Python__pycache__'],
  'baseline_rejected_raw_sha256':'5c2f93f9b66f75771587ed532928d02dbc3d6960fc1c0804d37e498faa9a969d',
  'declared_change_scope_sha256':descriptor('change-scope.json')['sha256'],
  'source_geometry_sha256':descriptor('geometry-input.json')['sha256'],
  'limits':c['limits'],'model_acceptance':'Pending actual raw, native, decoded semantic geometry and browser review; no automatic acceptance.'}
 output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'manifest':descriptor('source-freeze.json'),'files':len(files),'total_bytes':data['public_source_total_bytes'],'model_generated':False},indent=2))

if __name__=='__main__':main()
