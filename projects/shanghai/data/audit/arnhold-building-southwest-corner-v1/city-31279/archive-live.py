"""Publish only the checks completed on the two signed city sites. Deduplicate immutable local files."""
from pathlib import Path
import json,hashlib,shutil,os,sys
D=Path(__file__).parent;P=Path('/workspace/e-resource/projects/shanghai');n=int(sys.argv[1]);assert n in (279,)
a=P/'data/audit'/('zhu-mintang-residence-v1'if n==179 else'arnhold-building-southwest-corner-v1');out=Path('/dev/shm/arnhold279-live/verified-audit/city-31279');out.mkdir(exist_ok=True,parents=True)
read=lambda p:json.loads(p.read_bytes())
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def copy(f,name):
 t=out/name;t.parent.mkdir(exist_ok=True,parents=True)
 if not t.exists():
  try:os.link(f,t)
  except OSError:shutil.copy2(f,t)
 assert H(t)==H(f)
files={}
for phase in ('before','after'):
 used=n-1 if phase=='before'else n;incoming=D/'evidence'/str(n)/phase
 name=phase+'.json'if n==179 else('control-browser.json'if phase=='before'else'main-browser.json');f=incoming/name;r=read(f)
 e=read(incoming/'exit.json');assert e['code']==0 and e['production']==H(D/f'{used}-production.json')
 assert r['completed']and not any(r.get(k)for k in ('httpErrors','errors','pageErrors','failedRequests','failed'))
 if n==179:imgs=r['views'];assert r['browserClosed'];assert len(r['ground'])==24
 else:imgs=r['screenshots']
 if n==279 and phase=='after':assert len(r['ground'])==66
 for t in imgs:
  fimg=incoming/t['file'];assert H(fimg)==t['sha256'];copy(fimg,t['file'])
 copy(f,name);copy(incoming/'exit.json',phase+'-exit.json');copy(D/f'{used}-bindings.json',phase+'-bindings.json')
 files[phase]={'URL':e['base'],'production':e['production'],'count':r['catalog']['count'],'catalog_sha256':r['catalog']['sha256'],'photos':{t['file']:t['sha256']for t in imgs}}
rt='runtime-overlay.json'if n==179 else'runtime-placement.json';copy(D/f'runtime{n}'/rt,rt)
case=D/f'case{n}.json';copy(case,'case.json');copy(D/f'check-{n}-separated.cjs','check-city.cjs')
if n==279:copy(D/'candidate-audit-groups.cjs','candidate-audit-groups.cjs')
s=D/f'{n}-all-http.json';h=read(s);assert h['passed'] and h['production_receipt_sha256']==files['after']['production'];copy(s,'all-http.json')
control_full=D/'278-all-http.json';previous=read(control_full)
assert previous['passed'] and previous['production_receipt_sha256']==files['before']['production'] and len(previous['ranges'])>=5
copy(control_full,'before-all-http.json')
m=read(D/'two-transitions.json')[str(n)]
for k,digest in m['viewer_images']:assert H(a/k)==digest
x={'passed':True,'order':n,'real_city':files,'standalone_matched_by_actual_http':m,'ground_runtime':rt,'full_http':dict(count=h['count'],bytes=h['total_bytes'],ranges=len(h['ranges']))}
(out/'release-evidence.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


local=D/'viewer-31279'
new=read(local/'viewer.json')
assert new['passed'] and len(new['downloads'])==4 and len(new['views'])==6 and read(local/'closed.json')['code']==0
for x in ['closed.json','viewer.json',*(v['filename']for v in new['views'])]:copy(local/x,'standalone/'+x)

for key in ('controller-recovery.json','four-downloads-retained.cjs','viewer-retained.py','guest-344-recovered.json','offer-344-recovered.py'):
 copy(D/key,key)
for key,item in new['downloads'].items():
 path=local/'saved'/item['file']
 assert item['saveAsVerified'] and path.stat().st_size==item['bytes'] and H(path)==item['sha256']
