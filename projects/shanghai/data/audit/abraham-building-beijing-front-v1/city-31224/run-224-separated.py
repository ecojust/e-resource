"""Run the true parent and each measured public input on the signed predecessor and successor city sites."""
import sys,fcntl,json,subprocess,os,time,hashlib,datetime,tempfile
from pathlib import Path
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
e=w/'evidence/224';parts=e/'separate'
if len(sys.argv)<2:raise SystemExit('Supply the signed actual predecessor browser exit receipt')
previous=Path(sys.argv[1]);assert previous.resolve()==Path('/tmp/shanghai-main-223/223-map-slot-released.json');del sys.argv[1]
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
handoff=read(previous)
assert handoff['order']==223 and handoff['exit_code']==0 and handoff['remaining_chromium']==[]
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
   subprocess.run([sys.executable,'-Bu',w/'offer-289.py','native' if part=='before' else 'viewer'],check=True)
  if part=='before':
   guest=Path('/tmp/fenyang359/mapping/224-revised-model.py')
   assert sha(guest)=='d032fb9035ac59fe37d00a915f43b10248ae65b609ba5ce9faac93d0cf11faea'
   host=e/'before/closed.json'
   predecessor=Path('/tmp/chinatheatre289/native-closed.json')
   if not predecessor.is_file():predecessor=Path('/tmp/chinatheatre289/224-native-deferred.json')
   subprocess.run([sys.executable,'-Bu',guest,host,predecessor],check=False)
   returned=read(Path('/tmp/fenyang359/mapping/224-revised-model-closed.json'))
   assert returned['host_sha256']==sha(host) and returned['previous_sha256']==sha(predecessor)
   assert returned['remaining']==[] and type(returned['exit_code']) is int
  if part=='desktop':
   guest=Path('/tmp/fenyang359/mapping/224-after-desktop.py')
   assert sha(guest)=='bac8a1cfc2645dde9578edd88d81e923dea5e2939ab40fe93d491de8caa8252b'
   host=parts/'desktop/closed.json'
   subprocess.run([sys.executable,'-B',guest,host],check=False)
   outcome=read(Path('/tmp/fenyang359/mapping/224-city-closed.json'))
   assert outcome['host']==224 and outcome['order']==359 and outcome['host_sha256']==sha(host) and not outcome['remaining']
   previous_guest=Path('/tmp/fenyang359/mapping/224-city-closed.json')
   next_guest=Path('/tmp/fenyang-jewish-hospital358/after-224.py')
   assert sha(next_guest)=='4e4daabea698007001b44805962ea332e0ffc0bc438efa140cc46d464168bab3'
   subprocess.run([sys.executable,'-B',next_guest,host,previous_guest],check=False)
   returned=read(Path('/tmp/fenyang-jewish-hospital358/224-pilot-closed.json'))
   assert returned['order']==358 and returned['host']==224 and returned['host_sha256']==sha(host)
   assert returned['previous_sha256']==sha(previous_guest) and returned['host_report_sha256']==outcome['host_report_sha256']
   assert returned['remaining']==[] and isinstance(returned['exit_code'],int)
   residence=Path('/tmp/blackstone361/after-224-desktop.py')
   assert sha(residence)=='5959cbf8ef75837beabf6b189b059f54ee5b3ed41ab3107339ec59da2528d3d5'
   last=Path('/tmp/fenyang-jewish-hospital358/224-pilot-closed.json')
   subprocess.run([sys.executable,'-Bu',residence,host,last],check=False)
   done=read(Path('/tmp/blackstone361/224-pilot-closed.json'))
   assert done['order']==361 and done['host']==224 and done['host_sha256']==sha(host)
   assert done['previous_sha256']==sha(last) and done['host_report_sha256']==returned['host_report_sha256'] and done['remaining']==[]
   assert type(done['exit_code']) is int and done['passed']==(done['exit_code']==0) and done['finished']
  if part=='details':
   program=Path('/dev/shm/fuxing341-exposed-lod/after-224-details.py')
   assert sha(program)=='607b982c9b61f0d4a3ee19922200bdf6df569f78bd95ba219effd8107f8864ad'
   host=parts/'details/closed.json'
   receipt=program.parent/'224-runtime-closed.json'
   if not receipt.exists():subprocess.run([sys.executable,'-Bu',program,host],check=False)
   returned=read(receipt)
   assert returned['host_sha256']==sha(host) and returned['host_report_sha256']==read(host)['report_sha256']
   assert returned['all_children_exited'] and returned['remaining']==[] and type(returned['exit_code']) is int
  if part=='touch':
   program=Path('/tmp/petain379/revised-author/after-224.py')
   assert sha(program)=='842ca445866ef82e16fc99825371f18cd59eb47224f2ac02810016acafabbeda'
   host=parts/'touch/closed.json';prior=Path('/tmp/petain379/223-revised-study-closed.json')
   receipt=Path('/tmp/petain379/224-touch-model-closed.json')
   if not receipt.exists():subprocess.run([sys.executable,'-Bu',program,host,prior],check=False)
   returned=read(receipt)
   assert returned['host_sha256']==sha(host) and returned['host_report_sha256']==read(host)['report_sha256'] and returned['previous_sha256']==sha(prior)
   assert returned['remaining']==[] and type(returned['exit_code']) is int
 sys.exit(0)
if stages in (['architecture'],['closeups']) and not os.environ.get('QA224_FOCUS'):
 if stages==['closeups']:
  cert=read(w/'396-window-returned.json');assert cert['all_children_exited'] and not cert['remaining_children']
 subprocess.run([sys.executable,'-Bu',w/'individual-camera.py',previous,stages[0]],check=True);sys.exit(0)
if stages==['closeups'] and not (w/'396-unavailable.json').exists():
 certificate=w/'396-window-returned.json'
 while not certificate.exists():time.sleep(.4)
 receipt=read(certificate);assert receipt['all_children_exited'] and receipt['remaining_children']==[] and receipt['host_sha256']==sha(Path(receipt['host']))
if stages==['touch']:
 subprocess.run([sys.executable,'-Bu',w/'after-details-supplement.py'],check=True)
for n in [223,224]:
 b=read(w/f'{n}-bindings.json');assert b['production']==sha(w/f'{n}-production.json')
 assert all(sha(w/f'stage{n}'/path)==hashv for path,hashv in b['files'].items())
with (w/'browser.lock').open('a')as lock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
 fcntl.flock(lock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
 for part in stages:
  control=part=='before'
  dst=e/'before'if control else parts/part
  if focus:=os.environ.get('QA224_FOCUS'):dst=dst/'components'/focus
  dst.mkdir(parents=True,exist_ok=True)
  report=dst/('control-browser.json'if control else'main-browser.json')
  done=dst/'closed.json'
  if done.exists():
   q=read(done);assert q['exit']==0 and q['report_sha256']==sha(report) and read(report)['completed'] and not read(report).get('failure');continue
  assert not report.exists(),part
  used=223 if control else 224
  env={**os.environ,'MODEL_AUDIT_DIR':str(p/'data/audit/abraham-building-beijing-front-v1'),'SHANGHAI_PROJECT_ROOT':str(w/'stage224'),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+used}/','QA_OUTPUT_DIR':str(dst),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','QA_CONTROL_CATALOG':str(w/'stage223/data/candidate-city-integrations.json'),'QA_CONTROL_CITY_COUNT':str(read(w/'223-production.json')['resulting_count']),'QA_CONTROL_CATALOG_SHA256':read(w/'223-production.json')['files']['data/candidate-city-integrations.json'],'CITY_SECTION':part,'QA_CDP_PORT':'19724'}
  f=w/'check-224-separated.cjs';case=w/'case224.json'
  with tempfile.TemporaryDirectory(prefix='map224-'+part+'-',dir=max(('/tmp','/dev/shm'),key=lambda path:__import__('shutil').disk_usage(path).free))as tmp,(dst/'run.log').open('w')as lg:
   proc=subprocess.Popen(['node',f,case]+(['--control']if control else []),env={**env,'TMPDIR':tmp},stdout=lg,stderr=subprocess.STDOUT);seen=set()
   while proc.poll() is None:
    for q in Path('/proc').glob('[0-9]*/cmdline'):
     try:cmd=q.read_bytes().split(b'\0')
     except OSError:continue
     if cmd and os.path.basename(cmd[0])in [b'chromium',b'chrome',b'headless_shell']and (b'--remote-debugging-port=19724'in cmd or any(i.startswith(os.fsencode('--user-data-dir='+tmp+'/'))for i in cmd)):
      seen.add(int(q.parent.name))
    time.sleep(.9)
   active=[]
   for pid in seen:
    q=Path('/proc')/str(pid)/'stat'
    if q.exists()and q.read_text().rsplit(')',1)[1].split()[0]not in ('Z','X'):active.append(pid)
   q=dict(exit=proc.returncode,node=proc.pid,chromium_pids=sorted(seen),node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,report_sha256=sha(report)if report.is_file()else None,driver_sha256=sha(f),finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
   done.write_text(json.dumps(q,indent=2)+'\n')
   assert q['driver_sha256']==sha(f);(dst/'driver.cjs').write_bytes(f.read_bytes())
   print(part,q,flush=True)
   assert q['exit']==0 and q['node_closed'] and seen and not active and report.is_file() and read(report)['completed'] and not read(report).get('failure')
   if control:(dst/'exit.json').write_text(json.dumps(dict(code=0,production=sha(w/'223-production.json'),phase='before',base=env['MODEL_BASE_URL'],driver_sha256=sha(f),case_sha256=sha(case),finished=q['finished']),indent=2)+'\n')
