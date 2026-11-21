"""Run both public viewer sizes and four downloads against the final 31k entry."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
from urllib.request import urlopen
import argparse,json,os,fcntl,psutil,sys,subprocess,tempfile,time
p=argparse.ArgumentParser();p.add_argument('--assigned-standalone-slot',action='store_true',required=True);p.parse_args()
D=Path(__file__).resolve().parent;P=Path('/workspace/e-resource/projects/shanghai');a=P/'data/audit/sihang-building-v1';dst=D/'viewer-31213';dst.mkdir(exist_ok=True);h=lambda b:sha256(b).hexdigest();numeric=lambda f:json.loads(f.read_bytes())
stage=numeric(D/'213-bindings.json');port=stage['port'];base=f'http://127.0.0.1:{port}/';assert port==31213
fingerprints=numeric(D/'two-transitions.json')['213'];current=numeric(Path('/tmp/shanghai-yongjia-porch/scenes/213-comparison.json'));assert current['production_receipt_sha256']==stage['production'] and current['passed']
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 start=datetime.now(timezone.utc).isoformat()
 env={**os.environ,'MODEL_BASE_URL':base,'SHANGHAI_PROJECT_ROOT':str(P),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
 with tempfile.TemporaryDirectory(prefix='viewer213-',dir='/dev/net/shanghai-213-746jd3ez')as temp:
  env['TMPDIR']=temp
  proc=subprocess.Popen(['node','-r',P/'data/audit/brunner-mond-v1/viewer-timeout.cjs',D/'four-downloads.cjs','hongkou-sihang-building-north-front',dst],cwd=P,env=env)
  seen=set()
  while proc.poll() is None:
   try:children=psutil.Process(proc.pid).children(recursive=True)
   except psutil.NoSuchProcess:children=[]
   for child in children:
    try:
     if child.name() in ('chrome','chromium','headless_shell','chrome-headless-shell'):seen.add(child.pid)
    except psutil.NoSuchProcess:continue
   time.sleep(.15)
  code=proc.returncode
  def running(pid):
   try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0] not in ('X','Z')
   except (FileNotFoundError,ProcessLookupError):return False
  for attempt in range(40):
   remaining=[pid for pid in seen if running(pid)]
   if not remaining:break
   time.sleep(.1)
 finish=datetime.now(timezone.utc).isoformat()
 receipt=dict(base=base,code=code,pid=proc.pid,node_closed=not running(proc.pid),chromium_pids=sorted(seen),remaining_chromium=remaining,started=start,closed=finish,signature=stage['production'],driver_sha256=h((D/'four-downloads.cjs').read_bytes()),report_sha256=h((dst/'viewer.json').read_bytes()) if (dst/'viewer.json').is_file() else None)
 (dst/'closed.json').write_text(json.dumps(receipt,indent=2)+'\n')
 assert code==0 and receipt['node_closed'] and seen and not remaining,receipt
r=numeric(dst/'viewer.json');assert r['passed'] and r['base']==base and len(r['views'])==4 and not r['pageErrors'];assert {v['viewport']['width']for v in r['views']}=={390,1250}
bound={k:v['sha256']if isinstance(v,dict)else v for k,v in r['files'].items()};assert set(bound)=={'sihang-building.html','src/candidate-asset-viewer.js'} and all(fingerprints['viewer_inputs'][k]==v for k,v in bound.items())
for k,role in fingerprints['downloads'].items():assert r['downloads'][k]['sha256']==role['sha256']
for shot in r['views']:assert h((dst/shot['filename']).read_bytes())==shot['sha256']
print(len(r['views']),'real PNGs and',len(r['downloads']),'saved downloads')
