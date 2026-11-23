"""Run the true parent and each measured public input on the signed predecessor and successor city sites."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/270';parts=e/'separate'
if len(sys.argv)<2:raise SystemExit('Supply the signed actual predecessor browser exit receipt')
previous=Path(sys.argv[1]);assert previous.resolve()==Path('/tmp/shanghai-main-269/269-map-slot-released.json');del sys.argv[1]
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
handoff=read(previous)
assert handoff['order']==269 and handoff['exit_code']==0 and handoff['remaining_chromium']==[]
exit_code=next((handoff[k]for k in ('code','exit','exit_code','returncode')if k in handoff),None)
assert (exit_code==0 or (exit_code is None and handoff.get('passed') is True)) and not any(handoff.get(k)for k in ('remaining','remaining_chromium','remaining_processes')),(previous,handoff)
assert handoff.get('passed',True) is not False
stages=sys.argv[1:] or ['before','phone','desktop','details','architecture','closeups','distant']
if 'details' in stages and 'architecture' in stages and 'touch' not in stages:
 stages.insert(stages.index('details')+1,'touch')
if len(stages)>1:
 guest=Path('/tmp/gaolan335');prior=Path('/tmp/kemi334');highest=Path('/tmp/shanghai-yongjia-porch/scenes/335-comparison.json')
 def viewer_ready():
  return all(f.is_file() for f in (prior/'viewer-closed.json',guest/'native-closed.json',guest/'raw-335-confirmed.json',highest))
 def offer(kind):
  subprocess.run([sys.executable,'-Bu',w/'offer-335-recovered.py',kind],check=True)
  assert (w/f'335-{kind}-returned.json').is_file(),f'Actual 335 {kind} return is pending'
 offered=False
 for part in stages:
  subprocess.run([sys.executable,'-Bu',__file__,previous,part],check=True)
  if part=='before':offer('native')
  phone=parts/'phone/closed.json'
  if not offered and phone.is_file() and read(phone)['exit']==0 and viewer_ready():
   offer('viewer');offered=True
 if 'phone' in stages and not offered:
  while not viewer_ready():time.sleep(2)
  offer('viewer')
 sys.exit(0)
for n in [269,270]:
 b=read(w/f'{n}-bindings.json');assert b['production']==sha(w/f'{n}-production.json')
 assert all(sha(w/f'stage{n}'/path)==hashv for path,hashv in b['files'].items())
with (w/'browser.lock').open('a')as lock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
 fcntl.flock(lock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
 for part in stages:
  control=part=='before'
  dst=e/'before'if control else parts/part;dst.mkdir(parents=True,exist_ok=True)
  report=dst/('control-browser.json'if control else'main-browser.json')
  done=dst/'closed.json'
  if done.exists() and read(done).get('exit')!=0:
   old=dst.parent/(dst.name+'-failed-'+str(read(done).get('node','unknown')))
   assert not old.exists(),old
   dst.rename(old);dst.mkdir()
  if done.exists():
   q=read(done);assert q['exit']==0 and q['report_sha256']==sha(report);continue
  assert not report.exists(),part
  used=269 if control else 270
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/zhongken-bank-239-corner-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage270'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage269/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':str(read(w/'269-production.json')['resulting_count']),'QA_CONTROL_CATALOG_SHA256':read(w/'269-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19970'}
  registered=w/'check-zhongken-measured.cjs';f=dst/'actual-driver.cjs';f.write_bytes(registered.read_bytes())
  (dst/'candidate-audit-groups.cjs').write_bytes((w/'candidate-audit-groups.cjs').read_bytes())
  case=w/'case270.json';import socket
  with socket.socket()as probe:
   probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
  env.update(QA_CDP_PORT=str(port),QA_ANGLE_BACKEND='gl-egl',LIBGL_ALWAYS_SOFTWARE='1',GALLIVM_PERF='no_opt',LP_NATIVE_VECTOR_WIDTH='128',LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MALLOC_ARENA_MAX='1',QA_X11_SCANNER=str(w/'x11-scanlines'),QA_EVIDENCE_VOLUME='/dev/shm/270-city-live')
  (dst/'debug-port').write_text(str(port)+'\n')
  with tempfile.TemporaryDirectory(prefix='map270-'+part+'-',dir=max(('/tmp','/dev/shm','/run/codex-docker/user'),key=lambda path:__import__('shutil').disk_usage(path).free))as tmp,(dst/'run.log').open('w')as lg:
   proc=subprocess.Popen(['node',f,case]+(['--control']if control else []),env={**env,'TMPDIR':tmp},stdout=lg,stderr=subprocess.STDOUT);seen=set()
   while proc.poll() is None:
    import psutil
    try:
     for child in psutil.Process(proc.pid).children(recursive=True):
      try:
       if child.name() in ('chrome','chromium','headless_shell','chrome-headless-shell'):seen.add(child.pid)
      except (psutil.Error,FileNotFoundError):pass
    except psutil.NoSuchProcess:pass
    time.sleep(.18)
   active=[]
   for pid in seen:
    q=Path('/proc')/str(pid)/'stat'
    if q.exists()and q.read_text().rsplit(')',1)[1].split()[0]not in ('Z','X'):active.append(pid)
   with socket.socket()as closed_socket:
    cdp_closed=closed_socket.connect_ex(('127.0.0.1',port))!=0
   assert cdp_closed
   q=dict(debug_port=port,cdp_closed=cdp_closed,order=270,phase=part,exit_code=proc.returncode,remaining_chromium=active,report=str(report),exit=proc.returncode,node=proc.pid,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report)if report.is_file()else None,driver_sha256=sha(f),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active and report.is_file()
   if part in ('before','phone'):
    alias=w/'evidence'/part;alias.mkdir(exist_ok=True,parents=True)
    exported=alias/'closed.json'
    if not exported.exists():os.link(done,exported)
    assert sha(done)==sha(exported)
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'269-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')
