#!/usr/bin/env python3
"""Create NEW source compatibility preparation; never a ready model or tool freeze."""
from pathlib import Path
import copy,difflib,hashlib,json,shutil,struct

HERE=Path(__file__).resolve().parent
V11=HERE.parent
OLD=V11/'registration-evidence-revision-v2/toolchain'
NEW=HERE/'toolchain'
MUSEUM=V11/'auto-museum/geometry-v2'
ID='jiading-shanghai-auto-museum'
EXPECTED_BASE='f1f71403e3191c838e71ec0af4c26cab48720d4aaeb8f11d0052f938ccd7cd26'
EXPECTED_AUTHOR='5acf7f82a27d7ccfb4b7d4ca0c6e13d98cb381c8409cc3fa0a5697c01fe0a45a'
def desc(p):
 p=Path(p);return {'source':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def load(p):return json.loads(Path(p).read_text())
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:f.write(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

baseline=desc(OLD/'tool-source-freeze.json');author=desc(MUSEUM/'source-freeze.json')
assert baseline['sha256']==EXPECTED_BASE and author['sha256']==EXPECTED_AUTHOR
freeze=load(OLD/'tool-source-freeze.json')
copied=[]
for r in freeze['files']:
 p=Path(r['source']);assert desc(p)==r
 if p.is_relative_to(OLD):
  dest=NEW/p.relative_to(OLD);dest.parent.mkdir(parents=True,exist_ok=True)
  assert not dest.exists();shutil.copyfile(p,dest);assert dest.read_bytes()==p.read_bytes();copied.append({'original':r,'copy':desc(dest)})
author_doc=load(MUSEUM/'source-freeze.json');source_rows=author_doc['files'];assert len(source_rows)==59
for row in source_rows:
 p=MUSEUM/row['file'];assert desc(p)=={'source':str(p),'bytes':row['bytes'],'sha256':row['sha256']}
old_rules=load(OLD/'registration/public_dependency_allowlist.json');rules=copy.deepcopy(old_rules)
rule=rules['models'][ID];rule['source_freeze_sha256']=author['sha256'];rule['source_file_count']=59
rule['required_author_files']=[{k:r[k]for k in ('file','bytes','sha256')}for r in source_rows]
source_by_name={r['file']:r for r in source_rows}
for name,special in rule['special_files'].items():
 row=source_by_name[name];special.update(bytes=row['bytes'],sha256=row['sha256'])
 if special['category']=='authored-diagram-png':
  b=(MUSEUM/name).read_bytes()[:24];assert b[:8]==b'\x89PNG\r\n\x1a\n';special['pixel_size']=list(struct.unpack('>II',b[16:24]))
assert rules['models']['minhang-baoyugang-library']==old_rules['models']['minhang-baoyugang-library']
dest=NEW/'registration/public_dependency_allowlist.json'
assert dest.read_bytes()==(OLD/'registration/public_dependency_allowlist.json').read_bytes()
dest.write_text(json.dumps(rules,ensure_ascii=False,indent=2)+'\n')
patch=''.join(difflib.unified_diff((OLD/'registration/public_dependency_allowlist.json').read_text().splitlines(True),dest.read_text().splitlines(True),fromfile='f1f/registration/public_dependency_allowlist.json',tofile='museum-v2/registration/public_dependency_allowlist.json'))
with (HERE/'source-allowlist.patch').open('x')as f:f.write(patch)

old_pending=load(V11/'registration-compatibility-preparation/pending/jiading-shanghai-auto-museum.source-whitelist.pending.json')
prefix='source/precise/'+ID+'/'
old_rows={r['file'][len(prefix):]:r for r in old_pending['files']if r['kind']=='authored-source'}
rows=[]
for r in source_rows:
 row=copy.deepcopy(old_rows.get(r['file'],{'kind':'authored-source','license':'MIT','license_url':'https://opensource.org/license/mit','redistribution_basis':'New authored bounded repair/source development record; no third-party snapshot or pixels.'}))
 row.update(file=prefix+r['file'],source=str(MUSEUM/r['file']),bytes=r['bytes'],sha256=r['sha256']);rows.append(row)
for r in old_pending['files']:
 if r['kind']=='licensed-reference':
  row=copy.deepcopy(r);row['source']=str(MUSEUM/'references'/Path(row['source']).name);assert desc(row['source'])=={k:row[k]for k in ('source','bytes','sha256')};rows.append(row)
pending={'schema':'modern-model-public-source-whitelist-v11','building_id':ID,'status':'pending','source_freeze_sha256':author['sha256'],'tool_source_freeze_sha256':None,
 'document_roles':{'readme':prefix+'README.md','build':prefix+'README.md','attribution':prefix+'references/ATTRIBUTION.md'},'files':rows}
write(HERE/'museum-source-whitelist.pending.json',pending)
write(HERE/'baseline-lock.json',{'schema':'museum-v2-tool-compatibility-baseline-v11','original_tool_freeze':baseline,'new_museum_author_freeze':author,
 'library_author_rule_unchanged':True,'copied_frozen_tool_files':copied,'source_allowlist_only_changed_at_this_stage':True,
 'source_only':True,'new_tool_freeze':None,'model_ready':False,'geometry_accepted':False,'native_accepted':False,'browser_accepted':False,
 'next_gate':'Museum-specific actual revision/support proof adapter and explicit decoded transfer are still required before freezing a usable new registrar. Original Library/f1f remains immutable.'})
print(json.dumps({'new_source_rule':desc(dest),'source_count':len(source_rows),'special_count':len(rule['special_files']),'copied_frozen_files':len(copied),'model_ready':False},indent=2))
