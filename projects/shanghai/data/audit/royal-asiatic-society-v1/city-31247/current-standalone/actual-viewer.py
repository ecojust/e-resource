"""Run the ordinary museum page after the last city session and retain the four downloads."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,tempfile,time,fcntl
import psutil
w=Path(__file__).resolve().parent;host=Path('/tmp/shanghai-main-247/formal-31247')
h=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    b=(json.dumps(d,indent=2)+'\n').encode()
    t=p.with_suffix('.pending');t.write_bytes(b);t.replace(p)
def active(pid,birth):
    try:
        proc=psutil.Process(pid)
        return proc.create_time()==birth and proc.status()!=psutil.STATUS_ZOMBIE
    except psutil.Error:return False
pin=read(w/'formal-viewer-sources.json')
assert h((w/'formal-viewer.cjs').read_bytes())==pin['driver_sha256']
last=host/'isolated-evidence/distant/closed.json';close=read(last)
assert close['phase']=='distant' and close['exit_code']==0 and close['cdp_closed'] and close['remaining']==[]
outdir=host/'current-standalone'
outdir.mkdir(exist_ok=True)
with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lk:
    fcntl.flock(lk,fcntl.LOCK_EX)
    assert not (outdir/'closed.json').exists()
    dest=outdir/str(time.time_ns());dest.mkdir();start=now();seen={}
    with (dest/'node.log').open('wb') as log,tempfile.TemporaryDirectory(prefix='browser247-',dir='/dev/shm')as temp:
        env={**os.environ,'MODEL_BASE_URL':'http://127.0.0.1:31247/','TMPDIR':temp,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
        p=subprocess.Popen(['node',w/'formal-viewer.cjs','huangpu-royal-asiatic-society-huqiu-front',dest],env=env,stdout=log,stderr=subprocess.STDOUT)
        while p.poll() is None:
            try:children=psutil.Process(p.pid).children(recursive=True)
            except psutil.Error:children=[]
            for c in children:
                try:
                    if c.name()in ('chrome','chromium','chrome_crashpad_handler'):seen[c.pid]=c.create_time()
                except psutil.Error:pass
            time.sleep(.1)
        for _ in range(60):
            remaining=[k for k,v in seen.items() if active(k,v)]
            if not remaining:break
            time.sleep(.1)
    ev=dict(order=247,phase='independent',started=start,finished=now(),node_pid=p.pid,exit_code=p.returncode,chromium=seen,remaining=remaining,driver_sha256=pin['driver_sha256'],prior_sha256=h(last.read_bytes()),stdout_sha256=h((dest/'node.log').read_bytes()))
    if (dest/'viewer.json').is_file():ev.update(report_sha256=h((dest/'viewer.json').read_bytes()))
    save(dest/'process.json',ev)
    assert p.returncode==0 and not remaining and seen,ev
    report=read(dest/'viewer.json');old=read(host/'standalone-originals.json');assert report['passed'] and len(report['views'])==4 and report['base']=='http://127.0.0.1:31247/' and report['formalInputs']==pin['inputs'] and report['productionSHA256']==pin['production_sha256']
    assert report['scriptSHA256']==pin['driver_sha256'] and report['downloads'].keys()==old['downloads'].keys()
    for role,r in report['downloads'].items():
        assert r['saveAsVerified'] and old['downloads'][role]=={k:r[k] for k in ('file','bytes','sha256')}
        f=dest/'saved'/r['file'];assert f.stat().st_size==r['bytes'] and h(f.read_bytes())==r['sha256']
    assert {(r['viewport']['width'],r['role']) for r in report['views']}=={(width,role)for width in [390,1250] for role in ['full','lod']}
    for im in report['views']:assert h((dest/im['filename']).read_bytes())==im['sha256']
    ev.update(passed=True,report=str(dest/'viewer.json'),proof=str(dest/'process.json'),downloads=report['downloads'],views=report['views'])
    save(outdir/'closed.json',ev)

child=w/'after-viewer-580.py'
assert h(child.read_bytes())=='4dcb875a575b00a328e31d56ba238c0a919c87ea869af3316d421b515664320f'
subprocess.run([sys.executable,'-Bu',child],check=True)

late=Path('/workspace/.e-resource-recovery/grace/reboot245/after-247-580.py')
assert h(late.read_bytes())=='cfe540bdf89853a1cc32150705779976f0ed114830efca6552845c303ad5ec02'
previous=Path('/dev/shm/root-jkk580/development-native/early-development-returned.json')
subprocess.run([sys.executable,'-Bu',late,outdir/'closed.json',previous],check=True)
both=read(Path('/tmp/pingliang25-658/247-658-662-returned.json'))
assert both['passed'] and both['exit_code']==0 and both['all_children_exited'] and not both['remaining_children']
assert both['host_sha256']==h((outdir/'closed.json').read_bytes()) and both['after_580_sha256']==h(previous.read_bytes())
assert [r['order'] for r in both['physical_returns']]==[658,662]
for row in both['physical_returns']:
    assert row['return_sha256']==h(Path(row['return_file']).read_bytes()) and len(row['four_assets'])==4
