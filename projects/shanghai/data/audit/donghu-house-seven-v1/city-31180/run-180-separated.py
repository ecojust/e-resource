"""Run the true parent and each measured public input on the 217-place site."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/180';parts=e/'separate';end179=w/'evidence/179/slot-released.json'
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert read(end179)['passed'] and read(end179)['views_reviewed']
for n in [179,180]:
 b=read(w/f'{n}-bindings.json');assert b['production']==sha(w/f'{n}-production.json')
 assert all(sha(w/f'stage{n}'/path)==hashv for path,hashv in b['files'].items())
with (w/'browser.lock').open('a')as lock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
 fcntl.flock(lock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
 for part in (sys.argv[1:] or ['before','phone','desktop','details','distant']):
  control=part=='before'
  dst=e/'before'if control else parts/part;dst.mkdir(parents=True,exist_ok=True)
  report=dst/('control-browser.json'if control else'main-browser.json')
  done=dst/'closed.json'
  if done.exists():
   q=read(done);assert q['exit']==0 and q['report_sha256']==sha(report);continue
  assert not report.exists(),part
  used=179 if control else 180
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/donghu-house-seven-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage180'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage179/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':'216','QA_CONTROL_CATALOG_SHA256':read(w/'179-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19680'}
  f=w/'check-180-separated.cjs';case=w/'case180.json'
  with tempfile.TemporaryDirectory(prefix='map180-'+part+'-')as tmp,(dst/'run.log').open('w')as lg:
   proc=subprocess.Popen(['node',f,case]+(['--control']if control else []),env={**env,'TMPDIR':tmp},stdout=lg,stderr=subprocess.STDOUT);seen=set()
   while proc.poll() is None:
    for q in Path('/proc').glob('[0-9]*/cmdline'):
     try:cmd=q.read_bytes().split(b'\0')
     except OSError:continue
     if cmd and os.path.basename(cmd[0])in [b'chromium',b'chrome',b'headless_shell']and (b'--remote-debugging-port=19680'in cmd or any(i.startswith(os.fsencode('--user-data-dir='+tmp+'/'))for i in cmd)):
      seen.add(int(q.parent.name))
    time.sleep(.9)
   active=[]
   for pid in seen:
    q=Path('/proc')/str(pid)/'stat'
    if q.exists()and q.read_text().rsplit(')',1)[1].split()[0]not in ('Z','X'):active.append(pid)
   q=dict(exit=proc.returncode,node=proc.pid,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report),driver_sha256=sha(f),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'179-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')
