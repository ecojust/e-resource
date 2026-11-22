"""Run each public input only after the complete physical exit of city 229."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,os,psutil,subprocess,sys,tempfile,time,shutil
w=Path('/tmp/shanghai-main-230');p=Path('/workspace/e-resource/projects/shanghai')
prior=Path('/tmp/shanghai-main-229/229-map-slot-released.json')
j=lambda path:json.loads(path.read_bytes())
def sha(path):
 with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,data):
 temp=path.with_suffix('.new');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
def wait_for_prior():
 while not prior.is_file():time.sleep(5)
 x=j(prior)
 assert x['order']==229 and x['passed'] and x['exit_code']==0 and not x['remaining_chromium']
 assert x['all_captures_visually_reviewed'] and x['finished']
 assert x.get('receipts') or x.get('real_browser_process_exits') or x.get('sessions') or x.get('reports')
 return sha(prior)
def inactive(pid):
 try:return psutil.Process(pid).status()in [psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD]
 except psutil.NoSuchProcess:return True
def phase(name,args,report,gate):
 dst=w/'sessions'/name;dst.mkdir(exist_ok=True,parents=True);closed=dst/'closed.json';result=dst/report
 if closed.is_file():
  c=j(closed)
  prior_report=j(result) if result.is_file() else {}
  assert c['node_closed'] and not c['remaining'] and c['prior_sha256']==gate
  if c['exit']==0 and c['chromium_pids'] and prior_report.get('passed') and c['report_sha256']==sha(result):
   return
  history=w/'attempts'/name;history.mkdir(parents=True,exist_ok=True)
  archived=history/str(time.time_ns());dst.rename(archived);dst.mkdir()
  print('Preserved the incomplete session',archived,flush=True)
  if name.startswith('walk') and c['driver_sha256']==sha(w/'walk.cjs'):
   for part in ('walk','side','far','departure-return'):
    saved=archived/('component-'+part);receipt=saved/'process.json';report_path=saved/'real-city.json'
    if not receipt.exists() or not report_path.exists():break
    physical=j(receipt);capture=j(report_path)
    if physical.get('exit')!=0:break
    assert physical['driver_sha256']==c['driver_sha256'] and physical['report_sha256']==sha(report_path) and capture['passed'] and capture['closed']
    for record in capture['cases']:assert sha(saved/record['file'])==record['sha256']
    if part=='walk':assert j(saved/'real-city-mesh.json')['passed']
    revived=dst/saved.name
    shutil.copytree(saved,revived,copy_function=os.link)

 assert not result.exists(),dst
 check=args[args.index('-r')+2]if '-r'in args else args[1]
 with (w/'render.lock').open('a')as citylock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light,(dst/'run.log').open('w')as log,tempfile.TemporaryDirectory(prefix='bridge230-'+name+'-')as temp:
  fcntl.flock(citylock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
  env={**os.environ,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','MODEL_BASE_URL':'http://127.0.0.1:31230/','TMPDIR':temp}
  shutil.copy2(check,dst/'executed-driver.cjs')
  started=datetime.datetime.now(datetime.timezone.utc).isoformat()
  proc=subprocess.Popen(args,env=env,cwd=p,stdout=log,stderr=subprocess.STDOUT)
  children=set();born={}
  while proc.poll()is None:
   try:tree=psutil.Process(proc.pid).children(recursive=True)
   except psutil.NoSuchProcess:tree=[]
   for q in tree:
    try:
     if q.name()in ('chromium','chrome','headless_shell','chrome-headless-shell'):children.add(q.pid);born[q.pid]=q.create_time()
    except psutil.NoSuchProcess:continue
   time.sleep(.2)
  for _ in range(45):
   active=[q for q in children if not inactive(q)]
   if not active:break
   time.sleep(.1)
  c=dict(phase=name,exit=proc.returncode,node=proc.pid,node_closed=inactive(proc.pid),chromium_pids=sorted(children),observed_chromium_births=born,remaining=active,started=started,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_sha256=gate,driver=str(check),driver_sha256=sha(Path(check)),report_sha256=sha(result)if result.is_file()else None)
  write(closed,c);assert c['exit']==0 and c['node_closed']and children and not active,c
  rec=j(result);assert rec['passed']and not rec.get('errors')and not rec.get('pageErrors')and not rec.get('failedRequests')
  if name.startswith('walk'):assert j(dst/'real-city-mesh.json')['passed']
  if name=='standalone':
   assert len(rec['views'])==len(rec['orientationViews'])==len(rec['downloads'])==4
   for asset in rec['downloads'].values():
    file=dst/asset['saved'];assert asset['saveAsVerified'] and file.stat().st_size==asset['bytes'] and sha(file)==asset['sha256']
if __name__=='__main__':
 with (w/'watch.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
  os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MALLOC_ARENA_MAX='2',PYTHONDONTWRITEBYTECODE='1')
  gate=wait_for_prior()
  proof=j(w/'presentation-inputs.json');assert proof['passed']and proof['rows']['230']['count']==267
  for name in ['before','phone','desktop','mouse','touch','walk-phone','walk-desktop','standalone']:
   dst=w/'sessions'/name
   if name=='standalone':args=['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',w/'official-standalone.cjs','huangpu-zhapu-road-bridge',dst];report='viewer.json'
   elif name.startswith('walk'):args=['node',w/'walk.cjs','230',dst,'390' if name=='walk-phone'else'660'];report='real-city.json'
   else:args=['node',w/'overview.cjs',name,dst];report='report.json'
   phase(name,args,report,gate)
   if name=='desktop':
    guest=Path('/tmp/huashan831-371/mapping/after-230-desktop.py')
    assert sha(guest)=='8d59d5d96abdcd4349ddd134d23edfb896c303918006ce1b78bcfd5db2193a23'
    host=dst/'closed.json'
    result=guest.parent/'230-desktop-city-closed.json'
    if not result.exists():
     subprocess.run([sys.executable,'-Bu',guest,host],check=True)
    row=j(result)
    if row.get('previous_sha256'):
     geometry=Path(row['geometry'])
     assert sha(geometry)==row['previous_sha256']
    assert row['host_receipt_sha256']==sha(host) and row['host_report_sha256']==j(host)['report_sha256']
    assert row['order']==371 and row['host']==230 and row['all_children_exited'] and row['remaining']==row['remaining_children']==[]
    assert sha(host) in list(row.values()) and j(host)['report_sha256'] in list(row.values())
    entry=Path('/tmp/yangtze-hankou292/browser-temp-new/reuse-closed-292-at-230.py')
    assert sha(entry)=='63a0ea5a87111dcad0ce6a805e5a4243b20a0c894be25354c8f15bb8e70e511c'
    subprocess.run([sys.executable,'-Bu',entry,host,result],check=True)
    proof=j(Path('/dev/shm/y292/230-development-viewer-returned.json'))
    assert proof['order']==292 and proof['host']==230 and proof['phase']=='desktop'
    assert proof['host_sha256']==sha(host) and proof['host_report_sha256']==j(host)['report_sha256'] and proof['previous_sha256']==sha(result)
    assert proof['all_children_exited'] and proof['remaining_children']==[]
    assert proof['already_completed'] and proof['started'] is False and proof['previous_completed_exit']==0
   if name=='mouse':
    guest=Path('/tmp/ankang382/design/after-230-model.py');host=dst/'closed.json'
    assert sha(guest)=='fa4856d7a91ec9ac648596b0b22ced3e1c15b70bf9ef6ebe2a964a5ca5dfb79e'
    subprocess.run([sys.executable,'-Bu',guest,host],check=True)
    record=guest.parent.parent/'230-model-closed.json';row=j(record)
    assert row['order']==382 and row['host']==230 and row['phase']=='mouse'
    assert row['host_sha256']==sha(host) and row['host_report_sha256']==j(host)['report_sha256']
    assert row['all_children_exited'] and row['remaining']==[]
    if row.get('started'):assert isinstance(row['exit_code'],int) and row['phases']
    else:assert row.get('deferred') and not row.get('attempted')
   if name=='touch':
    guest=Path('/tmp/yongjia630-381/development-native/start.py');host=dst/'closed.json';author_sha='fa2f5f4f83172faa6af54f04f4a464312c2fae00e3ced1a654d6a00c93ba7976'
    assert sha(guest)=='b2378b2542f97e50d9edb9a939c21211c6bf425646bf9ef110e9d75e255fe694'
    result=guest.parent/'physical.json';admission=guest.parent/'admit.json'
    if result.is_file() and admission.is_file() and j(result).get('passed') and j(admission).get('previous_sha256')==sha(host) and j(admission).get('author_sha256')==author_sha:
     code=j(result)['exit_code']
    else:
     code=subprocess.run([sys.executable,'-Bu',guest,host,author_sha]).returncode
    row=j(result);admit=j(admission)
    assert row['order']==381 and row['all_children_exited'] and row['remaining_children']==[]
    assert not isinstance(row['exit_code'],bool) and row['exit_code']==code and row['passed']==(not code)
    assert admit['previous_sha256']==sha(host) and admit['author_sha256']==author_sha and row['events']
    for event in row['events']: assert event['pid']>0 and event['log_sha256']==sha(guest.parent/(event['name']+'.log'))
   if name=='walk-phone':
    guest=Path('/dev/shm/anting385-retry230/after-walk.py');assert sha(guest)=='2ee18b7fd5d40280af9ded5fdf602d6767eda867f78b5bfd0b6cfe6dd54a1f5a'
    host=dst/'closed.json';subprocess.run([sys.executable,'-Bu',guest,host],check=True)
    out=Path('/tmp/anting43-385/230-walk-wall-closed.json');row=j(out)
    assert row['order']==385 and row['host']==230 and row['source_sha256']==sha(host) and row['host_report_sha256']==j(host)['report_sha256'] and row['remaining']==[] and row['all_children_exited']
   if name=='walk-desktop':
    guest=Path('/tmp/tianping40-393/development-native/start.py');host=dst/'closed.json';author_sha='beec35bb7143fddeada13bac40379bec4cbee24b37445570de8fd4c0c7e73860'
    assert sha(guest)=='485e332952fd0add895a4fae7f23176bf443a385e54f121c026198ab21141403'
    result=guest.parent/'physical.json';admission=guest.parent/'admit.json'
    if result.is_file() and admission.is_file() and j(result).get('passed') and j(admission).get('previous_sha256')==sha(host) and j(admission).get('author_sha256')==author_sha:
     code=j(result)['exit_code']
    else:
     code=subprocess.run([sys.executable,'-Bu',guest,host,author_sha]).returncode
    row=j(result);admit=j(admission)
    assert row['order']==393 and row['all_children_exited'] and row['remaining_children']==[]
    assert not isinstance(row['exit_code'],bool) and row['exit_code']==code and row['passed']==(not code)
    assert admit['previous_sha256']==sha(host) and admit['author_sha256']==author_sha and row['events']
    for event in row['events']: assert event['pid']>0 and event['log_sha256']==sha(guest.parent/(event['name']+'.log'))
   if name in ['before','phone']:subprocess.run([sys.executable,'-B',w/'offer-295.py',name],check=True)
  host=w/'sessions/standalone/closed.json'
  guest=Path('/tmp/kiangsu-inn295/handoff/after-230-standalone.py')
  assert sha(guest)=='fbc3c983328ba944f375df263f8933ec776894052b7490bf0a6f1a7ca6ea3ad3'
  subprocess.run([sys.executable,'-Bu',guest,host],check=True)
  handback=j(Path('/tmp/kiangsu-inn295/230-standalone-returned.json'))
  assert handback['all_children_exited'] and not handback['remaining_children'] and sha(host) in handback.values() and j(host)['report_sha256'] in handback.values()
  wide=w/'sessions/before-wide'
  phase('before-wide',['node',w/'before-overview-wide.cjs','before',wide],'report.json',gate)
  print('All browser segments closed; inspect the saved photographs before releasing city 231.',flush=True)
