"""Run one documented city view or one authentic pointer entry, then wait for its actual Node and Chromium closure."""
from datetime import datetime,timezone
from pathlib import Path
from hashlib import sha256
import json,os,socket,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from nanshi_runtime import HOST,live_inputs,writable_area
import atexit,fcntl,tempfile
work=HOST;ev=work/'isolated-evidence'
phases=['control','mobile-card','mobile-pin','desktop-card','desktop-pin','street','roof','clock','central-arch','distant']
stage=sys.argv[1]
if stage=='--check-static':
    with live_inputs() as (root,rows):
        for order in (261,262):
            name=root/str(order)/'data/candidate-city-integrations.json'
            output=subprocess.check_output(['node','-e', "process.stdout.write(require('fs').readFileSync(process.argv[1]))",str(name)])
            assert sha256(output).hexdigest()==next(x['sha256'] for x in rows if x['stage']==order and x['file'].endswith('candidate-city-integrations.json'))
        saved=Path(__file__).resolve().parent/'measured-input-check.json'
        saved.write_text(json.dumps({'order':262,'checks':rows,'stage_order':phases,'browser_started':False},indent=2)+'\n')
    sys.exit(0)
assert stage in phases;read=lambda p:json.loads(p.read_bytes());sign=lambda p:sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
if stage == 'control':
    terminal = Path('/tmp/shanghai-main-261/261-map-slot-released.json')
    source = Path('/tmp/shanghai-main-261/final-map-31261/standalone-replay.json')
    wait_for = Path('/tmp/yangpu-music-440-history/development-native/261-development-returned.json')
    while not wait_for.is_file():time.sleep(3)
    returned = read(wait_for)
    assert (returned['order'],returned['host'])==(440,261)
    assert returned['previous_sha256']==sign(terminal) and returned['host_sha256']==sign(source)
    host = read(terminal)
    assert host['standalone_replay']['sha256']==sign(source)
    assert sign(Path(host['standalone_replay']['report']))==returned['host_report_sha256']
    signed = host['development_437']
    assert sign(Path(signed['receipt']))==signed['sha256'] and signed['outcome']['all_children_exited'] and not signed['outcome']['remaining_children']
    physical = Path(returned['physical'])
    assert physical.samefile(wait_for.parent/'physical.json') and sign(physical)==returned['physical_sha256']
    result=read(physical)
    assert result['exit_code']==returned['exit_code'] and result['passed']==returned['passed']
    assert result['all_children_exited'] and not result['remaining_children'] and returned['all_children_exited'] and returned['remaining_children']==[]
    assert returned['exit_code']==0 and returned['passed'] and result['passed']
    tail=Path('/workspace/.e-resource-recovery/root/jingan-636-study/development-native/early-development-returned.json')
    while not tail.is_file():time.sleep(3)
    tail_result=read(tail)
    assert (tail_result['host'],tail_result['order'],tail_result['exit_code'])==(261,636,0) and tail_result['passed']
    assert tail_result['host_sha256']==sign(terminal) and tail_result['all_children_exited'] and not tail_result['remaining_children']
    physics=Path(tail_result['physical'])
    assert physics.samefile(tail.parent/'physical.json') and sign(physics)==tail_result['physical_sha256'] and read(physics)['passed']
pin=read(work/'isolated-inputs.json');assert all(sign(work/file)==digest for file,digest in pin['frozen_program_and_inputs'].items())
ev.mkdir(exist_ok=True);out=ev/stage;out.mkdir(exist_ok=True)
index=phases.index(stage)
if index:
 prior=ev/phases[index-1]/'closed.json';r=read(prior);assert r['exit_code']==0 and not r['remaining_chromium'] and sign(Path(r['report']))==r['report_sha256'];prev={'path':str(prior),'sha256':sign(prior)}
else:
 previous=Path(sys.argv[2]).resolve();prior=read(previous);assert previous.is_file() and '261' in str(previous) and (prior.get('passed',False) or prior.get('all_captures_visually_reviewed') or prior.get('visually_reviewed') or prior.get('actual_process_exits') or prior.get('physical_exits') or prior.get('all_closed') or prior.get('exit_code')==0 or prior.get('order')==261);prev={'path':str(previous),'sha256':sign(previous)}
profile=tempfile.TemporaryDirectory(prefix='profile-',dir=writable_area());atexit.register(profile.cleanup);temp=Path(profile.name);source=Path('/workspace/e-resource/projects/shanghai/data/audit/nanshi-telephone-clock-front-v1/map-case.json')
args=['node',str(work/'check-nanshi-telephone-measured.cjs'),str(source)]
inputs=live_inputs();bind,manifest=inputs.__enter__();atexit.register(inputs.__exit__,None,None,None)
with socket.socket() as selection:
 selection.bind(('127.0.0.1',0)); debug_port=selection.getsockname()[1]
pre=stage=='control';origin=31261 if pre else 31262;env=dict(os.environ,QA_PHASE=stage,TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(bind/'262'),QA_CDP_PORT=str(debug_port),MODEL_BASE_URL='http://127.0.0.1:'+str(origin)+'/',QA_OUTPUT_DIR=str(out),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
if pre:env.update(QA_CONTROL_CATALOG=str(bind/'261/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=read(work/'signed-comparison.json')['stages'][0]['catalog_sha256'],QA_CONTROL_CITY_COUNT='296')
def processes():
 rows={}
 for proc in Path('/proc').glob('[0-9]*'):
  try:
   cmd=(proc/'cmdline').read_bytes().split(b'\0')
   if cmd and b'/usr/lib/chromium/chromium' in cmd and (str(temp).encode() in b' '.join(cmd) or f'--remote-debugging-port={debug_port}'.encode() in cmd):
    rows[int(proc.name)]=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
  except OSError:pass
 return rows
def listening():
 with socket.socket()as s:return s.connect_ex(('127.0.0.1',debug_port))==0
assert not listening() and not processes()
if (out/'closed.json').is_file():
 old=read(out/'closed.json')
 assert old['phase']==stage and old['exit_code']==0 and old['source_code_sha256']==sign(out/'actual-driver.cjs')
 assert old['predecessor']==prev and sign(Path(old['report']))==old['report_sha256'] and not old['remaining_chromium'] and old['cdp_closed']
 assert old['frame_check_sha256']==sign(out/'frame-check.json')
 sys.exit(0)
if any(out.iterdir()):
 hist=work/'isolated-attempts';hist.mkdir(exist_ok=True)
 target=hist/f'{stage}-{time.time_ns()}';out.rename(target);out.mkdir()
 evidence=[dict(name=p.name,sha256=sign(p)) for p in sorted(target.iterdir()) if p.is_file()]
 (target/'retained-at-reentry.json').write_text(json.dumps({'phase':stage,'retained':evidence},indent=2)+'\n')
env['NODE_OPTIONS']='--max-old-space-size=135 --max-semi-space-size=1'
launch_driver_sha256=sign(work/'check-nanshi-telephone-measured.cjs')
source_copy=out/'actual-driver.cjs'
source_copy.write_bytes((work/'check-nanshi-telephone-measured.cjs').read_bytes())
assert sign(source_copy)==launch_driver_sha256
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
rc=child.returncode;rpath=out/('control-browser.json'if pre else'main-browser.json');closed=dict(order=262,phase=stage,debug_port=debug_port,started=start,finished=now(),exit_code=rc,node_pid=child.pid,observed_chromium_pid_and_starttime=found,remaining_chromium=sorted(processes()),cdp_closed=not listening(),predecessor=prev,source_code_sha256=launch_driver_sha256,stdout_sha256=sign(log),report=str(rpath),report_sha256=sign(rpath)if rpath.is_file()else None)
assert not live and not closed['remaining_chromium'] and closed['cdp_closed']
closed.update(node_closed=child.poll() is not None,exit=rc,actual_origin=origin,port=origin,chromium_pids=sorted(int(k) for k in found),remaining=list(closed['remaining_chromium']))
if rc:
 (out/'failed-exit.json').write_text(json.dumps(closed,indent=2)+'\n');sys.exit(rc)
r=read(rpath);assert found and r['completed'] and not(r['failed']or r['errors']or r['warnings']);assert r['phase']==stage and r['server']==env['MODEL_BASE_URL'];assert len(r['screenshots'])==1 and r['scriptSha256']==closed['source_code_sha256'];assert all(sign(out/x['file'])==x['sha256']for x in r['screenshots'])
if stage in ['mobile-pin','desktop-pin']:
 b,=r['realBeaconInputs'];e=b['pointer'];assert e['trusted']and e['on_canvas']and e['type']==('touch'if stage=='mobile-pin'else'mouse')and b['landed']==pin['id']
subprocess.run([sys.executable,'-B',work/'verify-map-frames.py',rpath,out/'frame-check.json'],check=True)
closed['frame_check_sha256']=sign(out/'frame-check.json')
(out/'closed.json').write_text(json.dumps(closed,indent=2)+'\n');print(stage,closed['finished'],found)
