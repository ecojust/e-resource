"""Run the true parent and each measured public input on the signed predecessor and successor city sites."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/253';parts=e/'separate'
if len(sys.argv)<2:raise SystemExit('Supply the signed actual predecessor browser exit receipt')
previous=Path(sys.argv[1]);assert previous.resolve()==Path('/tmp/shanghai-main-252/252-map-slot-released.json');del sys.argv[1]
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
handoff=read(previous)
assert handoff['order']==252 and handoff['exit_code']==0 and handoff['remaining_chromium']==[]
exit_code=next((handoff[k]for k in ('code','exit','exit_code','returncode')if k in handoff),None)
assert (exit_code==0 or (exit_code is None and handoff.get('passed') is True)) and not any(handoff.get(k)for k in ('remaining','remaining_chromium','remaining_processes')),(previous,handoff)
assert handoff.get('passed',True) is not False
stages=sys.argv[1:] or ['before','phone','desktop','details','architecture','closeups','distant']
if 'details' in stages and 'architecture' in stages and 'touch' not in stages:
 stages.insert(stages.index('details')+1,'touch')
if len(stages)>1:
 for part in stages:
  subprocess.run([sys.executable,'-Bu',__file__,previous,part],check=True)
  if part in ('before','phone'):
   subprocess.run([sys.executable,'-Bu',w/'offer-318-after-restart.py','native' if part=='before' else 'viewer'],check=True)
 sys.exit(0)
for n in [252,253]:
 b=read(w/f'{n}-bindings.json');assert b['production']==sha(w/f'{n}-production.json')
 assert all(sha(w/f'stage{n}'/path)==hashv for path,hashv in b['files'].items())
with (w/'browser.lock').open('a')as lock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
 fcntl.flock(lock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
 for part in stages:
  control=part=='before'
  dst=e/'before'if control else parts/part;dst.mkdir(parents=True,exist_ok=True)
  report=dst/('control-browser.json'if control else'main-browser.json')
  done=dst/'closed.json'
  if done.exists():
   q=read(done);assert q['exit']==0 and q['report_sha256']==sha(report) and read(report)['completed'] and read(report)['screenshots'];continue
  assert not report.exists(),part
  used=252 if control else 253
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/hengye-li-jiangxi-corner-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage253'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage252/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':str(read(w/'252-production.json')['resulting_count']),'QA_CONTROL_CATALOG_SHA256':read(w/'252-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19753'}
  f=w/('check-253-settled-display.cjs' if part=='details' else 'check-253-near-marker.cjs' if part=='touch' else 'check-253-compositor.cjs' if part=='phone' else 'check-253-serial-candidates.cjs' if part=='before' else 'check-253-display-http.cjs');case=w/'case253.json'
  with tempfile.TemporaryDirectory(prefix='map253-'+part+'-',dir=max(('/tmp','/dev/shm','/run/codex-docker/user'),key=lambda path:__import__('shutil').disk_usage(path).free))as tmp,(dst/'run.log').open('w')as lg:
   proc=subprocess.Popen(['node',f,case]+(['--control']if control else []),env={**env,'TMPDIR':tmp},stdout=lg,stderr=subprocess.STDOUT);seen=set()
   while proc.poll() is None:
    import psutil
    try:
     for child in psutil.Process(proc.pid).children(recursive=True):
      try:
       if child.name() in ('chrome','chromium','headless_shell','chrome-headless-shell'):seen.add(child.pid)
      except psutil.Error:pass
    except psutil.NoSuchProcess:pass
    time.sleep(.18)
   active=[]
   for pid in seen:
    q=Path('/proc')/str(pid)/'stat'
    if q.exists()and q.read_text().rsplit(')',1)[1].split()[0]not in ('Z','X'):active.append(pid)
   q=dict(order=253,phase=part,exit_code=proc.returncode,remaining_chromium=active,report=str(report),exit=proc.returncode,node=proc.pid,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report)if report.is_file()else None,driver_sha256=sha(f),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active and report.is_file()
   captured=read(report);assert captured['completed'] and captured['section']==part and captured['screenshots'] and not captured['errors'] and not captured['failed']
   if part in ('before','phone'):
    alias=w/'evidence'/part;alias.mkdir(exist_ok=True,parents=True)
    exported=alias/'closed.json'
    if not exported.exists():
     try:os.link(done,exported)
     except OSError as err:
      if err.errno!=18:raise
      exported.symlink_to(done.resolve())
    assert sha(done)==sha(exported)
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'252-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')

if stages==['details']:
 task=Path('/tmp/nanshi578/after-253.py');assert sha(task)=='3f6d008208994fdd5a08dd92c7bbd363bdf251f41d53ab5d122333d5e79092b9'
 actual=parts/'details'/'closed.json'
 subprocess.run([sys.executable,'-Bu',task,actual],check=True)
 returned=read(task.parent/'253-native-returned.json')
 assert (returned['order'],returned['host'],returned['phase'])==(578,253,'details') and returned['passed']
 assert returned['host_sha256']==sha(actual) and returned['host_report_sha256']==sha(actual.with_name('main-browser.json'))
 assert returned['all_children_exited'] and returned['remaining_children']==[] and len(returned['phases'])==2
 for item in returned['phases']:
  assert item['physical_sha256']==sha(Path(item['physical']))
