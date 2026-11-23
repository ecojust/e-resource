"""Admit the garden portico only after the previous city phase has closed."""
from pathlib import Path
from datetime import datetime, timezone
import fcntl,hashlib,json,os,runpy,shutil,subprocess,sys,tempfile

here=Path(__file__).resolve().parent
w=Path('/tmp/fuxing-garden339');handoff=w/'mapping/handoff';host=Path('/tmp/shanghai-main-274');p=Path('/workspace/e-resource/projects/shanghai')
ident='huangpu-fuxing-garden-north-house-east-portico';tag='fuxing-garden-east-portico-v1';page='fuxing-garden-east-portico.html'
source=p/'source/precise'/ident/'source';audit=p/'data/audit'/tag;author=audit/'author-scene-review.json';assets=p/'assets/models/candidates'/ident
load=lambda f:json.loads(f.read_bytes())
def sha(f):
    with Path(f).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def write(f,info):
    data=(json.dumps(info,ensure_ascii=False,indent=2)+'\n').encode()
    if f.is_file():assert f.read_bytes()==data,f
    else:
        tmp=f.with_suffix('.partial');tmp.write_bytes(data);os.replace(tmp,f)
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.is_file():assert sha(src)==sha(dst),dst
    else:
        tmp=dst.with_suffix(dst.suffix+'.new');shutil.copyfile(src,tmp);assert sha(tmp)==sha(src);os.replace(tmp,dst)
def prior(f,order):
    j=load(f);assert j['order']==order and j['passed'] and j.get('exit',j.get('exit_code'))==0 and all(not v for k,v in j.items() if k.startswith('remaining'))
    return j
kind=sys.argv[1];assert kind in ('native','viewer');phase={'native':'before','viewer':'phone'}[kind]
closed=Path(sys.argv[2]);assert closed.samefile(host/'evidence/274'/('before' if kind=='native' else 'separate/phone')/'closed.json');rec=load(closed);report=Path(rec['report']);old=load(report)
assert rec['exit']==rec['exit_code']==0 and rec['node_closed'] and rec['chromium_pids'] and rec['remaining_chromium']==rec['remaining']==[] and rec['report_sha256']==sha(report)
assert old['completed'] and old['section']==phase and old['server']==('http://127.0.0.1:31273/' if phase=='before' else 'http://127.0.0.1:31274/') and rec['order']==274 and rec['phase']==phase
contract=load(handoff/'dispatch-recovered.json')
stamp=old['scriptSha256']
driver=here/'host-drivers'/stamp
assert stamp in contract['approved_host_drivers'] and sha(driver)==rec['driver_sha256']==stamp
assert old.get('source_code_sha256',stamp)==stamp
actual_driver=closed.parent/'actual-driver.cjs'
if actual_driver.is_file():assert sha(actual_driver)==stamp
for k,v in contract['programs_and_inputs'].items():assert sha(k)==v,k
assert sha(author)=='f9738363c3dfe969c9652f37da8244b3f0ec5bb12890ab2e1e1463cca9195679'
parent=Path('/tmp/park-fuxing338');prior(parent/'native-closed.json',338);raw=load(parent/'raw-338-confirmed.json');assert raw['order']==338 and raw['sha256']==sha(raw['snapshot'])
if kind=='viewer':prior(parent/'viewer-closed.json',338);prior(w/'native-closed.json',339)
with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    physical=Path('/dev/shm/fuxing-garden339-actual');physical.mkdir(exist_ok=True)
    attempt=Path(tempfile.mkdtemp(prefix=kind+'-',dir=physical));attempt_log=attempt/'run.log'
    temp_scope=tempfile.TemporaryDirectory(prefix='f339-',dir='/dev/shm');env=dict(os.environ,TMPDIR=temp_scope.name,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',GORDON_NATIVE_EVENTS=str(attempt/'native-stages.ndjson'),LD_LIBRARY_PATH='/tmp/country-tools/oidn/lib:'+os.environ.get('LD_LIBRARY_PATH',''))
    new_assets=attempt/'assets';new_audit=attempt/'audit'
    if kind=='native':
        command=[sys.executable,'-Bu',source/'build_model.py','--out',new_assets,'--audit',new_audit,'--blender',here/'blender-one','--oidn',here/'oidn-one','--gltfpack','/workspace/.e-resource-recovery/toolchain/node_modules/gltfpack/cli.js']
    else:
        helper=runpy.run_path(str(here/'signed-viewer-inputs.py'))['inputs']; snapshot=w/'raw-339-confirmed.json';inputs=helper(339,snapshot,ident,page,here/'signed-31339-viewer');write(here/'viewer-inputs.json',inputs)
        command=[sys.executable,'-Bu',here/'run-339-devices.py',ident,attempt]
        env.update(MODEL_BASE_URL='http://127.0.0.1:31339/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
    before=datetime.now(timezone.utc).isoformat();family=runpy.run_path(str(here/'observed_family.py'))
    with attempt_log.open('xb') as log:
        child=subprocess.Popen(['taskset','-c',str(min(os.sched_getaffinity(0))),*command],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);observed=family['watch'](child);code=child.wait()
    temp_scope.cleanup()
    remaining=[pid for pid,row in observed.items() if family['still_alive'](pid,row['birth'])];assert not remaining
    monitored=dict(order=339,host=274,kind=kind,exit=code,pid=child.pid,started=before,finished=datetime.now(timezone.utc).isoformat(),observed_descendants=observed,wrapper_closed=True,all_processes_closed=not remaining,remaining=remaining,host_receipt_sha256=sha(closed),host_report_sha256=sha(report),dispatch_sha256=sha(handoff/'dispatch-recovered.json'),parent_snapshot_sha256=raw['sha256'],parent_receipt_sha256=sha(parent/'raw-338-confirmed.json'))
    write(attempt/'process.json',monitored);assert code==0,(code,attempt_log)
    if kind=='native':
        manifest=load(new_assets/'manifest.json');rows=manifest['assets'];assert set(rows)=={'raw','full','lod','native'} and manifest['geometry_license']=='MIT' and manifest['photos_embedded'] is False
        for role,r in rows.items():
            f=new_assets/r['file'];assert sha(f)==r['sha256'] and f.stat().st_size==r['bytes']
            if role!='native':assert r['sha256']==contract['expected_meshes'][role]['sha256']
        geometry=new_audit/'geometry-native.json'; reopened=load(geometry)['native_reopened_and_compared'];assert reopened['mesh_count']==80 and reopened['match_raw'] and reopened['triangles']==24038 and reopened['materials']==11
        events=[json.loads(line) for line in (attempt/'native-stages.ndjson').read_text().splitlines()];assert [e['stage'] for e in events]==['render','reopen','denoise'] and all(e['exit']==0 for e in events)
        for f in (*new_audit.iterdir(),*new_assets.iterdir()):copy(f,(audit if f.parent==new_audit else assets)/f.name)
        monitored.update(passed=True,assets=rows,manifest_sha256=sha(assets/'manifest.json'),geometry_native_sha256=sha(geometry),group_count=80,blender_pids=[e['pid'] for e in events[:2]],native_stages=events,remaining_blender=[],remaining_oidn=[])
    else:
        target=audit/'standalone-31339';q=load(attempt/'viewer.json');assert q['passed'] and len(q['views'])==6 and len(q['downloads'])==4
        assert [(s['name'],s['viewport']['width'],s['closed'])for s in q['deviceRuns']]==[('desktop',770,True),('mobile',390,True)]
        for device in ['desktop','mobile']:
            proc=load(attempt/(device+'-node-exit.json'));subreport=attempt/(device+'-viewer.json');assert proc['exit']==0 and proc['report_sha256']==sha(subreport)
        for view in q['views']:
            f=attempt/view['filename'];assert sha(f)==view['sha256'];copy(f,target/f.name)
        rows=load(assets/'manifest.json')['assets']
        for role,download in q['downloads'].items():
            f=attempt/'saved'/rows[role]['file'];assert download['saveAsVerified'] and sha(f)==rows[role]['sha256']==download['sha256'] and f.stat().st_size==download['bytes']
        copy(attempt/'viewer.json',target/'viewer.json');chrome=[pid for pid,row in observed.items() if row['name'] in ('chromium','chrome','chrome-headless-shell','headless_shell')];assert chrome
        monitored.update(passed=True,views=6,downloads=4,node=child.pid,report=str(target/'viewer.json'),report_sha256=sha(target/'viewer.json'),receipt_sha256=sha(target/'viewer.json'),chromium_pids=chrome,remaining_chromium=[])
    write(w/(kind+'-closed.json'),monitored)
