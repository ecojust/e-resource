"""Run each authorized city-map view in a fresh Chromium and retain every completed session."""
from pathlib import Path
from datetime import datetime,timezone
import os,sys,json,hashlib,subprocess,time,shutil,fcntl
held_fds=[]
which=int(sys.argv[1]);name,tag={191:('wangdetang','wangdetang-v1'),201:('washington','washington-apartments-v1'),215:('savoy','savoy-apartments-v1')}[which]
base=Path('/dev/shm')/f'qa-{name}{which}-31';project=Path('/workspace/e-resource/projects/shanghai')
case=project/'data/audit'/tag/'map-case.json';driver=base/'check-map-separated.cjs';fixture=base/f'stage{which}';previous=base/f'stage{which-1}/data/candidate-city-integrations.json';sections=base/'separated';sections.mkdir(exist_ok=True)
def now():return datetime.now(timezone.utc).isoformat()
def read(f):return json.loads(f.read_bytes())
def sha(f):
 with f.open('rb') as fp:return hashlib.file_digest(fp,'sha256').hexdigest()
def write(f,obj):
 temp=f.with_suffix('.part');temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');temp.replace(f)
def browser_for(profile):
 rows=[]
 for name in Path('/proc').glob('[0-9]*/comm'):
  try:
   if name.read_text().strip()=='chromium' and (name.parent/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z' and str(profile).encode() in (name.parent/'cmdline').read_bytes():rows.append(int(name.parent.name))
  except OSError:pass
 return rows
def link(src,dst):
 if dst.exists():assert sha(dst)==sha(src)
 else:os.link(src,dst)
context=os.environ.copy()
context.update(OMP_NUM_THREADS='1',MALLOC_ARENA_MAX='2',MALLOC_TRIM_THRESHOLD_='131072',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',SHANGHAI_PROJECT_ROOT=str(fixture))
segment_order=['control','phone','desktop','street','roof','distant'] if which==191 else ['control','phone','desktop','street','roof','phone-zoom','beacon-mouse','beacon-touch','distant']
with (base/'separated.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if which==215:
  cold_start=Path('/tmp/savoy215/340-cpu-returned.json')
  while not cold_start.is_file():time.sleep(1)
  granted=read(cold_start);assert granted['order']==340 and granted['phase']=='initial-export' and granted['actual_processes_closed'] and granted['source'] and granted['checked_utc']
 if which in (201,215) and (base/'catalog-restoration.json').is_file():
  import zstandard,atexit
  held_fds=[]
  scratch_links=[]
  def remove_own_catalog_links():
   for f,raw in scratch_links:
    if f.is_symlink() and os.readlink(f)==raw:f.unlink()
  atexit.register(remove_own_catalog_links)
  for entry in read(base/'catalog-restoration.json')['entries']:
   path=Path(entry['path']);source=Path(entry['archive']);raw=zstandard.ZstdDecompressor().decompress(source.read_bytes())
   assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['signed_sha256']
   if path.is_file() and not path.is_symlink():assert path.read_bytes()==raw;continue
   fd=os.memfd_create('verified-city-215-catalog',os.MFD_ALLOW_SEALING)
   with os.fdopen(os.dup(fd),'wb') as sink:sink.write(raw)
   os.lseek(fd,0,os.SEEK_SET);fcntl.fcntl(fd,1033,15)  # Linux F_ADD_SEALS, all four immutable-data seals
   name='/proc/self/fd/'+str(fd)
   if path.is_symlink():
    assert os.readlink(path).startswith('/proc/');path.unlink()
   path.symlink_to(name);assert sha(path)==entry['signed_sha256'];held_fds.append(fd);scratch_links.append((path,name))
  del raw
 for part in segment_order:
  rcfile=sections/(part+'-closed.json');prior=part=='control';target=which-1 if prior else which
  if rcfile.exists():
   row=read(rcfile)
   if row['exit']==0 and not row['remaining_chromium'] and sha(Path(row['report']))==row['report_sha256'] and read(Path(row['report']))['completed']:continue
  if which==215 and part=='phone':
   host=sections/'control-closed.json'
   prior_run=read(host);report=Path(prior_run['report'])
   assert prior_run['exit']==0 and prior_run['node_closed'] and prior_run['chromium_pids'] and not prior_run['remaining_chromium']
   assert read(report)['completed'] and sha(report)==prior_run['report_sha256']
   guest=Path('/tmp/kemi334/design/215-cpu-window.py')
   assert sha(guest)=='06f9788661ddbbc23a4b0c613f8e99c5be6cb93ded9a72e894034b8ed901e3e1'
   receipt=Path('/tmp/kemi334/215-cpu-closed.json')
   if not receipt.exists():
    guest_run=subprocess.run([sys.executable,'-B',guest,host]);guest_code=guest_run.returncode
   else:guest_code=read(receipt)['exit_code']
   answer=read(receipt)
   assert answer['host']==215 and answer['order']==334 and answer['host_receipt_sha256']==sha(host) and answer['exit_code']==guest_code
   assert not answer['remaining'] and answer['processes'] and all(q['pid'] and q['ended'] for q in answer['processes'])
   write(sections/'334-cpu-handback.json',{'host_receipt':str(host),'host_sha256':sha(host),'guest':str(guest),'guest_sha256':sha(guest),'actual_exit':guest_code,'return':str(receipt),'return_sha256':sha(receipt),'at':now()})
  if which==215 and part=='street':
   host=sections/'desktop-closed.json';parent=read(host);report=Path(parent['report'])
   assert parent['order']==215 and parent['exit']==0 and parent['node_closed'] and parent['chromium_pids'] and not parent['remaining_chromium']
   assert sha(report)==parent['report_sha256'] and read(report)['completed']
   guest=Path('/tmp/fuxing-garden339/mapping/215-desktop-cpu.py');receipt=guest.parent/'215-desktop-cpu-closed.json'
   assert sha(guest)=='66562e370edd342b018710922565f5804c14402b000789bec789a829a1437e80'
   if not receipt.exists():subprocess.run([sys.executable,'-B',guest,host])
   item=read(receipt);assert item['host']==215 and item['order']==339 and item['phase']=='desktop'
   assert item['source_sha256']==sha(host) and item['host_report_sha256']==sha(report) and not item['remaining'] and item['pid']>0
   assert sha(Path(item['log']))==item['log_sha256']
   if item['passed']:assert item['exit_code']==0 and len(item['evidence'])==8 and all(sha(Path(f))==h for f,h in item['evidence'].items())
   write(sections/'339-cpu-handback.json',{'host':str(host),'host_sha256':sha(host),'guest':str(guest),'guest_sha256':sha(guest),'return':str(receipt),'return_sha256':sha(receipt),'exit':item['exit_code'],'at':now()})
  if which==215 and part=='desktop':
   host=sections/'phone-closed.json';parent=read(host);report=Path(parent['report'])
   assert parent['order']==215 and parent['exit']==0 and parent['node_closed'] and parent['chromium_pids'] and not parent['remaining_chromium']
   assert sha(report)==parent['report_sha256'] and read(report)['completed']
   guest=Path('/tmp/shanghai-main-274/215-phone-cpu.py');receipt=guest.parent/'215-phone-cpu-closed.json'
   assert sha(guest)=='9f08f6994cce31e800d7bc954e6edd58b3e0879d4e51ca5b89f0436836838038'
   if not receipt.is_file():
    result=subprocess.run([sys.executable,'-B',guest,host])
   item=read(receipt)
   assert item['order']==274 and item['host']==215 and item['phase']=='phone' and item['remaining']==[]
   assert item['source_sha256']==sha(host) and item['host_report_sha256']==sha(report) and item['supervisor_pid']>0 and item['finished']
   if item['passed']:assert item['exit_code']==0 and sha(Path(item['runtime']))==item['runtime_sha256']
   write(sections/'274-cpu-handback.json',{'host':str(host),'host_sha256':sha(host),'guest':str(guest),'guest_sha256':sha(guest),'return':str(receipt),'return_sha256':sha(receipt),'exit':item['exit_code'],'at':now()})
  if which==201 and part=='phone':
   handoff=sections/'control-closed.json'
   control=read(handoff)
   assert control['exit']==0 and not control['remaining_chromium']
   assert not browser_for(Path(control['profile'])) and not Path('/proc',str(control['node_pid'])).exists()
   assert sha(Path(control['report']))==control['report_sha256'] and read(Path(control['report']))['completed']
   resume=base/'resume-after-266.json'
   print('201 old-city control finished; 266 has the reserved native interval.',flush=True)
   native=Path('/tmp/yuanyuanchang266/native-closed.json')
   deferred=Path('/tmp/yuanyuanchang266/201-window-deferred.json')
   while not (native.exists() or deferred.exists() or resume.exists()):time.sleep(2)
   if not resume.exists():
    witness=deferred if deferred.exists() else native
    item=read(witness)
    if witness==native:
     assert item['exit']==0 and item['passed'] and item['all_processes_closed']
     assert len(item['assets'])==4 and all(len(a['sha256'])==64 and a['bytes']>0 for a in item['assets'].values())
    else:
     assert item['order']==266 and item['deferred'] and item['blender_started'] is False and item['missing']
    write(resume,{'order':201,'native_ran':witness==native,'control_sha256':sha(handoff),
           'receipt':str(witness),'receipt_sha256':sha(witness),'at':now()})
   go=read(resume)
   assert go['order']==201 and go['control_sha256']==sha(handoff)
   witness=Path(go['receipt']);other=read(witness);assert sha(witness)==go['receipt_sha256']
   if go['native_ran']:
    assert witness==Path('/tmp/yuanyuanchang266/native-closed.json') and other['exit']==0 and other['passed']
   else:
    assert witness==Path('/tmp/yuanyuanchang266/201-window-deferred.json') and other['deferred'] and not other['blender_started']
  if which==191 and part=='phone':
   previous_closed=read(sections/'control-closed.json')
   assert previous_closed['exit']==0 and not previous_closed['remaining_chromium']
   pause=base/'resume-after-258.json'
   print('191 prior released; waiting for 258 native admission or explicit release',flush=True)
   while not pause.is_file():time.sleep(2)
   grant=read(pause)
   assert grant['order']==191 and grant['after_segment']=='control' and grant['control_sha256']==sha(sections/'control-closed.json')
   if grant['native_ran']:
    native=Path('/tmp/reiss258/native-exit.json')
    assert sha(native)==grant['native_sha256'] and read(native)['exit']==0 and read(native)['passed']
   else:assert grant['coordinator']=='browser' and grant['reason']
  if which==201 and part=='street':
   handoff=sections/'desktop-closed.json';q=read(handoff)
   assert q['exit']==0 and not q['remaining_chromium'] and not browser_for(Path(q['profile']))
   assert not Path('/proc',str(q['node_pid'])).exists() and read(Path(q['report']))['completed']
   assert sha(Path(q['report']))==q['report_sha256']
   other=Path('/dev/shm/qa-savoy215-31/final-standalone/viewer.json')
   if not other.exists():
    scratch=Path(subprocess.check_output([sys.executable,'-B','/tmp/sichuan223/choose-profile.py','qa-savoy215-31'],text=True).strip())/'official-standalone'
    scratch.mkdir(exist_ok=True)
    subprocess.run([sys.executable,'-B','/tmp/sichuan223/check-standalone-final.py','215'],check=True,env={**os.environ,'TMPDIR':str(scratch)})
    for tick in range(30):
     if not browser_for(scratch):break
     time.sleep(.2)
    assert not browser_for(scratch)
   j=read(other);assert j['passed'] and not j['pageErrors'] and len(j['downloads'])==4 and len(j['views'])==4
   assert all(sha(other.parent/v['filename'])==v['sha256']for v in j['views'])
   write(sections/'215-standalone-replay.json',{'order':215,'exit':0,'signed_site':31215,'map_handoff_sha256':sha(handoff),'report':str(other),'report_sha256':sha(other),'completed':now()})
   saved=Path('/tmp/zili265/viewer-closed.json')
   deferred=Path('/tmp/zili265/201-viewer-deferred.json')
   print('201 desktop and 215 viewer closed; reserved 265 viewer interval.',flush=True)
   while not saved.is_file() and not deferred.is_file():time.sleep(2)
   witness=saved if saved.is_file() else deferred
   outcome=read(witness)
   assert outcome['order']==265
   if witness==saved:assert outcome['exit']==0 and outcome['remaining_chromium']==[]
   else:assert outcome['deferred'] and outcome['browser_started'] is False
   write(sections/'265-viewer-handback.json',{'witness':str(witness),'sha256':sha(witness),'checked':now()})
  if which==191 and part=='street':
   desktop_closed=read(sections/'desktop-closed.json')
   assert desktop_closed['exit']==0 and not desktop_closed['remaining_chromium'] and read(Path(desktop_closed['report']))['completed']
   wait=Path('/tmp/chienhsin257/viewer-closed.json')
   print('191 desktop released; waiting for 257 standalone close',flush=True)
   while not wait.exists():time.sleep(2)
   check=read(wait)
   assert check['order']==257 and check['exit']==0 and check['remaining_chromium']==[]
  top=Path(subprocess.check_output([sys.executable,'-B','/tmp/sichuan223/choose-profile.py',base.name],text=True).strip())
  stamp=str(time.time_ns());out=sections/(part+'-'+stamp);out.mkdir();profile=top/('part-'+stamp);profile.mkdir()
  cfg={**context,'TMPDIR':str(profile),'QA_OUTPUT_DIR':str(out),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+target}/','QA_SEGMENT':part}
  if prior:cfg.update(QA_CONTROL_CATALOG=str(previous),QA_CONTROL_CATALOG_SHA256=sha(previous),QA_CONTROL_CITY_COUNT=str(read(previous)['resulting_city_count']))
  start=now()
  with (out/'node.log').open('ab')as log:
   import psutil
   for actual in (driver,Path(__file__)):shutil.copy2(actual,out/actual.name)
   proc=subprocess.Popen(['node',driver,case,*(['--control']if prior else[])],env=cfg,stdout=log,stderr=log,start_new_session=True,pass_fds=tuple(held_fds))
   node=psutil.Process(proc.pid);observed={}
   while proc.poll() is None:
    try:
     for child in node.children(recursive=True):
      try:
       if child.name() in ('chromium','chrome'):observed[child.pid]=child.create_time()
      except psutil.Error:pass
    except psutil.Error:pass
    time.sleep(.12)
   rc=proc.wait()
   def still_running(pid,born):
    try:
     found=psutil.Process(pid)
     return found.create_time()==born and found.status()!=psutil.STATUS_ZOMBIE
    except psutil.Error:return False
   for _ in range(60):
    if not any(still_running(pid,born)for pid,born in observed.items()):break
    time.sleep(.1)
   residual=[pid for pid,born in observed.items()if still_running(pid,born)]

  for _ in range(26):
   if not browser_for(profile):break
   time.sleep(.25)
  doc=out/('control-browser.json'if prior else'main-browser.json')
  row={'order':which,'segment':part,'start':start,'finished':now(),'exit':rc,'node_pid':proc.pid,'observed_chromium':observed,'node_closed':proc.poll() is not None,'chromium_pids':sorted(observed),'remaining_chromium':sorted(set(browser_for(profile))|set(residual)),'profile':str(profile),'report':str(doc),'report_sha256':sha(doc) if doc.is_file()else None}
  write(out/'closed.json',row);write(rcfile,row)
  assert rc==0 and observed and not row['remaining_chromium'] and read(doc)['completed'],row
  if profile.is_dir()and not list(profile.iterdir()):profile.rmdir()
  print(part,row['finished'],flush=True)
 old=base/'evidence/before';old.mkdir(parents=True,exist_ok=True)
 prior=Path(read(sections/'control-closed.json')['report']);link(prior,old/'control-browser.json')
 for shot in read(prior)['screenshots']:link(prior.parent/shot['file'],old/shot['file'])
 after=base/'evidence/after';after.mkdir(parents=True,exist_ok=True)
 parts=[read(sections/(mode+'-closed.json')) for mode in segment_order[1:]]
 docs=[read(Path(p['report']))for p in parts]
 if which==201:
  accepted_drivers={'control':base/'check-map-full-desktop.cjs','phone':base/'check-map-full-desktop.cjs','desktop':base/'check-map-compact-desktop.cjs','street':base/'check-map-street-session.cjs',**{k:base/'check-map-roof-and-actions.cjs' for k in ['roof','phone-zoom','beacon-mouse','beacon-touch']}}
  for part,doc in zip(segment_order[1:],docs):assert doc['scriptSha256']==sha(accepted_drivers.get(part,driver))
 elif which==215:
  for row,report in zip(parts,docs):assert sha(Path(row['report']).parent/driver.name)==report['scriptSha256']
 else:assert all(d['scriptSha256']==docs[0]['scriptSha256'] for d in docs)
 for field in ['catalog','bindings','id','caseSha256','server','camera']:assert all(d[field]==docs[0][field] for d in docs)
 merged={k:v for k,v in docs[0].items()if k not in {'segment','desktopOnly'}}
 for key in ['views','screenshots','errors','warnings','files','failed','ground']:merged[key]=[v for d in docs for v in d.get(key,[])]
 merged.update(finished=docs[-1]['finished'],completed=True,individual_browser_sessions=parts,individual_scripts={d['segment']:d['scriptSha256'] for d in docs})
 for path,doc in zip(parts,docs):
  for shot in doc['screenshots']:
   f=Path(path['report']).parent/shot['file'];assert sha(f)==shot['sha256'];link(f,after/f.name)
 write(after/'main-browser.json',merged);(base/'exit').write_text('0\n')
 subprocess.run([sys.executable,'-B','/tmp/sichuan223/collect-map-after-close.py',str(which)],check=True)
 target=project/'data/audit'/tag/f'city-{31000+which}'/'separated-sessions';target.mkdir(exist_ok=True)
 for mode in segment_order:
  f=sections/(mode+'-closed.json');row=read(f);doc=Path(row['report'])
  if which==215:
   actual_driver=doc.parent/driver.name;assert sha(actual_driver)==read(doc)['scriptSha256'];shutil.copy2(actual_driver,target/(mode+'-driver.cjs'))
  for src,outname in [(f,mode+'-closed.json'),(doc,mode+'-browser.json')]:
   shutil.copy2(src,target/outname);assert sha(src)==sha(target/outname)
 for src in [Path(__file__),driver]+([base/'check-map-full-desktop.cjs',base/'check-map-compact-desktop.cjs',base/'check-map-street-session.cjs',base/'check-map-roof-and-actions.cjs'] if which==201 else []):
  shutil.copy2(src,target/src.name)
 print('complete',which,now(),flush=True)
 if which in (191,201,215):
  closed=[read(sections/(mode+'-closed.json')) for mode in segment_order]
  for entry in closed:
   assert entry['exit']==0 and not entry['remaining_chromium'] and not browser_for(Path(entry['profile'])) and not Path('/proc',str(entry['node_pid'])).exists()
  assert all(read(Path(entry['report']))['completed'] and sha(Path(entry['report']))==entry['report_sha256']for entry in closed)
  durable={191:Path('/tmp/wangdetang191'),201:Path('/tmp/washington201'),215:Path('/tmp/savoy215')}[which]
  durable.mkdir(exist_ok=True)
  write(durable/f'{which}-all-sessions-closed.json',{'order':which,'passed':True,'exit':0,'exit_code':0,'actual_last_exit_utc':closed[-1]['finished'],'all_exited':True,'remaining_chromium':[],'before_report':str(old/'control-browser.json'),'after_report':str(after/'main-browser.json'),'segments':closed})
