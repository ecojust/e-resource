#!/usr/bin/env python3
"""Freeze this new tool revision after controls/review. Never make a target ready."""
from pathlib import Path
import json,hashlib

ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent/'packaging-preparation';TOOLS=ROOT/'toolchain'
def meta(p):
 p=Path(p).resolve();return {'source':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 original=json.loads((BASE/'tool-source-freeze.json').read_bytes());rows={}
 allowed={'registration/contracts.py','registration/prepare_registration.py'}
 for item in original['files']:
  old=Path(item['source']);assert meta(old)==item,'Original frozen input changed: '+str(old)
  if old.is_relative_to(BASE):
   relative=old.relative_to(BASE);p=TOOLS/relative
   if str(relative) not in allowed:assert p.read_bytes()==old.read_bytes(),'Unapproved tool changed: '+str(relative)
  else:p=old
  rows[str(p.resolve())]=meta(p)
 extras=[TOOLS/'registration'/name for name in ['public_dependency_compat.py','public_dependency_allowlist.json','geometry_supplements.py']]
 extras += [ROOT/name for name in ['README.md','baseline-lock.json','source-layout-input-lock.json','combined-registration.patch','source-layout.patch','supplement-evidence.patch','freeze_tool_revision.py','independent-review-record.json','tests/test_supplement_guards.py','tests/supplement-guard-results.json','tests/integration-control-results.json']]
 extras += [ROOT.parent/'independent-modern-review'/name for name in ['audit_library_revision_preservation_v2.py','audit_glass_horizontal_seating.py','audit_library_colonnade_caps.py','library-supplemental-checker-freeze-v2.json']]
 for p in extras:rows[str(p.resolve())]=meta(p)
 controls=json.loads((ROOT/'tests/supplement-guard-results.json').read_bytes());integration=json.loads((ROOT/'tests/integration-control-results.json').read_bytes());review=json.loads((ROOT/'independent-review-record.json').read_bytes())
 assert controls['controls_passed'] is True and controls['actual_registration_performed'] is False
 assert integration['tool_integration_controls_passed'] is True and review['blocking_findings_remaining']==[]
 output={'schema':'modern-packaging-tool-source-freeze-v11','status':'frozen','revision':'combined-source-layout-and-library-supplements-v2',
  'files':[rows[k] for k in sorted(rows)],'original_tool_freeze':meta(BASE/'tool-source-freeze.json'),
  'source_layout_proposal':json.loads((ROOT/'source-layout-input-lock.json').read_bytes())['proposal_freeze'],
  'tool_guard_controls':meta(ROOT/'tests/supplement-guard-results.json'),'integration_controls':meta(ROOT/'tests/integration-control-results.json'),
  'independent_tool_review':meta(ROOT/'independent-review-record.json'),'source_dependencies_only':True,
  'pending_target_templates_excluded_from_publication':True,'generated_model_assets':False,
  'actual_registration_performed':False,'native_accepted':False,'browser_accepted':False,
  'scope':'Separate combined tool revision only. Original tools, source proposal, model geometry, evidence and acceptance gates remain untouched. This manifest does not authorize or certify any package/model publication.'}
 p=TOOLS/'tool-source-freeze.json';assert not p.exists(),'Do not replace a frozen tool revision';p.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(meta(p)))

if __name__=='__main__':main()
