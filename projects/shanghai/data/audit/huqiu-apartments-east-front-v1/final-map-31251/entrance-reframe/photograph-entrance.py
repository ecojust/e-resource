from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import json,os,socket,subprocess,sys,time,fcntl,tempfile
work=Path('/tmp/shanghai-main-251/final-map-31251')
stage='architecture';pre=False;origin=31251
read=lambda p:json.loads(p.read_bytes());sign=lambda p:sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
closing=work/'current-standalone/closed.json'
previous=Path('/workspace/.e-resource-recovery/root/jingan-596-study/development-native/early-development-returned.json')
result=read(previous);assert result['passed'] and result['exit_code']==0 and result['host']==251 and result['host_sha256']==sign(closing) and result['all_children_exited'] and not result['remaining_children']
gate=Path('/tmp/shanghai-standalone-viewer.lock').open('a');fcntl.flock(gate,fcntl.LOCK_EX)
prev={'path':str(previous),'sha256':sign(previous)}
out=work/'entrance-reframe';out.mkdir(exist_ok=True)
if (out/'closed.json').is_file():raise SystemExit(0)
temp=Path(tempfile.mkdtemp(prefix='p251-entrance-',dir='/run/codex-docker/user'))
args=['node',str(work/'east-entrance.cjs'),'/workspace/e-resource/projects/shanghai/data/audit/huqiu-apartments-east-front-v1/map-case.json',stage]
env=dict(os.environ,QA_PHASE=stage,TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT='/dev/shm/city-251-actual/251',QA_CDP_PORT='19551',MODEL_BASE_URL='http://127.0.0.1:31251/',QA_OUTPUT_DIR=str(out),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
def processes():
 rows={}
 for proc in Path('/proc').glob('[0-9]*'):
  try:
   cmd=(proc/'cmdline').read_bytes().split(b'\0')
   if cmd and b'/usr/lib/chromium/chromium' in cmd and (str(temp).encode() in b' '.join(cmd) or b'--remote-debugging-port=19551' in cmd):
    rows[int(proc.name)]=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
  except OSError:pass
 return rows
def listening():
 with socket.socket()as s:return s.connect_ex(('127.0.0.1',19551))==0
assert not listening() and not processes()
log=out/'node.log';assert not log.exists();start=now();found={}
with log.open('xb')as handle:
 child=subprocess.Popen(args,env=env,stdout=handle,stderr=subprocess.STDOUT)
 while child.poll()is None:
  found.update(processes())
  import psutil
  try: descendants=psutil.Process(child.pid).children(recursive=True)
  except psutil.Error:descendants=[]
  for descendant in descendants:
   try:
    if descendant.name() in ('chrome','chromium','chrome_crashpad_handler'):
     stat=(Path('/proc')/str(descendant.pid)/'stat').read_text().rsplit(')',1)[1].split();found[descendant.pid]=stat[19]
   except (OSError,psutil.Error):pass
  time.sleep(.18)
for tick in range(50):
 live=[]
 for pid,birth in found.items():
  try:
   st=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
   if st[19]==birth and st[0]!='Z':live.append(pid)
  except OSError:pass
 if not listening() and not processes() and not live:break
 time.sleep(.15)
rc=child.returncode;rpath=out/('control-browser.json'if pre else'main-browser.json');closed=dict(order=251,phase=stage,started=start,finished=now(),exit_code=rc,node_pid=child.pid,observed_chromium_pid_and_starttime=found,remaining_chromium=sorted(processes()),cdp_closed=not listening(),predecessor=prev,source_code_sha256=sign(work/'east-entrance.cjs'),stdout_sha256=sign(log),report=str(rpath),report_sha256=sign(rpath)if rpath.is_file()else None)
assert not live and not closed['remaining_chromium'] and closed['cdp_closed']
closed.update(node_closed=child.poll() is not None,exit=rc,actual_origin=origin,port=origin,chromium_pids=sorted(int(k) for k in found),remaining=list(closed['remaining_chromium']))
if rc:
 (out/'failed-exit.json').write_text(json.dumps(closed,indent=2)+'\n');sys.exit(rc)
r=read(rpath);assert found and r['completed'] and not(r['failed']or r['errors']or r['warnings']);assert r['phase']==stage and r['server']==env['MODEL_BASE_URL'];assert len(r['screenshots'])==4 and r['scriptSha256']==closed['source_code_sha256'];assert all(sign(out/x['file'])==x['sha256']for x in r['screenshots'])
assert len(r['views'])==2 and len(r['ground'])==76 and all(p['found']==p['expected'] for p in r['ground'])
(out/'closed.json').write_text(json.dumps(closed,indent=2)+'\n');print(closed['report_sha256'],flush=True)
