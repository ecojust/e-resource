"""Witness three independent map browser processes and offer each closed interval to the next source author."""
import fcntl,hashlib,json,os,shutil,socket,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

here=Path(__file__).resolve().parent
prior=Path('/tmp/shanghai-main-217/217-map-slot-released.json')
def read(f):return json.loads(f.read_bytes())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,d):
    p=f.with_suffix('.pending');p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');p.replace(f)
def now():return datetime.now(timezone.utc).isoformat()
def running(prefix):
    found={}
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            cmd=p.read_bytes().split(b'\0');stat=(p.parent/'stat').read_text().rsplit(')',1)[1].split()
            if stat[0]!='Z' and b'chrom' in cmd[0] and (str(prefix).encode() in b' '.join(cmd) or b'--remote-debugging-port=19518' in cmd):
                found[p.parent.name]=stat[19]
        except OSError:pass
    return found
def observe_children(parent):
    import psutil
    try: children=psutil.Process(parent).children(recursive=True)
    except psutil.Error:return {}
    result={}
    for p in children:
        try:
            if p.name() in ('chrome','chromium','chrome_crashpad_handler'):
                state=(Path('/proc')/str(p.pid)/'stat').read_text().rsplit(')',1)[1].split();result[str(p.pid)]=state[19]
        except (OSError,psutil.Error):pass
    return result

def observed_alive(observed):
    live=[]
    for pid,birth in observed.items():
        try: state=(Path('/proc')/pid/'stat').read_text().rsplit(')',1)[1].split()
        except OSError:continue
        if state[19]==birth and state[0] not in ('Z','X'):live.append(pid)
    return sorted(live)

def open_cdp():
    with socket.socket() as sock:return sock.connect_ex(('127.0.0.1',19518))==0
def checked(f):
    row=read(f)
    assert any(k in row and row[k]==0 for k in ('exit_code','exit','returncode','code')) and not any(row.get(k)for k in ('remaining','remaining_chromium','remaining_blender','remaining_processes')),f
    return row
def offer(stage,previous):
    h=Path('/tmp/fuzhou283');last=Path('/tmp/hankou-garden-hotel282')
    returned=h/('native-closed.json' if stage=='native' else 'independent-closed.json')
    gate=here/f'283-{stage}-window.json';defer=here/f'283-{stage}-deferred.json'
    if returned.is_file():assert checked(returned)['passed'];return
    if defer.is_file():return
    files=[last/'native-closed.json',last/'raw-282-confirmed.json']
    if stage=='viewer':files.extend([last/'viewer-closed.json',h/'native-closed.json',h/'physical-283.json'])
    if not all(p.is_file() for p in files):
        save(defer,{'order':283,'authorized':False,'previous_session':str(previous),'sha256':sha(previous),'absent_at_handoff':[str(p)for p in files if not p.is_file()],'time':now()});return
    checked(files[0]);rr=read(files[1]);assert rr.get('order')==282 and sha(Path(rr['snapshot']))==rr['sha256']
    if stage=='viewer':
        for close in [last/'viewer-closed.json',h/'native-closed.json']:checked(close)
    q=checked(previous);assert sha(Path(q['report']))==q['report_sha256']
    if not gate.exists():save(gate,{'order':283,'authorized':True,'previous_session':str(previous),'previous_session_sha256':sha(previous),'previous_browser_report_sha256':q['report_sha256'],'remaining_chromium':[],'predecessor_receipts':{str(p):sha(p)for p in files},'since':now()})
    print('283',stage,'authorized',flush=True)
    while not(returned.is_file()or defer.is_file()):time.sleep(2)
    if returned.is_file():assert checked(returned)['passed']
def capture(tag,mode,device,previous):
    out=here/'sessions'/tag;out.mkdir(parents=True,exist_ok=True);done=out/'closed.json';report=out/(mode+'.json')
    if done.exists():rc=checked(done);assert sha(Path(rc['report']))==rc['report_sha256'];return done
    if list(out.iterdir()):
        moved=here/'earlier-attempts'/(tag+'-'+datetime.now(timezone.utc).strftime('%H%M%S'));moved.parent.mkdir(exist_ok=True)
        out.rename(moved);out.mkdir()
    prof=Path(max(['/tmp','/dev/shm'],key=lambda s:shutil.disk_usage(s).free))/('sha-map218-'+tag);prof.mkdir(exist_ok=True)
    assert not open_cdp() and not running(prof)
    checker = here/('check-historical-desktop.cjs' if tag=='desktop' else 'check-historical-map.cjs')
    start=now();observed={};env={**os.environ,'TMPDIR':str(prof),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
    with (out/'stdout.log').open('xb') as log:
        child=subprocess.Popen(['node',checker,mode,here/'bound-inputs.json',out,here/'sessions/before/before.json',device],env=env,stdout=log,stderr=subprocess.STDOUT)
        while child.poll() is None:
            observed.update(running(prof));observed.update(observe_children(child.pid));time.sleep(.25)
    for _ in range(25):
        if not open_cdp() and not running(prof) and not observed_alive(observed):break
        time.sleep(.25)
    rc={'order':218,'tag':tag,'start':start,'end':now(),'node_pid':child.pid,'exit_code':child.returncode,'node_closed':child.poll() is not None,'chromium_pids':sorted(map(int,observed)),'remaining_chromium':sorted(set(running(prof)).union(observed_alive(observed))),'observed_chromium':observed,'cdp_closed':not open_cdp(),'report':str(report),'report_sha256':sha(report)if report.is_file()else None,'script_sha256':sha(checker),'previous_session':str(previous),'previous_session_sha256':sha(previous)}
    if child.returncode:save(out/'failed-exit.json',rc);raise SystemExit(child.returncode)
    r=read(report);assert not rc['remaining_chromium'] and rc['cdp_closed'] and observed and r['passed'] and r['browser_closed'] and len(r['captures'])==(1 if tag=='before' else 3)
    assert len(r['trusted_inputs'])==1 and r['trusted_inputs'][0]['trusted']
    assert all(sha(out/im['file'])==im['sha256'] for im in r['captures'])
    save(done,rc);print(tag,rc['end'],flush=True);return done
with(here/'whole-map.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    pins=read(here/'frozen-inputs.json');assert all(sha(here/p)==d for p,d in pins['files'].items())
    while not prior.is_file():time.sleep(3)
    old=read(prior);assert old.get('order',old.get('stage'))==217 and any(old.get(k)==0 for k in ('exit','exit_code','returncode')) and not any(old.get(k)for k in ('remaining_chromium','remaining_processes','remaining'))
    before=checked(here/'sessions/before/closed.json')
    phone=checked(here/'sessions/phone/closed.json')
    assert before['previous_session_sha256']==sha(prior) and phone['previous_session_sha256']==sha(here/'sessions/before/closed.json')
    for stage in ('native-closed.json','independent-closed.json'):assert checked(Path('/tmp/fuzhou283')/stage)['passed']
    prev=prior
    for tag,mode,device,phase in [('before','before','desktop','native'),('phone','after','mobile','viewer'),('desktop','after','desktop',None)]:
        with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as global_lock:
            fcntl.flock(global_lock,fcntl.LOCK_EX);prev=capture(tag,mode,device,prev)
        if phase:offer(phase,prev)
    save(here/'three-scene-outcomes.json',[read(here/'sessions'/tag/'closed.json') for tag in ['before','phone','desktop']])
    aggregate=here/'three-scene-outcomes.json'
    subprocess.run([sys.executable,'-B',here/'guest-338-and-352.py','352'],check=True)
    guest=Path('/tmp/fuxing341/218-after-scenes.py')
    assert sha(guest)=='a8ff4cde7c69435159c75d3b21f155d209f76bf2f5ba01a6828482723d18adbe'
    subprocess.run([sys.executable,'-B',guest,aggregate],check=True)
    returned=Path('/tmp/fuxing341/218-placement-cpu-closed.json');gpu=read(returned)
    assert gpu['source_sha256']==sha(aggregate) and not gpu['remaining'] and isinstance(gpu['exit_code'],int)
    save(here/'341-completed-offer.json',{'program_sha256':sha(guest),'physical_return':str(returned),'return_sha256':sha(returned),'passed':gpu['passed'],'deferred':gpu.get('deferred',False),'exit_code':gpu['exit_code']})
    trial=Path('/tmp/sinan-even342/design/prepare-218-offer.py')
    assert sha(trial)=='207fbeb38fe21356bcc74668477bd39e60fb2e4567bcc45da9d8ae1eb84d5cab'
    subprocess.run([sys.executable,'-B',trial,aggregate,returned],check=True)
    final_trial=Path('/tmp/sinan-even342/218-export-closed.json');model=read(final_trial)
    assert model['host_receipt_sha256']==sha(aggregate) and model['previous_return_sha256']==sha(returned) and model['remaining']==[]
    save(here/'342-completed-offer.json',dict(result=str(final_trial),sha256=sha(final_trial),attempted=model['attempted'],exit_code=model.get('exit_code')))
    print('218 three map viewers actually closed; visual review pending',flush=True)
