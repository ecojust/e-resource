"""Run the true parent and each measured public input on the signed predecessor and successor city sites."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/283';parts=e/'separate'
if len(sys.argv)<2:raise SystemExit('Supply the signed actual predecessor browser exit receipt')
previous=Path(sys.argv[1]);assert previous.resolve()==Path('/tmp/shanghai-main-282/282-map-slot-released.json');del sys.argv[1]
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
handoff=read(previous)
assert handoff['order']==282 and handoff['exit_code']==0 and handoff['remaining_chromium']==[]
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
   kind='native' if part=='before' else 'viewer'
   if not any((w/f'348-{kind}-{state}.json').is_file() for state in ('returned','deferred')):subprocess.run([sys.executable,'-Bu',w/'offer-348-live.py',kind],check=True)
 sys.exit(0)
for n in [282,283]:
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
   q=read(done);prior=read(report)
   assert q['exit']==0 and q['node_closed'] and q['chromium_pids'] and q['remaining']==[] and q['report_sha256']==sha(report)
   assert prior['completed'] and prior['section']==part and not prior['errors'] and not prior['failed'] and not prior.get('failure')
   continue
  assert not report.exists(),part
  used=282 if control else 283
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/russell-company-fuzhou-three-bay-front-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage283'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage282/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':str(read(w/'282-production.json')['resulting_count']),'QA_CONTROL_CATALOG_SHA256':read(w/'282-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19763'}
  f=w/('check-283-live.cjs' if part=='before' else 'check-desktop-283.cjs' if part=='desktop' else 'check-street-283.cjs' if part=='phone' else 'check-touch-reload-283.cjs' if part=='touch' else 'check-beacon-283.cjs' if part=='details' else 'check-feature-pair-283.cjs' if part in ('architecture','closeups') else 'check-283-field.cjs');__import__('shutil').copyfile(f,dst/'actual-driver.cjs');case=w/'case283.json'
  env.update(QA_X11_SCANNER='/dev/shm/pavilion273/x11-scanlines',QA_ANGLE_BACKEND='swiftshader',MALLOC_ARENA_MAX='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',LP_NUM_THREADS='1')
  if part in ('phone','desktop'):
   env.update(QA_ANGLE_BACKEND='swiftshader',QA_X11_SCANNER='/dev/shm/pavilion273/x11-scanlines',LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='1',LP_NATIVE_VECTOR_WIDTH='128',GALLIVM_PERF='no_opt',MALLOC_ARENA_MAX='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
  with tempfile.TemporaryDirectory(prefix='p-',dir='/dev/shm/russell283-live/profiles')as tmp,(dst/'run.log').open('w')as lg:
   short='/tmp/g80/work/russell283/profiles/'+Path(tmp).name
   env.update(QA_OUTPUT_DIR='/tmp/g80/work/russell283/'+str(dst.relative_to(w)),SHANGHAI_PROJECT_ROOT='/tmp/g80/work/russell283/bank/283',QA_CONTROL_CATALOG='/tmp/g80/work/russell283/bank/282/data/candidate-city-integrations.json',XDG_CACHE_HOME=short+'/ca',XDG_CONFIG_HOME=short+'/cfg',CHROME_CONFIG_HOME=short+'/cfg',NODE_OPTIONS='--max-old-space-size=82 --max-semi-space-size=1',QA_ANGLE_BACKEND='swiftshader',GALLIUM_DRIVER='llvmpipe',LIBGL_ALWAYS_SOFTWARE='1',MESA_SHADER_CACHE_DISABLE='true',LP_NATIVE_VECTOR_WIDTH='128',GALLIVM_PERF='no_opt')
   proc=subprocess.Popen(['nsenter','--preserve-credentials','--user','--mount','--target','3609719','--','node',*(['--expose-gc'] if part=='distant' else ['--jitless']),'--optimize-for-size','--preserve-symlinks-main',f,case]+(['--control']if control else []),env={**env,'TMPDIR':short},stdout=lg,stderr=subprocess.STDOUT);seen=set()
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
   q=dict(order=283,phase=part,exit_code=proc.returncode,remaining_chromium=active,report=str(report),exit=proc.returncode,node=proc.pid,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report)if report.is_file()else None,driver_sha256=sha(f),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active and report.is_file()
   current=read(report);assert current['completed'] and current['section']==part and not current['errors'] and not current['failed'] and not current.get('failure')
   if part in ('before','phone'):
    alias=w/'evidence'/part;alias.mkdir(exist_ok=True,parents=True)
    exported=alias/'closed.json'
    if not exported.exists():os.link(done,exported)
    assert sha(done)==sha(exported)
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'282-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')
