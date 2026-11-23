"""Accept a real 280 control or mobile closure. Unready 345 prerequisites release the city slot."""
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
 expected=Path('/tmp/shanghai-main-280/final-map-31280')/phase/'process.json';assert source.samefile(expected)
 row=read(source);assert row['order']==280 and row['phase']==phase and row['exit_code']==0 and row['node_closed'] and row['chromium_pids'] and row['remaining_chromium']==[]
 report=Path(row['report']);assert sha(report)==row['report_sha256'];summary=read(report);assert summary['completed'] and not summary['errors'] and not summary['failed']
 assert summary['server'].rstrip('/')=='http://127.0.0.1:'+('31279' if kind=='native' else '31280')
 assert row['remaining_children']==[] and row['node_pids'] and summary['id']=='huangpu-ta-ching-bank-southwest-tower'
 driver=expected.parent/'actual-driver.cjs'
 pins=read(h/'dispatch-live.json')
 assert sha(driver) in pins['phase_source_sha256'][phase]
 assert sha(driver)==row['driver_sha256']==summary['scriptSha256']
 for record in [row,summary]:
  if 'source_code_sha256' in record:assert record['source_code_sha256']==sha(driver)
 assert summary['screenshots']
 for shot in summary['screenshots']:
  assert Path(shot['file']).name==shot['file'];f=expected.parent/shot['file'];assert f.stat().st_size==shot['bytes'] and f.stat().st_size>1024 and sha(f)==shot['sha256']
 return row
def grant(kind,path):
 row=host(kind,path);pkg=runpy.run_path(str(w/'freeze-release.py'));cfg=pkg['cfg'];parent=Path(cfg['previous'])
 required_contract=h/'dispatch-live.json'
 if not required_contract.is_file():return None,[str(required_contract)]
 pins=read(required_contract);assert pins['order']==345 and all(sha(Path(k))==v for k,v in pins['physical_inputs'].items())
 native=parent/'native-closed.json';raw=parent/'raw-344-confirmed.json';files=[native,raw]
 if kind=='viewer':files.extend([parent/'viewer-closed.json',w/'native-closed.json',w/'raw-345-confirmed.json',Path('/tmp/shanghai-yongjia-porch/scenes/345-comparison.json')])
 missing=[str(f)for f in files if not f.is_file()]
 if missing:return None,missing
 pkg['native'](native,344,cfg['previous_id']);r,_,_,_=pkg['raw'](raw,344,cfg['previous_id'])
 if kind=='viewer':
  from urllib.request import urlopen
  previous=read(parent/'viewer-closed.json')
  assert previous['order']==344 and previous['passed'] and previous.get('exit',previous.get('exit_code'))==0 and previous.get('remaining',previous.get('remaining_chromium'))==[]
  peg=previous.get('receipt_sha256',previous.get('report_sha256',previous.get('viewer_sha256')))
  if peg:
   direct=[Path(previous[k])for k in ['report','receipt','viewer_report']if isinstance(previous.get(k),str)and Path(previous[k]).is_file()]
   direct.extend((pkg['pr']/'data/audit/guangci-maternity-pavilion-twin-stair-v1').rglob('viewer.json'))
   assert any(sha(p)==peg for p in direct)
  pkg['native'](w/'native-closed.json',345,cfg['id']);own,_,_,_=pkg['raw'](w/'raw-345-confirmed.json',345,cfg['id']);comp=read(files[-1]);assert comp['passed']and comp['order']==345 and comp['port']==31345 ;api=runpy.run_path(str(h/'official-viewer-files.py'));production=api['full'](345);published=production['files'];snapshot=read(Path(own['snapshot']))['files']
  key='data/candidate-city-integrations.json'
  assert snapshot[key]==own['catalog_sha256'] and published[key]==comp['catalog_sha256']
  assert hashlib.sha256(api['canon'](production)).hexdigest()==comp['production_receipt_sha256']
  actual_manifest=pkg['pr']/'assets/models/candidates'/cfg['id']/'manifest.json'
  manifest=read(actual_manifest)
  for value in manifest['assets'].values():
   relative='assets/models/candidates/'+cfg['id']+'/'+value['file']
   assert published[relative]==snapshot[relative]==value['sha256']

  evidence=runpy.run_path(str(h/'official-viewer-files.py'))['inputs'](345,w/'raw-345-confirmed.json',cfg['id'],cfg['page'],h/'frozen-official-inputs')
  assert len(evidence['inputs'])==3 and evidence['production_sha256']==comp['production_receipt_sha256']
  save(h/'verified-official-inputs.json',evidence)

 return {'order':345,'host':280,'kind':kind,'receipt':str(path),'sha256':sha(path),'report_sha256':row['report_sha256'],'dependencies':{str(f):sha(f)for f in files},'previous_snapshot_sha256':r['sha256']},[]
def run_observed(kind,source,row):
 import time,psutil
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
 log=h/(kind+'-launch-'+stamp+'.log');process=h/(kind+'-launch-'+stamp+'.json')
 start=datetime.now(timezone.utc).isoformat();seen={}
 with log.open('xb')as out:
  child=subprocess.Popen([sys.executable,'-Bu',h/'run-phase-live.py',kind],stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
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
 physical=dict(order=345,kind=kind,pid=child.pid,started=start,finished=datetime.now(timezone.utc).isoformat(),exit=child.returncode,observed_children=seen,remaining=remaining,wrapper_closed=child.poll()is not None,host_receipt_sha256=sha(source),host_report_sha256=row['report_sha256'])
 save(process,physical);assert physical['wrapper_closed'] and not remaining
 if child.returncode==0:return True
 save(w/('280-'+kind+'-failed.json'),{**physical,'passed':False,'attempted':True,'started':True,'remaining_children':[],'launch_log':str(log),'launch_log_sha256':sha(log),'launch_process':str(process),'launch_process_sha256':sha(process)})
 return False

def main():
 kind=sys.argv[1];assert kind in ['native','viewer'];source=Path(sys.argv[2]).resolve(strict=True)
 with (h/(kind+'.lock')).open('a')as gate:
  fcntl.flock(gate,fcntl.LOCK_EX);row=host(kind,source);done=w/(kind+'-closed.json')
  if done.is_file():
   x=read(done);assert x['passed']and x['exit']==0 and not x['remaining'] and x['host_receipt_sha256']==sha(source)and x['host_report_sha256']==row['report_sha256'];return
  auth,missing=grant(kind,source)
  if missing:
   save(w/('280-'+kind+'-deferred.json'),dict(order=345,host=280,kind=kind,deferred=True,blender_started=False,chromium_started=False,browser_started=False,started=False,attempted=False,source=str(source),source_sha256=sha(source),host_receipt_sha256=sha(source),host_report_sha256=row['report_sha256'],missing=missing,at=datetime.now(timezone.utc).isoformat()));return
  save(h/(kind+'-window.json'),auth)
  if not run_observed(kind,source,row):return
  result=read(done);assert result['passed'] and result['exit']==0 and not result['remaining']
if __name__=='__main__':main()
