"""Run each public input only after the complete physical exit of city 220."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,os,psutil,subprocess,sys,tempfile,time
w=Path(__file__).resolve().parent;p=Path('/workspace/e-resource/projects/shanghai')
prior=Path('/tmp/yangshupu220/220-map-slot-released.json')
j=lambda path:json.loads(path.read_bytes())
def sha(path):
 with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,data):
 temp=path.with_suffix('.new');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
def wait_for_prior():
 while not prior.is_file():time.sleep(5)
 x=j(prior)
 assert x['order']==220 and x['passed']and x['actual_closed_utc']and x['remaining_chromium']==[]and x['all_captures_visually_reviewed']and x['sessions']
 def verify(z):
  if isinstance(z,dict):
   for key,val in z.items():
    for k in ['sha256',key+'_sha256']:
     if key in ('path','report','exit','receipt','closed')and isinstance(val,str)and val.startswith('/')and isinstance(z.get(k),str):assert sha(Path(val))==z[k]
    verify(val)
  elif isinstance(z,list):
   for v in z:verify(v)
 for part in x['sessions']:
  f=Path(part['report']);assert part['exit_code']==0 and part['remaining_chromium']==[] and sha(f)==part['sha256']
 verify(x['reports'])
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
 with (w/'render.lock').open('a')as citylock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light,(dst/'run.log').open('w')as log,tempfile.TemporaryDirectory(prefix='bridge221-'+name+'-')as temp:
  fcntl.flock(citylock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
  env={**os.environ,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','MODEL_BASE_URL':'http://127.0.0.1:31221/','TMPDIR':temp}
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
  proof=j(w/'presentation-inputs.json');assert proof['passed']and proof['rows']['221']['count']==258
  for name in ['before','phone','desktop','mouse','touch','walk-phone','walk-desktop','standalone']:
   dst=w/'sessions'/name
   if name=='standalone':args=['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',p/'tools/check-candidate-viewer.cjs','huangpu-waibaidu-bridge',dst];report='viewer.json'
   elif name.startswith('walk'):args=['node',w/'walk.cjs','221',dst,'390' if name=='walk-phone'else'850'];report='real-city.json'
   else:args=['node',w/'overview.cjs',name,dst];report='report.json'
   phase(name,args,report,gate)
   if name=='touch':
    source=dst/'closed.json'
    program=Path('/tmp/jingu-shaoxing346/design/after-221.py');assert sha(program)=='a9943bc367e38f35e052e99ac0073098d5159ebc2474bed1a68e5871741de616'
    subprocess.run([sys.executable,'-B',program,source],check=True)
    returned=program.parents[1]/'221-pilot-closed.json';v=j(returned)
    assert (v['order'],v['host'],v['phase'])==(346,221,'touch')
    assert v['host_sha256']==sha(source) and v['host_report_sha256']==j(source)['report_sha256']
    assert v['attempted'] and v['remaining']==[] and v['finished'] and v['stages']
    assert all(x['pid']>0 and type(x['exit_code']) is int for x in v['stages'])
    assert v['exit_code']==v['stages'][-1]['exit_code'] and v['passed']==(v['exit_code']==0) and sha(Path(v['log']))==v['log_sha256']
    if v['passed']:assert len(v['stages'])==2 and len(v['products'])==5
    write(w/'346-pilot-handback.json',dict(source=str(source),source_sha256=sha(source),program_sha256=sha(program),result=str(returned),result_sha256=sha(returned),passed=v['passed']))
   if name=='desktop':
    program=Path('/tmp/shaoxing9-347/mapping/221-after-desktop.py')
    assert sha(program)=='af92636e0482cf2cd017a13db98cdc871c74fcafdb0ae0857834ec493ae82dbe'
    host=dst/'closed.json';subprocess.run([sys.executable,'-B',program,host],check=True)
    handback=program.parent/'221-city-cpu-closed.json';msg=j(handback)
    assert msg['order']==347 and msg['host']==221 and msg['host_sha256']==sha(host)
    assert msg['host_report_sha256']==sha(dst/'report.json') and msg['remaining']==[] and msg['finished']
    if msg['attempted']:
     parts=msg['phases'];assert parts and all(x['pid']>0 and 'exit' in x for x in parts)
     assert msg['passed']==(msg['exit']==msg['exit_code']==0) and sha(Path(msg['log']))==msg['log_sha256']
     if msg['passed']:assert len(parts)==3 and len(msg['evidence'])==7 and all(sha(Path(f))==v for f,v in msg['evidence'].items())
    else:assert msg['deferred'] and not msg['passed'] and not msg['phases']
    write(w/'347-city-cpu-handback.json',dict(host=str(host),host_sha256=sha(host),result=str(handback),result_sha256=sha(handback),program_sha256=sha(program),passed=msg['passed'],attempted=msg['attempted'],finished=msg['finished']))
   if name=='standalone':
    program=Path('/tmp/fuxing341/221-runtime-window.py')
    assert sha(program)=='dbbc44bd948c2fc1560124ccfb4f4818c4c40ff5792a4e2e6456ca0e6a48bd07'
    host=dst/'closed.json'
    subprocess.run([sys.executable,'-B',program,host],check=True)
    handback=program.parent/'221-cpu-closed.json'
    msg=j(handback)
    assert (msg['order'],msg['host'],msg['phase'])==(341,221,'standalone')
    assert msg['source_sha256']==msg['host_receipt_sha256']==sha(host)
    assert msg['host_report_sha256']==sha(dst/'viewer.json') and msg['remaining']==[] and msg['finished']
    if msg['attempted']:
     parts=msg['stages']
     assert parts and all(x['pid']>0 and sha(Path(x['log']))==x['log_sha256'] for x in parts)
     assert msg['exit_code']==parts[-1]['exit_code']
     assert msg['passed']==(len(parts)==4 and all(x['exit_code']==0 for x in parts))
    else:assert msg['deferred'] and not msg['passed'] and msg['exit_code'] is None and not msg['stages']
    write(w/'341-city-cpu-handback.json',dict(host=str(host),host_sha256=sha(host),result=str(handback),result_sha256=sha(handback),program_sha256=sha(program),passed=msg['passed'],attempted=msg['attempted'],finished=msg['finished']))
    program=Path('/tmp/jiangvilla349/221-runtime-window.py')
    assert sha(program)=='970bb24d3480870030f89044dbb0da70df022a0ca390aaeaea27d77aef220556'
    host=dst/'closed.json'
    subprocess.run([sys.executable,'-B',program,host],check=True)
    handback=program.parent/'221-cpu-closed.json'
    msg=j(handback)
    assert (msg['order'],msg['host'],msg['phase'])==(349,221,'standalone')
    assert msg['source_sha256']==msg['host_receipt_sha256']==sha(host)
    assert msg['host_report_sha256']==sha(dst/'viewer.json') and msg['remaining']==[] and msg['finished']
    if msg['attempted']:
     parts=msg['stages']
     assert parts and all(x['pid']>0 and sha(Path(x['log']))==x['log_sha256'] for x in parts)
     assert msg['exit_code']==parts[-1]['exit_code']
     assert msg['passed']==(len(parts)==4 and all(x['exit_code']==0 for x in parts))
    else:assert msg['deferred'] and not msg['passed'] and msg['exit_code'] is None and not msg['stages']
    write(w/'349-city-cpu-handback.json',dict(host=str(host),host_sha256=sha(host),result=str(handback),result_sha256=sha(handback),program_sha256=sha(program),passed=msg['passed'],attempted=msg['attempted'],finished=msg['finished']))
   if name in ['before','phone']:subprocess.run([sys.executable,'-B',w/'offer-286.py',name],check=True)
   if name=='walk-phone':
    source=dst/'closed.json';program=Path('/tmp/park-fuxing338/design/after-221-walk-phone.py');assert sha(program)=='d616c314b35b7d8ba6a20d0b5af961f727899abd27523f2c439a33c310ce9206'
    receipt_input=source;subprocess.run([sys.executable,'-Bu',program,receipt_input],check=True)
    returned=Path('/tmp/park-fuxing338/221-map-cpu-closed.json');result=j(returned)
    assert (result['order'],result['host'])==(338,221)
    assert result['host_sha256']==sha(source) and result['host_report_sha256']==sha(dst/'real-city.json') and j(dst/'real-city-mesh.json')['passed']
    assert result['remaining']==[] and result['stages'] and result['exit_code']==result['stages'][-1]['exit_code'] and result['passed']==(result['exit_code']==0)
    write(w/'338-checked-handback.json',dict(source=str(source),source_sha256=sha(source),return_file=str(returned),return_sha256=sha(returned),passed=result['passed'],finished=result.get('finished',result.get('ended'))))
   if name=='standalone':
    source=dst/'closed.json';program=Path('/tmp/elisabeth360/development-native/after-221.py');assert sha(program)=='89164383e1a79d117cbaadcd38944387105a8a15e61c05aee9887a2ac1d981e7'
    receipt_input=Path('/tmp/jiangvilla349/221-cpu-closed.json');subprocess.run([sys.executable,'-Bu',program,receipt_input],check=True)
    returned=Path('/tmp/elisabeth360/development-native/221-development-returned.json');result=j(returned)
    assert (result['order'],result['host'])==(360,221)
    assert result['previous_sha256']==sha(receipt_input) and result['host_sha256']==sha(source) and result['all_children_exited'] and result['remaining_children']==[]
    if result['attempted']:
     assert result['passed']==(result['exit_code']==0) and result['pid']>0
     if result['passed']: assert sha(Path(result['physical']))==result['physical_sha256']
    else: assert result['deferred'] and result['exit_code'] is None and result['missing']
    write(w/'360-checked-handback.json',dict(source=str(source),source_sha256=sha(source),return_file=str(returned),return_sha256=sha(returned),passed=result['passed'],finished=result.get('finished',result.get('ended'))))
  print('All browser segments closed; inspect the saved photographs before releasing city 222.',flush=True)
