"""Exact user-authorized README navigation exception; no broad README allowlist."""
from pathlib import Path
import hashlib,json,subprocess,sys
from urllib.parse import urlparse,parse_qs
BASE='93e3cb2d0ddeba1a7db7d435bf66c2f61492326e'
REL='projects/shanghai/data/audit/readme-navigation-v1/'
EXPECTED={'report.json':'65c7cbcac92d92c48fbfeb1fb648a10f637be0847cf4d14be12b81b40ae63569','README.md':'a2d934338d4f7048f00caba65f7c973a29206e7f84bafa18b4c496671064e006'}
def validate_navigation(root):
 root=Path(root);sha=lambda b:hashlib.sha256(b).hexdigest();bindings=[]
 assert {p.name for p in (root/REL).iterdir()}==set(EXPECTED)
 for n,h in EXPECTED.items():
  b=(root/REL/n).read_bytes();assert sha(b)==h,(n,'authorized receipt changed');bindings.append({'file':REL+n,'bytes':len(b),'sha256':h})
 d=json.loads((root/REL/'report.json').read_text());assert d['baseline_commit']==BASE and len(d['files'])==64
 cat=json.loads((root/'projects/shanghai/data/candidate-city-integrations.json').read_text());legacy=json.loads((root/'projects/shanghai/data/landmarks.json').read_text());known={r['id']:'overview'for r in cat['models']}|{r['id']:'walk'for r in legacy};rows=[];seen=set();navigation=0;references=0
 for r in d['files']:
  path=r['path'];assert path not in seen and Path(path).name=='README.md';seen.add(path);assert path.startswith(('projects/shanghai/source/','projects/shanghai/data/audit/'))
  before=subprocess.check_output(['git','show',BASE+':'+path],cwd=root);assert sha(before)==r['before_sha256'];s=before.decode()
  for op in r['replacement_operations']:
   assert s.count(op['before_text'])==1,(path,op['line']);s=s.replace(op['before_text'],op['after_text'],1)
  result=s.encode();after=(root/path).read_bytes();assert result==after and sha(after)==r['after_sha256'],path
  for ch in r['changes']:
   url=ch['after_url']
   if ch['kind']=='broken-relative-source-reference':
    target=(root/path).parent.joinpath(url).resolve();rel=str(target.relative_to(root));assert target.is_file()or subprocess.run(['git','cat-file','-e',BASE+':'+rel],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0;references+=1;continue
   u=urlparse(url);assert u.scheme=='https'and u.netloc=='raw.githack.com'and u.path=='/ecojust/e-resource/master/projects/shanghai/index.html';frag=parse_qs(u.fragment)
   if ch['kind']=='surface':assert frag=={'mode':['overview']}
   else:assert frag=={'landmark':[ch['model_id']],'mode':[known[ch['model_id']]]}
   navigation+=1
  rows.append({'file':path,'before_sha256':r['before_sha256'],'after_sha256':r['after_sha256'],'bytes':len(after),'exact_operations_replayed':len(r['replacement_operations'])})
 assert navigation==71 and references==4
 for r in d['preserved_immutable_links']:
  path=root/r['path'];content=path.read_text()if path.exists()else subprocess.check_output(['git','show',':'+r['path']],cwd=root,text=True);assert r['url']in content
 return{'schema':'city-museum-independent-navigation-exception-v1','passed':True,'baseline_commit':BASE,'authorization':'Root relayed explicit current user README navigation repair and approved these exact64 paths/before/after SHA plus these exact2 new audit documents. No general exception for README files or historical audits.','method':'Independently replay every uniquely matching textual operation from actual baseline Git bytes, compare complete current file bytes and exact after SHA; verify71 current global-map targets and4 source-reference targets. No browser or old model decode.','authorized_receipts':bindings,'existing_readme_files':rows,'existing_file_count':64,'canonical_global_targets':71,'corrected_source_reference_links':4,'immutable_links_preserved':len(d['preserved_immutable_links']),'new_navigation_audit_files':[REL+n for n in EXPECTED]}
if __name__=='__main__':
 root,out=map(Path,sys.argv[1:3]);r=validate_navigation(root);out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'existing_files':64,'global_targets':71,'new_audit_files':2}))
