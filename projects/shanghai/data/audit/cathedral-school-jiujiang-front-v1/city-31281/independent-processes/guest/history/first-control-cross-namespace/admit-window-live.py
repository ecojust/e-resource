"""Accept a real 281 control or mobile closure. Unready 346 prerequisites release the city slot."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,json,sys,subprocess,runpy,os
h=Path(__file__).resolve().parent;w=h.parent
read=lambda f:json.loads(f.read_bytes())
def sha(f):
 with f.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(f,v):
 t=f.with_name('.'+f.name+'.new');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(t,f)
def host(kind,source):
 phase='control' if kind=='native' else 'mobile-pin'
 work=Path('/tmp/shanghai-main-281/formal-31281')
 expected=work/'isolated-evidence'/phase/'closed.json';assert source.samefile(expected)
 row=read(source);port=31280 if kind=='native' else 31281
 assert row['order']==281 and row['phase']==phase and row['port']==row['actual_origin']==port
 assert row['exit']==row['exit_code']==0 and row['cdp_closed'] and row['node_closed'] and row['node_pid']>0 and row['chromium_pids']
 assert row['remaining']==row['remaining_chromium']==[] and set(row['chromium_pids'])==set(map(int,row['observed_chromium_pid_and_starttime']))
 assert all(int(v)>0 for v in row['observed_chromium_pid_and_starttime'].values())
 report=Path(row['report']);assert report.samefile(expected.parent/('control-browser.json' if kind=='native' else 'main-browser.json')) and sha(report)==row['report_sha256']
 result=read(report);assert result['id']=='huangpu-cathedral-school-jiujiang-front' and result['completed'] and result['phase']==phase
 assert result['server']=='http://127.0.0.1:'+str(port)+'/' and len(result['screenshots'])>=1 and not result['errors']
 actual=expected.parent/'actual-driver.cjs'
 assert sha(actual)==row['source_code_sha256']==row['driver_sha256']==result['scriptSha256']
 assert sha(actual) in read(h/'dispatch-live.json')['phase_source_sha256'][phase]
 for q in result['screenshots']:
  f=Path(q['file']);assert f.name==q['file'] and (report.parent/f).stat().st_size==q['bytes'] and sha(report.parent/f)==q['sha256']
 return row
def check_raw_and_site(raw,book,comparison,signature,manifest_bytes,model,page):
    catalog='data/candidate-city-integrations.json'
    order=raw['order']
    assert comparison['passed'] and comparison['order']==order and comparison['port']==31000+order
    assert raw['catalog_sha256']==book['files'][catalog]
    assert comparison['catalog_sha256']==signature['files'][catalog]
    assert book['resulting_count']==raw['count']==signature['resulting_count']
    stem='assets/models/candidates/'+model+'/'
    key=stem+'manifest.json'
    assert hashlib.sha256(manifest_bytes).hexdigest()==signature['files'][key]==book['files'][key]
    manifest=json.loads(manifest_bytes)
    assert manifest['id']==model and manifest['viewer_page']==page and set(manifest['assets'])=={'raw','full','lod','native'}
    for role,item in manifest['assets'].items():
        name=item['file']
        assert isinstance(name,str) and name and name not in ('.','..') and '/' not in name
        assert item['bytes']>0 and signature['files'][stem+name]==book['files'][stem+name]==item['sha256'],role
    return True

def grant(kind,path):
 row=host(kind,path);pkg=runpy.run_path(str(h/'read-physical-prior.py'));cfg=pkg['cfg'];parent=Path(cfg['previous'])
 required_contract=h/'dispatch-live.json'
 if not required_contract.is_file():return None,[str(required_contract)]
 pins=read(required_contract);assert pins['order']==346 and all(sha(Path(k))==v for k,v in pins['physical_inputs'].items())
 native=parent/'native-closed.json';raw=parent/'raw-345-confirmed.json';files=[native,raw]
 if kind=='viewer':files.extend([parent/'viewer-closed.json',w/'native-closed.json',w/'raw-346-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/346-comparison.json')])
 missing=[str(f)for f in files if not f.is_file()]
 if missing:return None,missing
 pkg['native'](native,345,cfg['previous_id']);r,_,_,_=pkg['raw'](raw,345,cfg['previous_id'])
 if kind=='viewer':
  from urllib.request import urlopen
  previous=read(parent/'viewer-closed.json')
  assert previous['order']==345 and previous['passed'] and previous.get('exit',previous.get('exit_code'))==0 and previous.get('remaining',previous.get('remaining_chromium'))==[]
  peg=previous.get('receipt_sha256',previous.get('report_sha256',previous.get('viewer_sha256')))
  if peg:
   direct=[Path(previous[k])for k in ['report','receipt','viewer_report']if isinstance(previous.get(k),str)and Path(previous[k]).is_file()]
   direct.extend((pkg['pr']/'data/audit/anhe-terrace-ruijin-gate-v1').rglob('viewer.json'))
   assert any(sha(p)==peg for p in direct)
  pkg['native'](w/'native-closed.json',346,cfg['id']);own,raw_book,_,_=pkg['raw'](w/'raw-346-confirmed.json',346,cfg['id']);comp=read(files[-1]);assert comp['passed']and comp['order']==346 and comp['port']==31346
  page=pkg['pr']/cfg['page']
  with urlopen('http://127.0.0.1:31346/'+cfg['page'],timeout=12) as resp:
   bookpath=files[-1].with_name('346-production.json');signature=read(bookpath);assert sha(bookpath)==comp['production_receipt_sha256']
   assert resp.status==200 and hashlib.sha256(resp.read()).hexdigest()==signature['files'][cfg['page']]
  manifest_url='http://127.0.0.1:'+str(comp['port'])+'/assets/models/candidates/'+cfg['id']+'/manifest.json'
  with urlopen(manifest_url,timeout=12) as public_manifest:
   assert public_manifest.status==200
   check_raw_and_site(own,raw_book,comp,signature,public_manifest.read(),cfg['id'],cfg['page'])
 return {'order':346,'host':281,'kind':kind,'receipt':str(path),'sha256':sha(path),'report_sha256':row['report_sha256'],'dependencies':{str(f):sha(f)for f in files},'previous_snapshot_sha256':r['sha256']},[]
def run_observed(kind,source,row):
 import time,psutil
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
 log=h/(kind+'-launch-'+stamp+'.log');process=h/(kind+'-launch-'+stamp+'.json')
 start=datetime.now(timezone.utc).isoformat();seen={}
 with log.open('xb')as out:
  child=subprocess.Popen(['nsenter','--target',Path('/run/lock/j346/pid').read_text().strip(),'--user','--mount','--preserve-credentials',sys.executable,'-Bu',h/'run-phase-live.py',kind],stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  while child.poll() is None:
   try:
    for proc in psutil.Process(child.pid).children(recursive=True):
     try:seen[proc.pid]=proc.create_time()
     except psutil.Error:pass
   except psutil.Error:pass
   time.sleep(.12)
 def alive(pid,birth):
  try:q=psutil.Process(pid);return q.create_time()==birth and q.status()!=psutil.STATUS_ZOMBIE
  except psutil.NoSuchProcess:return False
 for _ in range(60):
  remaining=[pid for pid,t in seen.items()if alive(pid,t)]
  if not remaining:break
  time.sleep(.16)
 physical=dict(order=346,kind=kind,pid=child.pid,started=start,finished=datetime.now(timezone.utc).isoformat(),exit=child.returncode,observed_children=seen,remaining=remaining,wrapper_closed=child.poll()is not None,host_receipt_sha256=sha(source),host_report_sha256=row['report_sha256'])
 save(process,physical);assert physical['wrapper_closed'] and not remaining
 if child.returncode==0:return True
 save(h/(kind+'-failed.json'),{**physical,'passed':False,'attempted':True,'started':True,'remaining_children':[],'launch_log':str(log),'launch_log_sha256':sha(log),'launch_process':str(process),'launch_process_sha256':sha(process)})
 failure=read(h/(kind+'-failed.json'))
 save(h/(kind+'-deferred.json'),{**failure,'order':346,'host':281,'kind':kind,'deferred':True,'attempted':True,'started':True,'source':str(source),'source_sha256':sha(source)})
 return False

def main():
 kind=sys.argv[1];assert kind in ['native','viewer'];source=Path(sys.argv[2]).absolute()
 with (h/(kind+'.lock')).open('a')as gate:
  fcntl.flock(gate,fcntl.LOCK_EX);row=host(kind,source);done=w/(kind+'-closed.json')
  if done.is_file():
   x=read(done);assert x['passed']and x['exit']==0 and not x['remaining'] and x['host_receipt_sha256']==sha(source) and x['host_report_sha256']==row['report_sha256'];return
  auth,missing=grant(kind,source)
  if missing:
   save(h/(kind+'-deferred.json'),dict(order=346,host=281,kind=kind,deferred=True,blender_started=False,browser_started=False,started=False,attempted=False,source=str(source),source_sha256=sha(source),host_receipt_sha256=sha(source),host_report_sha256=row['report_sha256'],missing=missing,at=datetime.now(timezone.utc).isoformat()));return
  save(h/(kind+'-window.json'),auth)
  if not run_observed(kind,source,row):return
  result=read(done);assert result['passed'] and result['exit']==0 and not result['remaining']
if __name__=='__main__':main()
