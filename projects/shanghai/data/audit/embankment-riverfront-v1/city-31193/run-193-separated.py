"""Run the true parent and each measured public input on the signed predecessor and successor city sites."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/193';parts=e/'separate'
if len(sys.argv)<2:raise SystemExit('Supply the signed actual predecessor browser exit receipt')
previous=Path(sys.argv[1]);del sys.argv[1]
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
handoff=read(previous)
exit_code=next((handoff[k]for k in ('code','exit','exit_code','returncode')if k in handoff),None)
assert (exit_code==0 or (exit_code is None and handoff.get('passed') is True)) and not any(handoff.get(k)for k in ('remaining','remaining_chromium','remaining_processes')),(previous,handoff)
assert handoff.get('passed',True) is not False
assert handoff['order']==192
names=[item['name'] for item in handoff['sessions']]
assert names == ['before','phone','phone-zoom','desktop','architecture','distant'],names
assert all(item['exit_code']==0 and not item['remaining_chromium'] for item in handoff['sessions'])
published=Path(handoff['reports']);assert published.is_file()
assert read(published)['code']==0
for n in [192,193]:
 b=read(w/f'{n}-bindings.json');assert b['production']==sha(w/f'{n}-production.json')
 assert all(sha(w/f'stage{n}'/path)==hashv for path,hashv in b['files'].items())
with (w/'browser.lock').open('a')as lock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
 fcntl.flock(lock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
 stages=['before','phone','desktop','beacon','beacon-return','architecture','distant','downloads']
 requested=sys.argv[1:] or stages
 assert len(requested)==len(set(requested)) and all(part in stages for part in requested)
 for part in requested:
  control=part=='before'
  dst=e/'before'if control else parts/part;dst.mkdir(parents=True,exist_ok=True)
  report=dst/('control-browser.json'if control else'main-browser.json')
  done=dst/'closed.json'
  f=w/('check-193-separated.cjs' if control else 'check-193-default-camera.cjs' if part in ('desktop','phone') else 'check-193-marker.cjs' if part in ('beacon','beacon-return') else 'check-193-near-views.cjs')
  if done.exists():
   q=read(done);assert q['exit']==0 and q['node_closed'] and not q['remaining'] and q['report_sha256']==sha(report) and q['driver_sha256']==sha(f);continue
  assert not report.exists(),part
  used=192 if control else 193
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/embankment-riverfront-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage193'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage192/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':'229','QA_CONTROL_CATALOG_SHA256':read(w/'192-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19693'}
  case=w/'case193.json'
  profile_base=max(['/tmp','/dev/shm'],key=lambda loc:__import__('shutil').disk_usage(loc).free)
  started=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with tempfile.TemporaryDirectory(prefix='map193-'+part+'-',dir=profile_base)as tmp,(dst/'run.log').open('w')as lg:
   proc=subprocess.Popen(['node',f,case]+(['--control']if control else []),env={**env,'TMPDIR':tmp},stdout=lg,stderr=subprocess.STDOUT);seen=set()
   while proc.poll() is None:
    for q in Path('/proc').glob('[0-9]*/cmdline'):
     try:cmd=q.read_bytes().split(b'\0')
     except OSError:continue
     if cmd and os.path.basename(cmd[0])in [b'chromium',b'chrome',b'headless_shell']and (b'--remote-debugging-port=19693'in cmd or any(i.startswith(os.fsencode('--user-data-dir='+tmp+'/'))for i in cmd)):
      seen.add(int(q.parent.name))
    time.sleep(.9)
   active=[]
   for pid in seen:
    q=Path('/proc')/str(pid)/'stat'
    if q.exists()and q.read_text().rsplit(')',1)[1].split()[0]not in ('Z','X'):active.append(pid)
   q=dict(exit=proc.returncode,node=proc.pid,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report) if report.is_file() else None,driver_sha256=sha(f),started=started,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active and report.is_file()
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'192-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')
