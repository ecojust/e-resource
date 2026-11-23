"""Replay the URL selected by a real pointer in a fresh browser to release the previous street's GPU resources."""
import os,sys,datetime,json,subprocess,time,hashlib
from pathlib import Path
import psutil
pid,driver,case,phase=sys.argv[1:]
root=Path('/dev/shm/taching280-live/evidence')/phase
local=Path('/tmp/g80/evidence')/phase
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
for part in ('activate','render'):
 folder=root/'pointer-activation' if part=='activate' else root
 target=local/'pointer-activation' if part=='activate' else local
 folder.mkdir(parents=True,exist_ok=True)
 if part=='activate' and (folder/'session-closed.json').is_file():
  prior=json.loads((folder/'session-closed.json').read_bytes()); report=folder/'main-browser.json'
  assert prior['exit_code']==0 and prior['remaining']==[] and sha(report)==prior['report_sha256']
  assert sha(folder/'actual-driver.cjs')==prior['driver_sha256']==json.loads(report.read_bytes())['scriptSha256']
  assert json.loads(report.read_bytes())['completed'] and json.loads(report.read_bytes())['phase']==phase
  continue
 if part=='activate':(folder/'actual-driver.cjs').write_bytes(Path(driver).read_bytes())
 profile=Path(os.environ['TMPDIR'])/part
 active_profile=Path('/dev/shm/taching280-live/graphics')/Path(os.environ['TMPDIR']).name/part
 active_profile.mkdir(exist_ok=True)
 env=dict(os.environ,QA_POINTER_STEP=part,QA_POINTER_INPUT_REPORT=str(local/'pointer-activation/main-browser.json'),QA_OUTPUT_DIR=str(target),TMPDIR=str(profile),XDG_CONFIG_HOME=str(profile/'cfg'),XDG_CACHE_HOME=str(profile/'cache'),CHROME_CONFIG_HOME=str(profile/'cfg'))
 report=folder/'main-browser.json'; assert not report.exists()
 argv=['nsenter','--preserve-credentials','--user','--mount','--target',pid,'--','node',driver,case,phase]
 start=now();proc=subprocess.Popen(argv,env=env);seen={}
 while proc.poll() is None:
  try:kids=psutil.Process(proc.pid).children(recursive=True)+[psutil.Process(proc.pid)]
  except psutil.Error:kids=[]
  for item in kids:
   try:seen[item.pid]=(item.create_time(),item.name())
   except psutil.Error:pass
  time.sleep(.23)
 remaining=[]
 for num,(birth,name)in seen.items():
  try:child=psutil.Process(num);alive=child.create_time()==birth and child.status()not in ('zombie','dead')
  except psutil.Error:alive=False
  if alive:remaining.append(num)
 receipt={'stage':part,'started':start,'finished':now(),'exit_code':proc.returncode,'node_pids':[num for num,(_,name)in seen.items()if name in ('MainThread','node','nodejs')],'chromium_pids':[num for num,(_,name)in seen.items()if name in ('chromium','chrome')],'remaining':remaining,'driver_sha256':sha(driver),'report_sha256':sha(report)if report.is_file()else None}
 (folder/('session-closed.json'if part=='activate'else 'render-session-closed.json')).write_text(json.dumps(receipt,indent=2)+'\n')
 assert proc.returncode==0 and receipt['node_pids'] and receipt['chromium_pids'] and not remaining and json.loads(report.read_bytes())['completed'],receipt
