"""Run the true parent and each measured public input on the signed predecessor and successor city sites."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/211';parts=e/'separate'
if len(sys.argv)<2:raise SystemExit('Supply the signed actual predecessor browser exit receipt')
previous=Path(sys.argv[1]);assert previous.resolve()==Path('/tmp/liberty210/210-map-slot-released.json');del sys.argv[1]
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
handoff=read(previous)
assert handoff['order']==210 and handoff['exit_code']==0 and handoff['remaining_chromium']==[]
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
   subprocess.run([sys.executable,'-Bu',w/'offer-276.py','native' if part=='before' else 'viewer'],check=True)
 sys.exit(0)
if stages==['touch']:
 subprocess.run([sys.executable,'-Bu',w/'offer-cpu-325.py'],check=True)
if stages==['details']:
 subprocess.run([sys.executable,'-Bu',w/'after-desktop-guest-window.py'],check=True)
for n in [210,211]:
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
   q=read(done);assert q['exit']==0 and q['report_sha256']==sha(report);continue
  assert not report.exists(),part
  used=210 if control else 211
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/midget-apartments-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage211'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage210/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':str(read(w/'210-production.json')['resulting_count']),'QA_CONTROL_CATALOG_SHA256':read(w/'210-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19711'}
  f=w/'check-211-separated.cjs';case=w/'case211.json'
  with tempfile.TemporaryDirectory(prefix='map211-'+part+'-',dir=max(('/tmp','/dev/shm'),key=lambda path:__import__('shutil').disk_usage(path).free))as tmp,(dst/'run.log').open('w')as lg:
   proc=subprocess.Popen(['node',f,case]+(['--control']if control else []),env={**env,'TMPDIR':tmp},stdout=lg,stderr=subprocess.STDOUT);seen=set()
   import psutil
   births={}
   while proc.poll() is None:
    try:
     for child in psutil.Process(proc.pid).children(recursive=True):
      try:
       if child.name() in ('chromium','chrome','chrome-headless-shell','headless_shell'):
        births[child.pid]=child.create_time()
      except psutil.Error:continue
    except psutil.Error:pass
    time.sleep(.15)
   seen=set(births)
   def survivors():
    active=[]
    for pid,born in births.items():
     try:
      child=psutil.Process(pid)
      if child.create_time()==born and child.status()!=psutil.STATUS_ZOMBIE:active.append(pid)
     except psutil.NoSuchProcess:pass
    return active
   for _ in range(40):
    if not survivors():break
    time.sleep(.1)
   active=survivors()
   q=dict(exit=proc.returncode,node=proc.pid,observed_chromium_births=births,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report)if report.is_file()else None,driver_sha256=sha(f),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active and report.is_file()
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'210-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')
