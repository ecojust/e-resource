"""Run each public input only after the complete physical exit of city 222."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,os,psutil,subprocess,sys,tempfile,time
w=Path(__file__).resolve().parent;p=Path('/workspace/e-resource/projects/shanghai')
prior=Path('/tmp/signal222/city-31222/222-map-slot-released.json')
j=lambda path:json.loads(path.read_bytes())
def sha(path):
 with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,data):
 temp=path.with_suffix('.new');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
def wait_for_prior():
 while not prior.is_file():time.sleep(5)
 x=j(prior)
 assert x['order']==222 and x['passed']and x['final_closed_at']and x['remaining_chromium']==[]and x['after_real_screenshot_review']and x['receipts']
 def verify(z):
  if isinstance(z,dict):
   for key,val in z.items():
    for k in ['sha256',key+'_sha256']:
     if key in ('path','report','exit','receipt','closed')and isinstance(val,str)and val.startswith('/')and isinstance(z.get(k),str):assert sha(Path(val))==z[k]
    verify(val)
  elif isinstance(z,list):
   for v in z:verify(v)
 verify(x['receipts'])
 return sha(prior)
def inactive(pid):
 try:return psutil.Process(pid).status()in [psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD]
 except psutil.NoSuchProcess:return True
def phase(name,args,report,gate):
 dst=w/'sessions'/name;dst.mkdir(exist_ok=True,parents=True);closed=dst/'closed.json';result=dst/report
 if closed.is_file():
  c=j(closed);assert c['exit']==0 and c['node_closed']and not c['remaining']and c['report_sha256']==sha(result)and c['prior_sha256']==gate;return
 assert not result.exists(),dst
 check=args[args.index('-r')+2]if '-r'in args else args[1]
 with (w/'render.lock').open('a')as citylock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light,(dst/'run.log').open('w')as log,tempfile.TemporaryDirectory(prefix='bridge223-'+name+'-')as temp:
  fcntl.flock(citylock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
  env={**os.environ,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','MODEL_BASE_URL':'http://127.0.0.1:31223/','TMPDIR':temp}
  started=datetime.datetime.now(datetime.timezone.utc).isoformat()
  proc=subprocess.Popen(args,env=env,cwd=p,stdout=log,stderr=subprocess.STDOUT)
  children=set()
  while proc.poll()is None:
   try:tree=psutil.Process(proc.pid).children(recursive=True)
   except psutil.NoSuchProcess:tree=[]
   for q in tree:
    try:
     if q.name()in ('chromium','chrome','headless_shell','chrome-headless-shell'):children.add(q.pid)
    except psutil.NoSuchProcess:continue
   time.sleep(.2)
  for _ in range(45):
   active=[q for q in children if not inactive(q)]
   if not active:break
   time.sleep(.1)
  c=dict(phase=name,exit=proc.returncode,node=proc.pid,node_closed=inactive(proc.pid),chromium_pids=sorted(children),remaining=active,started=started,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_sha256=gate,driver=str(check),driver_sha256=sha(Path(check)),report_sha256=sha(result)if result.is_file()else None)
  write(closed,c);assert c['exit']==0 and c['node_closed']and children and not active,c
  rec=j(result);assert rec['passed']and not rec.get('errors')and not rec.get('pageErrors')and not rec.get('failedRequests')
  if name.startswith('walk'):assert j(dst/'real-city-mesh.json')['passed']
  if name=='standalone':assert len(rec['views'])==len(rec['downloads'])==4
if __name__=='__main__':
 with (w/'watch.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);gate=wait_for_prior()
  proof=j(w/'presentation-inputs.json');assert proof['passed']and proof['rows']['223']['count']==260
  for name in ['before','phone','desktop','mouse','touch','walk-phone','walk-desktop','standalone']:
   dst=w/'sessions'/name
   if name=='standalone':args=['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',w/'formal-bridge-viewer.cjs','huangpu-sichuan-road-bridge',dst];report='viewer.json'
   elif name.startswith('walk'):args=['node',w/'walk.cjs','223',dst,'390' if name=='walk-phone'else'850'];report='real-city.json'
   else:args=['node',w/'overview.cjs',name,dst];report='report.json'
   phase(name,args,report,gate)
   if name=='before':
    source=dst/'closed.json'; program=Path('/tmp/swire287/offer-real-31287.py')
    assert sha(program)=='fda3e06599d694bd474d1ee68003e6b61cce4ce23f5c83771fbd6fa8ebdb0ee9'
    subprocess.run([sys.executable,'-Bu',program,'223',source],check=True)
    returned=program.parent/'223-formal-viewer-returned.json'; result=j(returned)
    assert result['host_sha256']==sha(source) and result['host_report_sha256']==j(source)['report_sha256']
    assert result['remaining_chromium']==[] and result['finished']
    if result.get('passed'):
     assert sha(Path(result['receipt']))==result['receipt_sha256']
    elif result.get('started'):
     assert result['exit_code']!=0 and sha(Path(result['closure']))==result['closure_sha256']
    else: assert result.get('deferred')
    write(w/'287-checked-handback.json',dict(host_sha256=sha(source),returned=str(returned),returned_sha256=sha(returned),passed=bool(result.get('passed'))))
   if name in ['before','phone']:subprocess.run([sys.executable,'-B',w/'offer-288.py',name],check=True)
   if name=='before':
    program=w/'offer-380-after-288.py'
    assert sha(program)=='a3e5e5fff45f38ec854e236cbbaba81f6c9b475bccfe81a5e3b3bdb4fc95833c'
    subprocess.run([sys.executable,'-Bu',program],check=True)
   if name=='touch':
    source=dst/'closed.json'; entry=Path('/dev/shm/fuxing341-exposed-lod/after-223-touch.py')
    assert sha(entry)=='428c96d4b19f5ba372fc1bc895d68e9e6e41899710e0e05af1b95eec5ea62a2b'
    subprocess.run([sys.executable,'-Bu',entry,source],check=True)
    result=entry.with_name('223-lod-returned.json');v=j(result)
    assert (v['order'],v['host'],v['phase'])==(341,223,'touch') and v['remaining']==[] and v['all_children_exited']
    assert v['host_sha256']==sha(source) and v['host_report_sha256']==sha(dst/'report.json')
    assert v['stages'] and all(s['pid']>0 and type(s['exit_code']) is int and sha(Path(s['log']))==s['log_sha256'] for s in v['stages'])
    if v['passed']:assert v['exit_code']==0 and len(v['stages'])==2 and all(s['exit_code']==0 for s in v['stages'])
    else:assert v['exit_code']!=0
    write(w/'341-checked-handback.json',dict(source_sha256=sha(source),result=str(result),result_sha256=sha(result),passed=v['passed']))
   if name=='walk-phone':
    source=dst/'closed.json'
    entry=Path('/tmp/huaihai-1634-research/east-door-supplement/after-223-walk.py')
    assert sha(entry)=='d010ebf1f236eec7173f82dc6de6af573fd8e1c2d363f8aa08587ce2ed9f6ccb'
    subprocess.run([sys.executable,'-Bu',entry,source],check=True)
    ticket=entry.with_name('after-223-walk.json'); actual=j(ticket)
    assert (actual['order'],actual['host'])==(217,223) and actual['attempted'] and actual['started_session']
    assert actual['host_receipt_sha256']==sha(source) and actual['host_report_sha256']==sha(dst/'real-city.json')
    assert actual['exit']==actual['exit_code'] and actual['remaining']==actual['remaining_children']==[]
    assert actual['node_closed'] and actual['node_pid']>0 and actual['all_children_exited'] and actual['started']<=actual['finished']
    assert all(str(pid) in actual['observed_births'] for pid in actual['chromium_pids'])
    assert sha(Path(actual['log']))==actual['log_sha256']
    if actual['report_sha256']:assert sha(Path(actual['report']))==actual['report_sha256']
    if actual['passed']:assert actual['exit']==0 and actual['chromium_pids'] and actual['report_sha256']
    write(w/'217-checked-handback.json',dict(returned=str(ticket),returned_sha256=sha(ticket),passed=actual['passed'],exit_code=actual['exit_code']))
   if name=='walk-desktop':
    source=dst/'closed.json';program=Path('/tmp/sinan-even342/design/after-223-walk.py')
    assert sha(program)=='7475ffad44276c4ae125a9307a22f3d411804403a2b040cfe459b50da690660d'
    subprocess.run([sys.executable,'-B',program,source],check=True)
    actual=j(Path('/tmp/sinan-even342/223-map-cpu-closed.json'))
    assert actual['order']==342 and actual['host']==223 and actual['phase']==name
    assert actual['host_sha256']==sha(source) and actual['host_report_sha256']==sha(dst/'real-city.json') and actual['remaining']==[]
   if name=='standalone':
    source=dst/'closed.json'
    program=Path('/tmp/donghu-70-350/design/after-223.py');assert sha(program)=='f6a710fdcb7fd2232729afc3386c19cb814170e3f790f1ded8b7836527252f2e'
    subprocess.run([sys.executable,'-B',program,source],check=True)
    returned=program.parents[1]/'223-pilot-closed.json';v=j(returned)
    assert (v['order'],v['host'],v['phase'])==(350,223,'standalone')
    assert v['host_sha256']==sha(source) and v['host_report_sha256']==j(source)['report_sha256']
    assert v['attempted'] and v['remaining']==[] and v['finished'] and v['stages']
    assert all(x['pid']>0 and type(x['exit_code']) is int for x in v['stages'])
    assert v['exit_code']==v['stages'][-1]['exit_code'] and v['passed']==(v['exit_code']==0) and sha(Path(v['log']))==v['log_sha256']
    if v['passed']:assert len(v['stages'])==2 and len(v['products'])==5
    write(w/'350-pilot-handback.json',dict(source=str(source),source_sha256=sha(source),program_sha256=sha(program),result=str(returned),result_sha256=sha(returned),passed=v['passed']))
   if name=='desktop':
    program=Path('/tmp/fenyang359/mapping/223-model.py')
    assert sha(program)=='5a0df40c41cf01a379489a1c5af0ffc7142f8a7aa65261b59a189e7e58880473'
    source=dst/'closed.json'
    subprocess.run([sys.executable,'-B',program,source],check=True)
    returned=program.with_name('223-model-closed.json');actual=j(returned)
    assert actual['order']==359 and actual['host']==223 and actual['phase']=='desktop' and actual['source_sha256']==sha(source) and actual['host_report_sha256']==sha(dst/'report.json')
    assert actual['remaining']==[] and actual['passed']==(actual['exit_code']==0) and sha(Path(actual['log']))==actual['log_sha256']
    vector=Path('/tmp/fenyang359/vector/offer-223.py');assert sha(vector)=='a962dc76ec29f6f57eac069fcfc08dd4b9b7538f5b87ff99df5baad084cab525'
    subprocess.run([sys.executable,'-B',vector,source],check=True)
    receipt=j(vector.with_name('223-vectors-returned.json'))
    assert receipt['order']==359 and receipt['host']==223 and receipt['source_sha256']==sha(source) and receipt['host_report_sha256']==sha(dst/'report.json')
    assert receipt['previous_sha256']==sha(returned) and receipt['remaining']==[]
    if receipt['attempted']:
     assert receipt['passed']==(receipt['exit_code']==0) and sha(Path(receipt['log']))==receipt['log_sha256']
    else:assert receipt['deferred'] and not actual['passed']


   if name=='mouse':
    source=dst/'closed.json';program=Path('/tmp/fenyang357/after-223-mouse.py');assert sha(program)=='8557167cbc39f8d27f2fdd8696ef6d78e0150deed745c4207bf48f65f8837b55'
    receipt_input=source;subprocess.run([sys.executable,'-Bu',program,receipt_input],check=True)
    returned=Path('/tmp/fenyang357/223-source-review-closed.json');result=j(returned)
    assert (result['order'],result['host'])==(357,223)
    assert result['host_sha256']==sha(source) and result['host_report_sha256']==sha(dst/'report.json')
    assert result['remaining']==[] and result['stages'] and result['exit']==result['exit_code']==result['stages'][-1]['exit']
    assert result['passed']==(result['exit']==0) and all(x['pid']>0 and sha(Path(x['log']))==x['log_sha256'] for x in result['stages'])
    if result['passed']: assert len(result['stages'])==3 and all(sha(Path(k))==v for k,v in result['evidence'].items())
    write(w/'357-checked-handback.json',dict(source=str(source),source_sha256=sha(source),return_file=str(returned),return_sha256=sha(returned),passed=result['passed'],finished=result.get('finished',result.get('ended'))))
   if name=='standalone':
    subprocess.run([sys.executable,'-Bu',w/'offer-368-development.py',dst/'closed.json',Path('/tmp/donghu-70-350/223-pilot-closed.json')],check=True)
    prior=Path('/tmp/anfu284-368/development-native/223-development-returned.json')
    entry=Path('/tmp/anfu201-366/design/after-223-model.py')
    assert sha(entry)=='84ba1e9ce23489243356b2e0a4d35042290b075b8e233345147d33491b3678cf'
    subprocess.run([sys.executable,'-Bu',entry,dst/'closed.json',prior],check=True)
    result=Path('/tmp/anfu201-366/223-model-closed.json');rr=j(result)
    assert (rr['order'],rr['host'],rr['phase'])==(366,223,name)
    assert rr['host_sha256']==sha(dst/'closed.json') and rr['host_report_sha256']==sha(dst/'viewer.json')
    assert rr['previous_sha256']==sha(prior) and rr['remaining']==[] and rr['all_children_exited']
    assert rr['phases'] and all(z['pid']>0 and not z['remaining'] and sha(Path(z['log']))==z['log_sha256'] for z in rr['phases'])
    assert rr['exit_code']==rr['phases'][-1]['exit_code'] and rr['passed']==(rr['exit_code']==0)
    write(w/'366-checked-handback.json',dict(host_sha256=rr['host_sha256'],returned=str(result),returned_sha256=sha(result),passed=rr['passed']))
  print('All browser segments closed; inspect the saved photographs before releasing city 224.',flush=True)
