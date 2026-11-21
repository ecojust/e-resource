"""Run the true parent and each measured public input on the signed predecessor and successor city sites."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/199';parts=e/'separate'
if len(sys.argv)<2:raise SystemExit('Supply the signed actual predecessor browser exit receipt')
previous=Path(sys.argv[1]);del sys.argv[1]
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
handoff=read(previous)
exit_code=next((handoff[k]for k in ('code','exit','exit_code','returncode')if k in handoff),None)
assert (exit_code==0 or (exit_code is None and handoff.get('passed') is True)) and not any(handoff.get(k)for k in ('remaining','remaining_chromium','remaining_processes')),(previous,handoff)
assert handoff.get('passed',True) is not False
stages=sys.argv[1:] or ['before','phone','desktop','details','architecture','distant']
if 'details' in stages and 'architecture' in stages and 'touch' not in stages:
 stages.insert(stages.index('details')+1,'touch')
if stages[0]=='before' and len(stages)>1:
 subprocess.run([sys.executable,'-Bu',__file__,previous,'before'],check=True)
 control=e/'before/closed.json';report=e/'before/control-browser.json'
 checked=read(control)
 assert checked['exit']==0 and checked['node_closed'] and not checked['remaining'] and checked['report_sha256']==sha(report)
 marker=w/'264-native-window.json'
 proposal={'order':199,'preceding_segment':'before','exit':0,'remaining':[],'actual_control':str(control),'sha256':sha(control),'report_sha256':sha(report)}
 if marker.exists():assert read(marker)==proposal
 else:
  tmp=marker.with_suffix('.new');tmp.write_text(json.dumps(proposal,indent=2)+'\n');tmp.replace(marker)
 print('Physical 199 predecessor browser exited. The independent native session may take the free slot.',flush=True)
 native=Path('/tmp/waterworks264/native-closed.json');defer=w/'264-native-slot-deferred.json'
 while not (native.is_file() or defer.is_file()):time.sleep(3)
 if native.is_file():
  actual=read(native)
  assert actual.get('order',264)==264 and any(actual.get(k)==0 for k in ('exit','exit_code','returncode','code')) and not any(actual.get(k)for k in ('remaining','remaining_chromium','remaining_processes'))
 else:
  decision=read(defer);assert decision['control_sha256']==sha(control) and decision['author_confirmed_deferred'] and decision['reason']
 subprocess.run([sys.executable,'-Bu',__file__,previous,*stages[1:]],check=True)
 sys.exit(0)
if stages[0]=='phone' and len(stages)>1:
 subprocess.run([sys.executable,'-Bu',__file__,previous,'phone'],check=True)
 closed=parts/'phone/closed.json';browser=parts/'phone/main-browser.json'
 physical=read(closed)
 assert physical['exit']==0 and physical['node_closed'] and not physical['remaining'] and physical['chromium_pids'] and sha(browser)==physical['report_sha256']
 marker=w/'264-viewer-window.json'
 proposal={'order':199,'preceding_segment':'phone','exit':0,'remaining':[],'actual_phone_exit':str(closed),'sha256':sha(closed),'report_sha256':sha(browser)}
 if marker.exists():assert read(marker)==proposal
 else:
  tmp=marker.with_suffix('.new');tmp.write_text(json.dumps(proposal,indent=2)+'\n');tmp.replace(marker)
 print('The normal 199 touch-screen browser has physically closed; 264 may use the independent viewer window.',flush=True)
 independence=Path('/tmp/waterworks264/standalone-closed.json');defer=w/'264-viewer-slot-deferred.json'
 while not (independence.is_file() or defer.is_file()):time.sleep(3)
 if independence.is_file():
  item=read(independence);assert item.get('order',264)==264 and item['exit_code']==0 and item['remaining_chromium']==[]
  assert len(item['screens'])==6 and len(item['downloads'])==4
 else:
  decision=read(defer);assert decision['phone_exit_sha256']==sha(closed) and decision['author_confirmed_deferred'] and decision['reason']
 subprocess.run([sys.executable,'-Bu',__file__,previous,*stages[1:]],check=True)
 sys.exit(0)
for n in [198,199]:
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
  used=198 if control else 199
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/wukang-east-annex-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage199'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage198/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':'235','QA_CONTROL_CATALOG_SHA256':read(w/'198-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19699'}
  f=w/'check-199-separated.cjs';case=w/'case199.json'
  with tempfile.TemporaryDirectory(prefix='map199-'+part+'-')as tmp,(dst/'run.log').open('w')as lg:
   proc=subprocess.Popen(['node',f,case]+(['--control']if control else []),env={**env,'TMPDIR':tmp},stdout=lg,stderr=subprocess.STDOUT);seen=set()
   while proc.poll() is None:
    for q in Path('/proc').glob('[0-9]*/cmdline'):
     try:cmd=q.read_bytes().split(b'\0')
     except OSError:continue
     if cmd and os.path.basename(cmd[0])in [b'chromium',b'chrome',b'headless_shell']and (b'--remote-debugging-port=19699'in cmd or any(i.startswith(os.fsencode('--user-data-dir='+tmp+'/'))for i in cmd)):
      seen.add(int(q.parent.name))
    time.sleep(.9)
   active=[]
   for pid in seen:
    q=Path('/proc')/str(pid)/'stat'
    if q.exists()and q.read_text().rsplit(')',1)[1].split()[0]not in ('Z','X'):active.append(pid)
   q=dict(exit=proc.returncode,node=proc.pid,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report)if report.is_file()else None,driver_sha256=sha(f),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active and report.is_file()
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'198-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')
