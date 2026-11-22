"""Admit the recovered Jiaozhou gate build only on its observed city 253 closure."""
from pathlib import Path
from datetime import datetime, timezone
import fcntl,hashlib,json,os,runpy,shutil,subprocess,sys,tempfile

here=Path(__file__).resolve().parent
w=Path('/tmp/gong-residence318');handoff=w/'mapping/handoff';host=Path('/tmp/shanghai-main-253');p=Path('/workspace/e-resource/projects/shanghai')
ident='jingan-gong-residence-jiaozhou-gate';tag='gong-residence-jiaozhou-gate-v1';page='gong-residence-jiaozhou-gate.html'
source=p/'source/precise'/ident/'source';audit=p/'data/audit'/tag;author=audit/'preflight/model-review.json';assets=p/'assets/models/candidates'/ident
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
closed=Path(sys.argv[2]);assert closed.samefile(host/'evidence'/phase/'closed.json');rec=load(closed);report=Path(rec['report']);old=load(report)
assert rec['exit']==rec['exit_code']==0 and rec['node_closed'] and rec['chromium_pids'] and rec['remaining_chromium']==rec['remaining']==[] and rec['report_sha256']==sha(report)
assert old['completed'] and old['section']==phase and rec['order']==253 and rec['phase']==phase
contract=load(handoff/'dispatch-recovered.json')
for k,v in contract['programs_and_inputs'].items():assert sha(k)==v,k
assert sha(author)=='7a8c647fb59d73a6794f08b882716c3d26079e244e9fcbb01e7a19479eba152e'
parent=Path('/tmp/sumitomo-jiaozhou317');prior(parent/'native-closed.json',317);raw=load(parent/'raw-317-confirmed.json');assert raw['order']==317 and raw['sha256']==sha(raw['snapshot'])
if kind=='viewer':prior(parent/'viewer-closed.json',317);prior(w/'native-closed.json',318)
with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    physical=Path('/dev/shm/gong318-actual');physical.mkdir(exist_ok=True)
    attempt=Path(tempfile.mkdtemp(prefix=kind+'-',dir=physical));attempt_log=attempt/'run.log'
    env=dict(os.environ,TMPDIR=str(attempt),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',GORDON_NATIVE_EVENTS=str(attempt/'native-stages.ndjson'),LD_LIBRARY_PATH='/tmp/country-tools/oidn/lib:'+os.environ.get('LD_LIBRARY_PATH',''))
    new_assets=attempt/'assets';new_audit=attempt/'audit'
    if kind=='native':
        command=[sys.executable,'-Bu',source/'build_model.py','--out',new_assets,'--audit',new_audit,'--blender',here/'blender-one','--oidn',here/'oidn-one','--gltfpack','/tmp/country-tools/node_modules/.bin/gltfpack']
    else:
        helper=runpy.run_path(str(here/'signed-viewer-inputs.py'))['inputs']; snapshot=w/'raw-318-confirmed.json';inputs=helper(318,snapshot,ident,page,here/'signed-31318-viewer');write(here/'viewer-inputs.json',inputs)
        command=['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',here/'six-view-download.cjs',ident,attempt]
        env.update(MODEL_BASE_URL='http://127.0.0.1:31318/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
    before=datetime.now(timezone.utc).isoformat();family=runpy.run_path(str(here/'observed_family.py'))
    with attempt_log.open('xb') as log:
        child=subprocess.Popen(['taskset','-c',str(min(os.sched_getaffinity(0))),*command],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);observed=family['watch'](child);code=child.wait()
    remaining=[pid for pid,row in observed.items() if family['still_alive'](pid,row['birth'])];assert not remaining
    monitored=dict(order=318,host=253,kind=kind,exit=code,pid=child.pid,started=before,finished=datetime.now(timezone.utc).isoformat(),observed_descendants=observed,wrapper_closed=True,remaining=remaining,host_receipt_sha256=sha(closed),host_report_sha256=sha(report),dispatch_sha256=sha(handoff/'dispatch-recovered.json'),parent_snapshot_sha256=raw['sha256'],parent_receipt_sha256=sha(parent/'raw-317-confirmed.json'))
    write(attempt/'process.json',monitored);assert code==0,(code,attempt_log)
    if kind=='native':
        manifest=load(new_assets/'manifest.json');rows=manifest['assets'];assert set(rows)=={'raw','full','lod','native'} and manifest['photographic_texture_license']=='CC BY-SA 4.0'
        for role,r in rows.items():
            f=new_assets/r['file'];assert sha(f)==r['sha256'] and f.stat().st_size==r['bytes']
            if role!='native':assert r['sha256']==load(author)['assets'][role]['sha256']
        geometry=new_audit/'geometry-native.json'; reopened=load(geometry)['native_reopened_and_compared'];assert reopened['mesh_count']==load(author)['editable_groups']==189
        gate=reopened['gong_residence_gate']
        assert gate['plaque_triangles_with_checked_uv']==6 and gate['camera_count']>0 and gate['packed_image_sha256']
        events=[json.loads(line) for line in (attempt/'native-stages.ndjson').read_text().splitlines()];assert [e['stage'] for e in events]==['render','reopen','denoise'] and all(e['exit']==0 for e in events)
        for f in (*new_audit.iterdir(),*new_assets.iterdir()):copy(f,(audit if f.parent==new_audit else assets)/f.name)
        monitored.update(passed=True,assets=rows,manifest_sha256=sha(assets/'manifest.json'),geometry_native_sha256=sha(geometry),group_count=189,blender_pids=[e['pid'] for e in events[:2]],native_stages=events,remaining_blender=[],remaining_oidn=[])
    else:
        target=audit/'standalone-31318';q=load(attempt/'viewer.json');assert q['passed'] and len(q['views'])==6 and len(q['downloads'])==4
        for view in q['views']:
            f=attempt/view['filename'];assert sha(f)==view['sha256'];copy(f,target/f.name)
        rows=load(assets/'manifest.json')['assets']
        for role,download in q['downloads'].items():
            f=attempt/'saved'/rows[role]['file'];assert download['saveAsVerified'] and sha(f)==rows[role]['sha256']==download['sha256'] and f.stat().st_size==download['bytes']
        copy(attempt/'viewer.json',target/'viewer.json');chrome=[pid for pid,row in observed.items() if row['name'] in ('chromium','chrome','chrome-headless-shell','headless_shell')];assert chrome
        monitored.update(passed=True,views=6,downloads=4,node=child.pid,report=str(target/'viewer.json'),receipt_sha256=sha(target/'viewer.json'),chromium_pids=chrome,remaining_chromium=[])
    write(w/(kind+'-closed.json'),monitored)
