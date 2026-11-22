"""Run both public viewer sizes and four downloads against the final 31k entry."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
from urllib.request import urlopen
import argparse,json,os,fcntl,sys,subprocess,tempfile,time,psutil
p=argparse.ArgumentParser();p.add_argument('--assigned-standalone-slot',action='store_true',required=True);p.parse_args()
D=Path(__file__).resolve().parent;P=Path('/workspace/e-resource/projects/shanghai');a=P/'data/audit/yuanfang-railway-corner-v1';dst=D/'viewer-31249';dst.mkdir(exist_ok=True);h=lambda b:sha256(b).hexdigest();numeric=lambda f:json.loads(f.read_bytes())
stage=numeric(D/'249-bindings.json');port=stage['port'];base=f'http://127.0.0.1:{port}/';assert port==31249
fingerprints=numeric(D/'two-transitions.json')['249'];current=numeric(Path('/tmp/shanghai-yongjia-porch/scenes/249-comparison.json'));assert current['production_receipt_sha256']==stage['production'] and current['passed']
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 start=datetime.now(timezone.utc).isoformat()
 env={**os.environ,'MODEL_BASE_URL':base,'SHANGHAI_PROJECT_ROOT':str(D/'stage249'),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
 with tempfile.TemporaryDirectory(prefix='viewer249-',dir=max(('/tmp','/dev/shm','/run/codex-docker/user'),key=lambda p:__import__('shutil').disk_usage(p).free))as temp:
  env['TMPDIR']=temp
  proc=subprocess.Popen(['node','-r',D/'keep-four-saves.cjs','-r',P/'data/audit/brunner-mond-v1/viewer-timeout.cjs',D/'formal-viewer.cjs','huangpu-yuanfang-lane-railway-corner',dst],cwd=P,env=env)
  seen=set()
  while proc.poll() is None:
   try:queue=[proc.pid];checked=set()
   except ProcessLookupError:break
   while queue:
    pid=queue.pop()
    if pid in checked:continue
    checked.add(pid)
    try:
     cmd=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
     if cmd and os.path.basename(cmd[0]) in (b'chrome',b'chromium',b'headless_shell',b'chrome-headless-shell'):seen.add(pid)
     queue.extend(child.pid for child in psutil.Process(pid).children())
    except (FileNotFoundError,ProcessLookupError,psutil.NoSuchProcess):continue
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
 receipt=dict(base=base,code=code,pid=proc.pid,node_closed=not running(proc.pid),chromium_pids=sorted(seen),remaining_chromium=remaining,started=start,closed=finish,signature=stage['production'],driver_sha256=h((D/'formal-viewer.cjs').read_bytes()),report_sha256=h((dst/'viewer.json').read_bytes()) if (dst/'viewer.json').is_file() else None)
 (dst/'closed.json').write_text(json.dumps(receipt,indent=2)+'\n')
 assert code==0 and receipt['node_closed'] and seen and not remaining,receipt
r=numeric(dst/'viewer.json');assert r['passed'] and r['base']==base and len(r['views'])==6 and not r['pageErrors'];assert {v['viewport']['width']for v in r['views']}=={390,1250}
bound={k:v['sha256']if isinstance(v,dict)else v for k,v in r['files'].items()};assert bound==fingerprints['viewer_inputs']
proof=numeric(D/'formal-viewer-sources.json')
assert proof['production_sha256']==stage['production']==r['productionSHA256'] and r['formalInputs']==proof['inputs']
assert r['scriptSHA256']==proof['driver_sha256']==h((D/'formal-viewer.cjs').read_bytes())
assert set(r['downloads'])==set(fingerprints['downloads'])=={'raw','full','lod','native'}
for k,role in fingerprints['downloads'].items():
 item=r['downloads'][k];assert item['saveAsVerified'] and item['bytes']==role['bytes'] and item['sha256']==role['sha256'] and item['file']==Path(role['file']).name
for shot in r['views']:assert h((dst/shot['filename']).read_bytes())==shot['sha256']
print(len(r['views']),'real PNGs and',len(r['downloads']),'saved downloads')

for item in r['downloads'].values():
 saved=dst/'saved'/item['file'];assert saved.stat().st_size==item['bytes'] and h(saved.read_bytes())==item['sha256']
