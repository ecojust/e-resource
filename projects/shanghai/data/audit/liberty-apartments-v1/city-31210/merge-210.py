"""Join the completed physical public interactions and asset receipts."""
from pathlib import Path
import json,hashlib,os,shutil
w=Path(__file__).parent;h=w/'evidence/210';parts=h/'separate';dest=h/'after';root=Path('/workspace/e-resource/projects/shanghai/data/audit/liberty-apartments-v1/city-31210')
read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():
  try:os.link(src,dst)
  except OSError:shutil.copyfile(src,dst)
 assert sha(src)==sha(dst)
def save(f,d):
 f.parent.mkdir(exist_ok=True,parents=True);f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
data={};receipts={}
for i in ['before','desktop','phone','details','touch','architecture','closeups','distant']:
 control=i=='before';q=h/'before'if control else parts/i;f=q/('control-browser.json'if control else'main-browser.json');cl=q/'closed.json';d=read(f);c=read(cl)
 assert d['section']==i and d['completed'] and not d['errors'] and not d['failed'] and not d.get('failure')
 assert c['report_sha256']==sha(f) and c['driver_sha256']==sha(w/('check-touch-compact.cjs' if i=='touch' else 'check-210-separated.cjs')) and c['exit']==0 and c['node_closed']and not c['remaining']
 copy(f,root/'sessions'/i/f.name);copy(cl,root/'sessions'/i/cl.name)
 if control:continue
 for v in d['screenshots']:
  assert v['sha256']==sha(q/v['file']);copy(q/v['file'],dest/v['file'])
 receipts[i]=c;data[i]=d
d=dict(data['details'])
assert all(row['scriptSha256']==receipts[phase]['driver_sha256'] for phase,row in data.items())
for k in ['catalog','id','caseSha256','bindings','server']:
 assert all(x[k]==d[k]for x in data.values())
for field in ['views','screenshots']:d[field]=[v for row in data.values()for v in row[field]]
d['ground']=data['architecture']['ground']
assert len(d['ground'])==20 and len(d['views'])==len(d['screenshots'])==9
assert {'map-mobile','map-desktop','map-beacon-return','map-touch-beacon-return','map-street-facade','map-roof','map-distant','map-recessed-door-and-steps','map-three-ribs-and-setbacks'}=={a['view']for a in d['views']}
assert d['realBeacon']['landed']==data['touch']['realBeacon']['landed']==d['id']
assert data['touch']['realBeacon']['action']=='physical canvas touch'
d['physical_selections']=[d['realBeacon'],data['touch']['realBeacon']]
d['files']=[]
for name in dict.fromkeys(v['file']for row in data.values()for v in row['files']):
 records=[r for row in data.values()for r in row['files']if r['file']==name]
 assert len({(r['sha256'],r['bytes'])for r in records})==1
 d['files'].append({**records[0],'loadedByScene':any(r['loadedByScene']for r in records)})
assert len([r for r in d['files']if '/models/candidates/'in r['file']])==4
d.pop('section',None);d['sessions']=receipts;d['started']=min(r['started']for r in data.values());d['finished']=max(r['finished']for r in data.values())
save(dest/'main-browser.json',d);save(dest/'exit.json',dict(code=0,phase='after',base=d['server'],case_sha256=d['caseSha256'],driver_sha256=d['scriptSha256'],production=sha(w/'210-production.json'),finished=d['finished'],sessions=receipts))
for name in ['check-210-separated.cjs','check-touch-compact.cjs','source-driver.sha256','run-210-separated.py','merge-210.py']:copy(w/name,root/name)

transitions=[]
failed_base=Path('/dev/shm/liberty210-active-proofs')
for phase in ('touch-first-390x844-renderer-crash','touch-second-390x590-renderer-crash','touch-fourth-return-renderer-crash'):
 directory=failed_base/phase;f=directory/'main-browser.json';c=directory/'closed.json';capture=read(f);exit_record=read(c)
 proof=capture.get('realBeacon',{});assert proof.get('pointer',{}).get('trusted') and proof['pointer']['type']=='touch' and proof['landed']==d['id']
 assert 'xuhui-willow-court' in proof['previous'] and exit_record['exit']==1 and exit_record['node_closed'] and not exit_record['remaining'] and exit_record['report_sha256']==sha(f)
 copy(f,root/'sessions'/phase/f.name);copy(c,root/'sessions'/phase/c.name)
 transitions.append({'phase':phase,'action':proof,'ended':exit_record['finished'],'report_sha256':sha(f),'physical_exit':exit_record['exit'],'role':'trusted cross-selection; the renderer subsequently stopped before its final capture'})
save(root/'touch-cross-selection.json',{'touch_cross_selection':transitions,'completed_screenshot':{'phase':'touch','sha256':data['touch']['screenshots'][0]['sha256'],'role':'touching the already loaded public beacon'}})
