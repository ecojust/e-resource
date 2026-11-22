"""Collect real, sequential browser sessions and preserve the complete evidence of any failed attempt."""
from pathlib import Path
import datetime, fcntl, hashlib, json, os, shutil, subprocess, sys, time
import psutil

work=Path('/tmp/shanghai-main-258')
parent=Path('/tmp/shanghai-main-257/257-map-slot-released.json')
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,value):
    tmp=p.with_suffix('.writing')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(p)
def validate_parent():
    p=load(parent)
    assert p['order']==257 and p['passed'] and p['exit_code']==0 and p['remaining_chromium']==[]
    assert p['results_sha256']==sha(Path('/workspace/e-resource/projects/shanghai/data/audit/qianxin-historic-front-v1/city-31257/results.json'))
    accepted=Path('/workspace/e-resource/projects/shanghai/data/audit/qianxin-historic-front-v1/city-31257/results.json')
    assert load(accepted)=={k:v for k,v in p.items() if k!='results_sha256'}
    for shot in p['screenshots'].values():assert sha(shot['source'])==shot['sha256']
    assert p['all_captures_visually_reviewed'] and p['after_real_screenshot_review'] and p['views_reviewed'] and p['finished']
    assert len(p['actual_saved_downloads'])==4 and p['screenshots']
    assert p['reports']==p['receipts'] and set(p['reports'])==set(p['real_browser_process_exits'])
    assert set(p['reports'])=={'before','phone','desktop'} and len(p['screenshots'])==11
    assert set(p['guest_322'])=={'native','viewer'}
    for item in p['guest_322'].values():assert sha(item['path'])==item['sha256']
    for key,row in p['reports'].items():
        exit_record=load(row['exit'])
        assert exit_record==p['real_browser_process_exits'][key] and sha(row['exit'])==row['exit_sha256']
        assert exit_record.get('code',exit_record.get('exit_code'))==0 and exit_record['node_closed'] and exit_record['chromium_pids'] and exit_record['remaining_chromium']==[]
        assert exit_record['report_sha256']==sha(row['report'])==row['report_sha256']
def live(pid,birth):
    try:return psutil.Process(pid).create_time()==birth and psutil.Process(pid).status()!=psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:return False
def current_children(phase):
    token=f'SHANGHAI_258_PHASE={phase}'.encode()
    identities=[]
    for child in psutil.process_iter(['pid','status']):
        if child.info['status']==psutil.STATUS_ZOMBIE:continue
        try:
            entries=Path('/proc',str(child.pid),'environ').read_bytes().split(b'\0')
        except OSError:continue
        if token in entries:identities.append(child.pid)
    return identities
def phase(tag,mode,device):
    out=work/'evidence'/tag;out.mkdir(parents=True,exist_ok=True)
    receipt=out/'closed.json';report=out/(mode+'.json')
    interrupted=not receipt.exists() and any(out.iterdir())
    if interrupted or (receipt.exists() and load(receipt)['exit_code']!=0):
        assert not current_children(tag), f'A previous {tag} process is still running'
        if interrupted:
            write(out/'interrupted.json',dict(phase=tag,observed_files={f.name:sha(f) for f in out.iterdir() if f.is_file()},remaining=[]))
            identifier=sha(out/'interrupted.json')
        else:identifier=sha(receipt)
        evidence=work/'attempts'/f'{tag}-{identifier[:12]}'
        evidence.parent.mkdir(exist_ok=True)
        assert not evidence.exists()
        out.rename(evidence);out.mkdir()
    if not receipt.exists():
        temp=Path(max(('/dev/shm','/tmp'),key=lambda item:shutil.disk_usage(item).free))/('city-258-'+tag)
        temp.mkdir(exist_ok=True)
        env={**os.environ,'TMPDIR':str(temp),'SHANGHAI_258_PHASE':tag,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
        start=now();seen={}
        with (out/'process.log').open('ab')as log:
            process=subprocess.Popen(['node',work/'check-historical-map.cjs',mode,work/'bound-inputs.json',out,work/'evidence/before/before.json',device],env=env,stdout=log,stderr=log,start_new_session=True)
            main=psutil.Process(process.pid);main_birth=main.create_time()
            while process.poll() is None:
                try:
                    for child in main.children(recursive=True):
                        try:
                            if 'chrom' in child.name().lower():seen[child.pid]=child.create_time()
                        except psutil.NoSuchProcess:pass
                except psutil.NoSuchProcess:pass
                time.sleep(.2)
            code=process.wait()
        for attempt in range(50):
            remaining=sorted(set(current_children(tag))|{pid for pid,birth in seen.items() if live(pid,birth)})
            if not remaining:break
            time.sleep(.2)
        write(receipt,dict(order=258,tag=tag,phase=tag,start=start,finished=now(),exit=code,exit_code=code,node_closed=not live(process.pid,main_birth),node_pid=process.pid,node_birth=main_birth,chromium_pids=sorted(seen),chromium_birth_times=seen,remaining=remaining,remaining_chromium=remaining,report=str(report),report_sha256=sha(report) if report.is_file() else None,process_log_sha256=sha(out/'process.log')))
    state=load(receipt)
    assert state['exit_code']==0 and state['node_closed'] and state['chromium_pids'] and not state['remaining_chromium'] and sha(report)==state['report_sha256']
    data=load(report)
    assert data['script_sha256']==sha(work/'check-historical-map.cjs') and data['signed_input_sha256']==sha(work/'bound-inputs.json')
    assert data['completed'] and data['passed'] and data['browser_closed'] and data['section']==tag
    assert len(data['captures'])==(1 if tag=='before'else 5)
    assert len(data['trusted_inputs'])==1 and data['trusted_inputs'][0]['trusted']
    if tag=='desktop':assert len(data['saved_downloads'])==4
    for capture in data['captures']:assert sha(out/capture['file'])==capture['sha256']
    return state
with (work/'admission.lock').open('a')as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    validate_parent()
    runs=[]
    for tag,mode,device in [('before','before','desktop'),('phone','after','mobile'),('desktop','after','desktop')]:
        for attempt in range(2):
            try:
                completed=phase(tag,mode,device)
                break
            except (AssertionError,FileNotFoundError):
                status=work/'evidence'/tag/'closed.json'
                if attempt or not status.is_file() or load(status)['exit_code']==0 or current_children(tag):raise
        runs.append(completed)
        if tag!='desktop':subprocess.run([sys.executable,'-Bu',work/'offer-323.py','native' if tag=='before'else'viewer'],check=True)
    write(work/'actual-sessions.json',runs)
    guest=Path('/tmp/hujiang433/development-native/after-258.py');assert sha(guest)=='9613e98e517a6f6a8cf4c2939433bb8755b70eec77750a9af54b7a287f1750a9'
    result=subprocess.run([sys.executable,'-Bu',guest,work/'actual-sessions.json'])
    seal=load(guest.parent/'258-development-returned.json')
    assert seal['order']==433 and seal['host']==258 and seal['previous_sha256']==sha(work/'actual-sessions.json') and seal['host_receipt_sha256']==sha(work/'evidence/desktop/closed.json') and seal['all_children_exited'] and not seal['remaining_children']
    if seal['started']:assert sha(Path(seal['physical']))==seal['physical_sha256'] and seal['exit_code']==result.returncode
    else:assert seal['deferred'] and not result.returncode
