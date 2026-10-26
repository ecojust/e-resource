#!/usr/bin/env python3
"""Freeze the new minimal Museum tool selection; no model ready/registration."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parent;V11=ROOT.parent;TOOLS=ROOT/'toolchain'
OLD=V11/'registration-evidence-revision-v2/toolchain'
EXPECTED='f1f71403e3191c838e71ec0af4c26cab48720d4aaeb8f11d0052f938ccd7cd26'
def desc(p):
 p=Path(p).resolve()
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return {'source':str(p),'bytes':p.stat().st_size,'sha256':h}
def load(p):return json.loads(Path(p).read_text())
def main():
 original=desc(OLD/'tool-source-freeze.json');assert original['sha256']==EXPECTED
 rows={};changed=[];allowed={'registration/public_dependency_allowlist.json','registration/prepare_registration.py'}
 for row in load(OLD/'tool-source-freeze.json')['files']:
  source=Path(row['source']);assert desc(source)==row
  if source.is_relative_to(OLD):
   relative=source.relative_to(OLD);path=TOOLS/relative
   if desc(path)['sha256']!=row['sha256']:
    assert relative.as_posix()in allowed;changed.append(relative.as_posix())
  else:path=source
  rows[str(path)]=desc(path)
 assert set(changed)==allowed
 extras=[ROOT/n for n in ['README.md','prepare_source_compat.py','baseline-lock.json','source-allowlist.patch','freeze_tool_revision.py',
  'independent-review-record.json','tests/check_source_compat.py','tests/source-control-results.json',
  'tests/check_museum_supplements.py','tests/museum-supplement-control-results-v2.json']]
 extras += [TOOLS/'registration'/n for n in ['supplement_dispatch.py','museum_supplements.py']]
 adaptation=ROOT/'request-adaptation/source-freeze.json';extras.append(adaptation)
 for row in load(adaptation)['files']:
  p=Path(row.get('source',row.get('file')));assert {k:desc(p)[k]for k in ['bytes','sha256']}=={k:row[k]for k in ['bytes','sha256']};extras.append(p)
 museum=V11/'independent-museum-review'
 for name in ['preservation-checker-freeze-v1.json','envelope-checker-freeze-v1.json','area-bounded-entry-freeze-v1.json']:
  freeze=museum/'geometry-v2-review'/name;extras.append(freeze)
  for row in load(freeze)['files']:
   p=Path(row.get('source',row.get('file')));assert {k:desc(p)[k]for k in ['bytes','sha256']}=={k:row[k]for k in ['bytes','sha256']};extras.append(p)
 extras += [museum/'checker-v2'/n for n in ['audit_raw_structure.py','modern_mesh.py','finite_checks.py','run_finite_checks.py']]
 extras += [museum/'run_bounded.py',museum/'resource-runner-freeze-v1.json']
 for p in extras:rows[str(p.resolve())]=desc(p)
 source_controls=load(ROOT/'tests/source-control-results.json');supplement_controls=load(ROOT/'tests/museum-supplement-control-results-v2.json');review=load(ROOT/'independent-review-record.json')
 assert source_controls['source_contract_controls_passed']is True and source_controls['control_count']==25
 assert supplement_controls['controls_passed']is True and supplement_controls['control_count']==26
 assert review['blocking_findings_remaining']==[]
 oldrules=load(OLD/'registration/public_dependency_allowlist.json');newrules=load(TOOLS/'registration/public_dependency_allowlist.json')
 assert newrules['models']['minhang-baoyugang-library']==oldrules['models']['minhang-baoyugang-library']
 assert newrules['models']['jiading-shanghai-auto-museum']['source_file_count']==59
 assert newrules['models']['jiading-shanghai-auto-museum']['special_files']==oldrules['models']['jiading-shanghai-auto-museum']['special_files']
 output={'schema':'modern-packaging-tool-source-freeze-v11','status':'frozen','revision':'museum-geometry-v2-exact59-and-four-supplements-v3',
  'files':[rows[k]for k in sorted(rows)],'original_tool_freeze':original,
  'intended_model':'jiading-shanghai-auto-museum','museum_source_freeze':desc(V11/'auto-museum/geometry-v2/source-freeze.json'),
  'published_library_keeps_original_tool_freeze':original,'changed_original_tool_files':sorted(changed),
  'new_registrar_modules':['registration/supplement_dispatch.py','registration/museum_supplements.py'],
  'core_decoder_bridge_and_math_unchanged':True,'single_master_probe_protocol_unchanged':True,
  'source_compatibility_controls':desc(ROOT/'tests/source-control-results.json'),
  'supplement_gate_controls':desc(ROOT/'tests/museum-supplement-control-results-v2.json'),
  'independent_tool_review':desc(ROOT/'independent-review-record.json'),'source_dependencies_only':True,
  'generated_model_assets':False,'actual_registration_performed':False,'model_ready_created':False,'native_accepted':False,'browser_accepted':False,
  'scope':'New exact Museum tool selection only. Actual current model reports must independently pass. No Library/published source, original tool, geometry, evidence or acceptance flag was changed.'}
 p=TOOLS/'tool-source-freeze.json'
 with p.open('x')as f:f.write(json.dumps(output,indent=2)+'\n')
 print(json.dumps({'freeze':desc(p),'files':len(rows),'changed':sorted(changed)}))

if __name__=='__main__':main()
