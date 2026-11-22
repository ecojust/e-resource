"""Run the true parent and each measured public input on the signed predecessor and successor city sites."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/231';parts=e/'separate'
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
if len(stages)>1:
 for part in stages:
  subprocess.run([sys.executable,'-Bu',__file__,previous,part],check=True)
  if part in ['before','phone']:subprocess.run([sys.executable,'-Bu',w/'offer-296.py',part],check=True)
  if part in ('before','phone'):
   after_before=part=='before'
   wp=Path('/tmp/kong482' if after_before else '/tmp/yingbin486')
   step='native' if after_before else 'viewer'
   close=e/('before' if after_before else 'separate/phone')/'closed.json'
   bank=Path('/tmp/nanshi-bank296')/(step+'-closed.json')
   before=bank if bank.is_file() else w/('296-'+step+'-deferred.json')
   completed=wp/'231-native-returned.json'
   if not completed.is_file():
    subprocess.run([sys.executable,'-Bu',wp/'native-on-cleared-host.py',close,before])
   checked=read(completed)
   assert checked['host_sha256']==sha(close) and checked['previous_sha256']==sha(before) and checked['all_children_exited'] and checked['remaining_children']==[]
   if after_before:
    subprocess.run([sys.executable,'-Bu','/dev/shm/k295-dev/after-231.py',close,completed],check=True)
  if part in ('details','architecture'):
   wp=Path('/tmp/boc-warehouse490' if part=='details' else '/tmp/fuxin-mill494')
   close=e/'separate'/part/'closed.json';completed=wp/'231-native-returned.json'
   if not completed.is_file():subprocess.run([sys.executable,'-Bu',wp/'native-on-cleared-host.py',close])
   checked=read(completed)
   assert checked['host_sha256']==sha(close) and checked['all_children_exited'] and checked['remaining_children']==[]
  if part=='desktop':subprocess.run([sys.executable,'-Bu',w/'offer-392.py'],check=True)
 sys.exit(0)
if len(stages)==1 and stages[0]=='details':
 rec=read(parts/'desktop'/'main-browser.json')
 assert rec['completed'] and rec['screenshots'] and not rec['failed'] and not rec.get('failure'), 'Desktop returned before its image; resume the missing capture.'
for n in [230,231]:
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
   q=read(done);actual=read(report);assert q['exit']==0 and q['report_sha256']==sha(report) and actual['completed'] and actual['screenshots'];continue
  assert not report.exists(),part
  used=230 if control else 231
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/unrra-gray-building-north-front-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage231'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage230/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':str(read(w/'230-production.json')['resulting_count']),'QA_CONTROL_CATALOG_SHA256':read(w/'230-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19731'}
  old_inputs=e/'previous-attempts'
  if part in ['details','touch']:
   for held in sorted(old_inputs.glob(part+'-*-landed'),reverse=True):
    report_file=held/'main-browser.json';exit_file=held/'closed.json'
    if report_file.is_file() and exit_file.is_file() and read(report_file).get('realBeacon',{}).get('landed')==read(w/'case231.json')['id']:
     env['SAVED_REAL_POINTER']=str(exit_file);break
  f=w/({'architecture':'finish-physical-architecture.cjs','distant':'finish-physical-distant.cjs'}.get(part,'check-231-separated.cjs'));case=w/'case231.json'
  frozen_driver=dst/'executed-driver.cjs';frozen_driver.write_bytes(f.read_bytes())
  helper=w/'cdp-city-page.cjs'
  if part in ['desktop','details','touch','architecture','distant']:(dst/helper.name).write_bytes(helper.read_bytes())
  with tempfile.TemporaryDirectory(prefix=part[:2]+'-',dir='/dev/shm/u231/t')as tmp,(dst/'run.log').open('w')as lg:
   proc=subprocess.Popen(['node',f,case]+(['--control']if control else []),env={**env,'TMPDIR':tmp},stdout=lg,stderr=subprocess.STDOUT);seen=set()
   while proc.poll() is None:
    for q in Path('/proc').glob('[0-9]*/cmdline'):
     try:cmd=q.read_bytes().split(b'\0')
     except OSError:continue
     if cmd and os.path.basename(cmd[0])in [b'chromium',b'chrome',b'headless_shell']and (b'--remote-debugging-port=19731'in cmd or any(i.startswith(os.fsencode('--user-data-dir='+tmp+'/'))for i in cmd)):
      seen.add(int(q.parent.name))
    if part in ('architecture','distant') and (dst/'verification-browser-start.json').is_file() and not (dst/'external-observer.json').exists():
     start=read(dst/'verification-browser-start.json');pid=start['pid'];live=Path('/proc')/str(pid);fields=(live/'stat').read_text().rsplit(')',1)[1].split()
     assert start['node']==proc.pid and int(fields[1])==proc.pid and fields[19]==start['starttime'] and fields[0] not in ('X','Z')
     assert b'--remote-debugging-port=19731' in (live/'cmdline').read_bytes().split(b'\0')
     seen.add(pid);(dst/'external-observer.json').write_text(json.dumps({**start,'observer':os.getpid(),'method':'live /proc stat PPID, birth time, executable and debugging port'},indent=2)+'\n')
    time.sleep(.9)
   active=[]
   for pid in seen:
    q=Path('/proc')/str(pid)/'stat'
    if q.exists()and q.read_text().rsplit(')',1)[1].split()[0]not in ('Z','X'):active.append(pid)
   q=dict(exit=proc.returncode,node=proc.pid,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report)if report.is_file()else None,driver_sha256=sha(f),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active and report.is_file()
   actual=read(report)
   assert actual['completed'] and actual['screenshots'] and not actual['errors'] and not actual['failed'] and not actual.get('failure'), (part,'diagnostic ended before all real images')
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'230-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')
