"""Accept a real 272 control or mobile closure. Unready 337 prerequisites release the city slot."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,json,sys,subprocess,runpy,os
h=Path(__file__).resolve().parent;w=h.parents[1]
read=lambda f:json.loads(f.read_bytes())
def sha(f):
 with f.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(f,v):
 t=f.with_name('.'+f.name+'.new');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(t,f)
def host(kind,source):
 phase='before' if kind=='native' else 'phone'
 expected=Path('/tmp/shanghai-main-272/final-map-31272')/phase/'process.json';assert os.path.samefile(source,expected)
 row=read(source);assert row['order']==272 and row['phase']==phase and row['exit_code']==0 and row['node_closed'] and row['chromium_pids'] and row['remaining_chromium']==[]
 report=Path(row['report']);assert sha(report)==row['report_sha256'];summary=read(report);assert summary['completed'] and not summary['errors'] and not summary['failed']
 assert summary['server'].rstrip('/')=='http://127.0.0.1:'+('31271' if kind=='native' else '31272')
 assert row['remaining_children']==[] and row['node_pids'] and summary['id']=='huangpu-salt-industry-bank-entrance'
 actual=source.parent/'actual-driver.cjs'
 assert sha(actual) in {sha(f) for f in (h/'signed-272-drivers').glob('*.cjs')}
 assert sha(actual)==row['driver_sha256']==summary['source_code_sha256']==summary['scriptSha256']
 assert summary['screenshots']
 for shot in summary['screenshots']:
  f=source.parent/shot['file'];assert Path(shot['file']).parts==(shot['file'],) and f.stat().st_size==shot['bytes'] and f.stat().st_size>1024 and sha(f)==shot['sha256']
 return row
def grant(kind,path):
 row=host(kind,path);pkg=runpy.run_path(str(w/'freeze-release.py'));cfg=pkg['cfg'];parent=Path(cfg['previous'])
 required_contract=h/'dispatch-recovered.json'
 if not required_contract.is_file():return None,[str(required_contract)]
 pins=read(required_contract);assert pins['order']==337 and all(sha(Path(k))==v for k,v in pins['physical_inputs'].items())
 native=parent/'native-closed.json';raw=parent/'raw-336-confirmed.json';files=[native,raw]
 if kind=='viewer':files.extend([parent/'viewer-closed.json',w/'native-closed.json',w/'raw-337-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/337-comparison.json')])
 missing=[str(f)for f in files if not f.is_file()]
 if missing:return None,missing
 pkg['native'](native,336,cfg['previous_id']);r,_,_,_=pkg['raw'](raw,336,cfg['previous_id'])
 if kind=='viewer':
  from urllib.request import urlopen
  previous=read(parent/'viewer-closed.json')
  assert previous['order']==336 and previous['passed'] and previous.get('exit',previous.get('exit_code'))==0 and previous.get('remaining',previous.get('remaining_chromium'))==[]
  peg=previous.get('receipt_sha256',previous.get('report_sha256',previous.get('viewer_sha256')))
  if peg:
   direct=[Path(previous[k])for k in ['report','receipt','viewer_report']if isinstance(previous.get(k),str)and Path(previous[k]).is_file()]
   direct.extend((pkg['pr']/'data/audit/xile-apartments-maoming-portholes-v1').rglob('viewer.json'))
   assert any(sha(p)==peg for p in direct)
  pkg['native'](w/'native-closed.json',337,cfg['id']);own,_,_,_=pkg['raw'](w/'raw-337-confirmed.json',337,cfg['id']);comp=read(files[-1]);assert comp['passed']and comp['order']==337 and comp['port']==31337 
  cat='data/candidate-city-integrations.json';snap=read(Path(own['snapshot']));assert snap['files'][cat]==own['catalog_sha256']
  sys.path.insert(0,'/tmp/shanghai-yongjia-porch');from common import full,canon
  production=full(337);assert hashlib.sha256(canon(production)).hexdigest()==comp['production_receipt_sha256'] and production['files'][cat]==comp['catalog_sha256']
  assert all(snap['files'][asset]==production['files'][asset] for asset in [p for p in own['added'] if p.startswith('assets/models/candidates/')])

  evidence=runpy.run_path(str(h/'official-viewer-files.py'))['inputs'](337,w/'raw-337-confirmed.json',cfg['id'],cfg['page'],h/'frozen-official-inputs')
  assert len(evidence['inputs'])==3 and evidence['production_sha256']==comp['production_receipt_sha256']
  save(h/'verified-official-inputs.json',evidence)

 return {'order':337,'host':272,'kind':kind,'receipt':str(path),'sha256':sha(path),'report_sha256':row['report_sha256'],'dependencies':{str(f):sha(f)for f in files},'previous_snapshot_sha256':r['sha256']},[]
def run_observed(kind,source,row):
 import time,psutil
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
 log=h/(kind+'-launch-'+stamp+'.log');process=h/(kind+'-launch-'+stamp+'.json')
 start=datetime.now(timezone.utc).isoformat();seen={}
 with log.open('xb')as out:
  child=subprocess.Popen([sys.executable,'-Bu',h/'run-phase-recovered.py',kind],stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
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
 physical=dict(order=337,kind=kind,pid=child.pid,started=start,finished=datetime.now(timezone.utc).isoformat(),exit=child.returncode,observed_children=seen,remaining=remaining,wrapper_closed=child.poll()is not None,host_receipt_sha256=sha(source),host_report_sha256=row['report_sha256'])
 save(process,physical);assert physical['wrapper_closed'] and not remaining
 if child.returncode==0:return True
 save(w/('272-'+kind+'-failed.json'),{**physical,'passed':False,'attempted':True,'started':True,'remaining_children':[],'launch_log':str(log),'launch_log_sha256':sha(log),'launch_process':str(process),'launch_process_sha256':sha(process)})
 return False

def main():
 kind=sys.argv[1];assert kind in ['native','viewer'];source=Path(sys.argv[2]).absolute()
 with (h/(kind+'.lock')).open('a')as gate:
  fcntl.flock(gate,fcntl.LOCK_EX);row=host(kind,source);done=w/(kind+'-closed.json')
  if done.is_file():
   x=read(done);assert x['passed']and x['exit']==0 and not x['remaining'] and x['host_receipt_sha256']==sha(source)and x['host_report_sha256']==row['report_sha256'];return
  auth,missing=grant(kind,source)
  if missing:
   save(w/('272-'+kind+'-deferred.json'),dict(order=337,host=272,kind=kind,deferred=True,blender_started=False,chromium_started=False,browser_started=False,started=False,attempted=False,source=str(source),source_sha256=sha(source),host_receipt_sha256=sha(source),host_report_sha256=row['report_sha256'],missing=missing,at=datetime.now(timezone.utc).isoformat()));return
  save(h/(kind+'-window.json'),auth)
  if not run_observed(kind,source,row):return
  result=read(done);assert result['passed'] and result['exit']==0 and not result['remaining']
if __name__=='__main__':main()
