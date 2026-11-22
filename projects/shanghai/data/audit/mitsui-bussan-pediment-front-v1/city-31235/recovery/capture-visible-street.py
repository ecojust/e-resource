"""Run one documented city view or one authentic pointer entry, then wait for its actual Node and Chromium closure."""
from datetime import datetime,timezone
from pathlib import Path
from hashlib import sha256
import json,os,socket,subprocess,sys,time
work=Path(__file__).resolve().parent;ev=work/'isolated-evidence'
phases=['control','mobile-card','mobile-pin','desktop-card','desktop-pin','street','roof','plaque','pediment','distant']
stage='roof';read=lambda p:json.loads(p.read_bytes());sign=lambda p:sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
w=Path('/workspace/.e-resource-recovery/grace/reboot235');work=Path('/tmp/shanghai-main-235/formal-31235')
prior=Path('/tmp/xiaonanmen300/235-formal-viewer-returned.json');q=read(prior)
assert q['order']==300 and q['host']==235 and q['all_children_exited'] and not q['remaining_children']
prev={'path':str(prior),'sha256':sign(prior)}
out=work/'actual-readable-frontage';out.mkdir(exist_ok=True)
already=out/'closed.json'
if already.exists():
 rec=read(already);assert rec['exit_code']==0 and rec['report_sha256']==sign(Path(rec['report'])) and rec['predecessor']==prev;raise SystemExit()
temp=Path('/dev/shm/235-readable-frontage-profile');temp.mkdir(exist_ok=True)
driver=w/'source-registered-full-facade.cjs';assert sign(driver)=='a29066444fd00c36bd275b998d4a80349a102523ef54fba43b02a1a7adcbcb85'
source=Path('/workspace/e-resource/projects/shanghai/data/audit/mitsui-bussan-pediment-front-v1/map-case.json');args=['node',str(driver),str(source)]
pre=False;env=dict(os.environ,QA_PHASE=stage,TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(work/'stage235'),QA_CDP_PORT='19635',MODEL_BASE_URL='http://127.0.0.1:31235/',QA_OUTPUT_DIR=str(out),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
def processes():
 rows={}
 for proc in Path('/proc').glob('[0-9]*'):
  try:
   cmd=(proc/'cmdline').read_bytes().split(b'\0')
   if cmd and b'/usr/lib/chromium/chromium' in cmd and (str(temp).encode() in b' '.join(cmd) or b'--remote-debugging-port=19635' in cmd):
    rows[int(proc.name)]=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
  except OSError:pass
 return rows
def listening():
 with socket.socket()as s:return s.connect_ex(('127.0.0.1',19635))==0
import fcntl
lock=Path('/tmp/shanghai-standalone-viewer.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
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
rc=child.returncode;rpath=out/('control-browser.json'if pre else'main-browser.json');closed=dict(order=235,phase=stage,started=start,finished=now(),exit_code=rc,node_pid=child.pid,observed_chromium_pid_and_starttime=found,remaining_chromium=sorted(processes()),cdp_closed=not listening(),predecessor=prev,source_code_sha256=sign(driver),stdout_sha256=sign(log),report=str(rpath),report_sha256=sign(rpath)if rpath.is_file()else None)
assert not live and not closed['remaining_chromium'] and closed['cdp_closed']
closed.update(node_closed=child.poll() is not None,chromium_pids=sorted(int(k) for k in found),remaining=list(closed['remaining_chromium']))
if rc:
 (out/'failed-exit.json').write_text(json.dumps(closed,indent=2)+'\n');sys.exit(rc)
r=read(rpath);assert found and r['completed'] and not(r['failed']or r['errors']or r['warnings']);assert r['phase']==stage and r['server']==env['MODEL_BASE_URL'];assert len(r['screenshots'])==3 and r['scriptSha256']==closed['source_code_sha256'];assert all(sign(out/x['file'])==x['sha256']for x in r['screenshots'])
if stage in ['mobile-pin','desktop-pin']:
 b,=r['realBeaconInputs'];e=b['pointer'];assert e['trusted']and e['on_canvas']and e['type']==('touch'if stage=='mobile-pin'else'mouse')and b['landed']==pin['id']
(out/'closed.json').write_text(json.dumps(closed,indent=2)+'\n');print(stage,closed['finished'],found)
