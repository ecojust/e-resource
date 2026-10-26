#!/usr/bin/env python3
"""Finite source-publication guards only. No actual model acceptance."""
from pathlib import Path
import copy,json,sys,tempfile
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parents[1];V11=HERE.parent
sys.path.insert(0,str(HERE/'toolchain/registration'))
import contracts as c

def desc(p):return {'source':str(p),**c.meta(p)}
def load(p):return json.loads(Path(p).read_text())
results=[]
photo_sets=load(V11/'registration-compatibility-preparation/pending/declared-photo-rows.json')
roots={'jiading-shanghai-auto-museum':V11/'auto-museum/geometry-v2','minhang-baoyugang-library':V11/'pao-yue-kong-library/geometry-v2'}
for ident,root in roots.items():
 pending=(HERE/'museum-source-whitelist.pending.json' if ident.startswith('jiading') else V11/'registration-compatibility-preparation/pending/minhang-baoyugang-library.source-whitelist.pending.json')
 original=load(pending);positive=copy.deepcopy(original);positive['status']='ready'
 # This descriptor identifies the known baseline for an isolated source test;
 # it never becomes a new executable tool manifest or a real target/request.
 tool=desc(V11/'registration-evidence-revision-v2/toolchain/tool-source-freeze.json')
 positive['tool_source_freeze_sha256']=tool['sha256']
 base={'source_freeze':desc(root/'source-freeze.json'),'tool_source_freeze':tool}
 frozen={str(root/r.get('file',r.get('path'))):c.identity(r)for r in load(root/'source-freeze.json')['files']}
 def check(name,doc,accept=False,request_change=None,photos=None):
  with tempfile.TemporaryDirectory(prefix='isolated-source-control-',dir=HERE/'tests')as tmp:
   p=Path(tmp)/'synthetic.json';p.write_text(json.dumps(doc));request={**copy.deepcopy(base),'source_delivery_whitelist':desc(p)}
   if request_change:request_change(request)
   try:
    c.public_source_whitelist(request,{'id':ident},{'asset_files':[]},photos if photos is not None else photo_sets[ident],frozen,{},c.Inputs())
    assert accept,'Unexpected accepted control '+name
    results.append({'model':ident,'control':name,'expected':'source-only accepted','observed_expected':True})
   except ValueError as e:
    assert not accept,(name,str(e));results.append({'model':ident,'control':name,'expected':'rejected','observed_expected':True,'reason':str(e)})
 check('all frozen source dependencies remain at original relative paths',positive,True)
 check('pending remains rejected',original)
 for rel in ['calibration.json','references/commons-57659417.jpg'] if ident.startswith('jiading') else ['calibration.json','references/commons-14434416-original.jpg']:
  d=copy.deepcopy(positive);d['files']=[r for r in d['files']if r['file']!='source/precise/'+ident+'/'+rel];check('reject missing '+rel,d)
 d=copy.deepcopy(positive);row=next(r for r in d['files']if r['file'].endswith('plan-elevation-v2.png'));row['file']=row['file'].replace('plan-elevation-v2','unreviewed');check('reject relocated binary dependency',d)
 d=copy.deepcopy(positive);next(r for r in d['files']if r['kind']=='authored-source' and r['file'].endswith('.jpg'))['license']='MIT';check('reject relabeled photograph license',d)
 photos=copy.deepcopy(photo_sets[ident]);photos[0]['author']='Unrelated author';check('reject incorrect photograph author',positive,photos=photos)
 d=copy.deepcopy(positive);next(r for r in d['files']if r['file'].endswith('calibration.json'))['sha256']='0'*64;check('reject stale dependency SHA',d)
 d=copy.deepcopy(positive);next(r for r in d['files']if r['file'].endswith('plan-elevation-v2.png'))['kind']='generated-evidence';check('reject binary evidence bypass',d)
 check('reject unknown source freeze',positive,request_change=lambda r:r['source_freeze'].update(sha256='0'*64))
 if ident.startswith('jiading'):
  for rel in ['repair-inputs.json','change-scope.json','history/source-freeze-v1.json']:
   d=copy.deepcopy(positive);d['files']=[r for r in d['files']if r['file']!='source/precise/'+ident+'/'+rel];check('reject missing new bounded-repair dependency '+rel,d)
  check('reject v1 source freeze under v2 tool selection',positive,request_change=lambda r:r['source_freeze'].update(sha256='82e0bb92df2d7ff09bc0554fc5c421546b865a7b8849b6cbbdb131133169db2c'))

old=V11/'registration-evidence-revision-v2/toolchain'
old_rules=load(old/'registration/public_dependency_allowlist.json');new_rules=load(HERE/'toolchain/registration/public_dependency_allowlist.json')
assert new_rules['models']['minhang-baoyugang-library']==old_rules['models']['minhang-baoyugang-library']
assert len(new_rules['models']['jiading-shanghai-auto-museum']['required_author_files'])==59
assert new_rules['models']['jiading-shanghai-auto-museum']['special_files']==old_rules['models']['jiading-shanghai-auto-museum']['special_files']
for file in ['registration/public_dependency_compat.py','registration/contracts.py','registration/report_adapters.py','registration/geometry_supplements.py','engine/finite_checks.py','engine/modern_mesh.py','engine/audit_raw_structure.py','decode_core.mjs','check_decoded_modern.mjs','run_decoded_finite.py','package_modern.py']:
 assert (HERE/'toolchain'/file).read_bytes()==(old/file).read_bytes()
results.append({'control':'Library branch, all10 Museum special-file identities and core checker/decoder/mathematics stay exact','observed_expected':True})
report={'schema':'museum-v2-exact-source-compatibility-controls-v11','source_contract_controls_passed':True,'control_count':len(results),'controls':results,'actual_geometry_checked':False,'new_tool_freeze_created':False,'model_ready':False,'actual_registration_performed':False,'native_accepted':False,'browser_accepted':False}
with(HERE/'tests/source-control-results.json').open('x')as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_controls':len(results),'passed_in_source_contract_scope':True,'model_ready':False}))
