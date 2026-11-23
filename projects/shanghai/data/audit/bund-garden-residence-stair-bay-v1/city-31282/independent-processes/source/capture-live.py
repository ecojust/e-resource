"""Run one documented city view or one authentic pointer entry, then wait for its actual Node and Chromium closure."""
from datetime import datetime,timezone
from pathlib import Path
from hashlib import sha256
import json,os,socket,subprocess,sys,time
work=Path(__file__).resolve().parent;driver=work/'check-stair-field.cjs';ev=work/'isolated-evidence'
phases=['control','mobile-card','mobile-pin','desktop-card','desktop-pin','street','roof','lower-stair-windows','upper-stair-windows','distant']
stage=sys.argv[1];driver=work/'check-stair-field.cjs';assert stage in phases;read=lambda p:json.loads(p.read_bytes());sign=lambda p:sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
pin=read(work/'isolated-inputs.json');__import__('frozen_inputs').verify(work)
ev.mkdir(exist_ok=True);out=ev/stage;out.mkdir(exist_ok=True);assert not (out/'closed.json').exists()
index=phases.index(stage)
if index:
 prior=ev/phases[index-1]/'closed.json';r=read(prior);assert r['exit_code']==0 and not r['remaining_chromium'] and sign(Path(r['report']))==r['report_sha256'];prev={'path':str(prior),'sha256':sign(prior)}
else:
 previous=Path(sys.argv[2]).resolve();subprocess.run([sys.executable,'-B',work/'check-parent-281-live.py',previous],check=True);prior=read(previous);assert previous.is_file() and '281' in str(previous) and (prior.get('passed',False) or prior.get('all_captures_visually_reviewed') or prior.get('visually_reviewed') or prior.get('actual_process_exits') or prior.get('physical_exits') or prior.get('all_closed') or prior.get('exit_code')==0 or prior.get('order')==281);prev={'path':str(previous),'sha256':sign(previous)}
import tempfile,shutil
tempbase=Path('/dev/shm/hankou282-live/profiles');profile=tempfile.TemporaryDirectory(prefix='p-',dir=tempbase);temp=Path('/tmp/g80/work/hankou282/profiles')/Path(profile.name).name
shutil.copyfile(driver,out/'actual-driver.cjs');source=work/'case282.json'
args=['nsenter','--preserve-credentials','--user','--mount','--target','3609719','--','node',*(['--jitless','--optimize-for-size'] if stage in phases else []),'--preserve-symlinks-main',str(driver),str(source)]
pre=stage=='control';origin=31281 if pre else 31282;env=dict(os.environ,QA_PHASE=stage,TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT='/tmp/g80/work/hankou282/bank/282',QA_CDP_PORT='19582',MODEL_BASE_URL='http://127.0.0.1:'+str(origin)+'/',QA_OUTPUT_DIR='/tmp/g80/work/hankou282/evidence/'+stage,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
env.update(NODE_OPTIONS='--max-old-space-size=76 --max-semi-space-size=1',QA_X11_SCANNER='/dev/shm/pavilion273/x11-scanlines',XDG_CONFIG_HOME=str(temp/'cfg'),XDG_CACHE_HOME=str(temp/'ca'),CHROME_CONFIG_HOME=str(temp/'cfg'),QA_ANGLE_BACKEND='swiftshader',LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',MESA_SHADER_CACHE_DISABLE='true',MALLOC_ARENA_MAX='1',LP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
env.update(MALLOC_TRIM_THRESHOLD_='65536',MALLOC_MMAP_THRESHOLD_='131072')
if pre or stage in ('desktop-pin','distant'):env.update(QA_ANGLE_BACKEND='gl-egl',LP_NATIVE_VECTOR_WIDTH='128',GALLIVM_PERF='no_opt')
if pre:env.update(QA_CONTROL_CATALOG='/tmp/g80/work/hankou282/bank/281/data/candidate-city-integrations.json',QA_CONTROL_CATALOG_SHA256=read(work/'signed-comparison.json')['stages'][0]['catalog_sha256'],QA_CONTROL_CITY_COUNT='316')
def processes():
 rows={}
 for proc in Path('/proc').glob('[0-9]*'):
  try:
   cmd=(proc/'cmdline').read_bytes().split(b'\0')
   if cmd and b'/usr/lib/chromium/chromium' in cmd and (str(temp).encode() in b' '.join(cmd) or b'--remote-debugging-port=19582' in cmd):
    rows[int(proc.name)]=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
  except OSError:pass
 return rows
def listening():
 with socket.socket()as s:return s.connect_ex(('127.0.0.1',19582))==0
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
rc=child.returncode;rpath=out/('control-browser.json'if pre else'main-browser.json');closed=dict(order=282,phase=stage,started=start,finished=now(),exit_code=rc,node_pid=child.pid,observed_chromium_pid_and_starttime=found,remaining_chromium=sorted(processes()),cdp_closed=not listening(),predecessor=prev,source_code_sha256=sign(driver),stdout_sha256=sign(log),report=str(rpath),report_sha256=sign(rpath)if rpath.is_file()else None)
assert not live and not closed['remaining_chromium'] and closed['cdp_closed']
closed.update(driver_sha256=sign(driver),node_closed=child.poll() is not None,exit=rc,actual_origin=origin,port=origin,chromium_pids=sorted(int(k) for k in found),remaining=list(closed['remaining_chromium']))
if rc:
 (out/'failed-exit.json').write_text(json.dumps(closed,indent=2)+'\n');sys.exit(rc)
r=read(rpath);assert found and r['completed'] and not(r['failed']or r['errors']or r['warnings']);assert r['phase']==stage and r['server']==env['MODEL_BASE_URL'];assert len(r['screenshots'])==1 and r['scriptSha256']==closed['source_code_sha256'];assert all(sign(out/x['file'])==x['sha256']for x in r['screenshots'])
if stage in ['mobile-pin','desktop-pin']:
 b,=r['realBeaconInputs'];e=b['pointer'];assert e['trusted']and e['on_canvas']and e['type']==('touch'if stage=='mobile-pin'else'mouse')and b['landed']==pin['id']
(out/'closed.json').write_text(json.dumps(closed,indent=2)+'\n');print(stage,closed['finished'],found)
