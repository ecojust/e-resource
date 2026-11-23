"""Reopen the published Mingfu meshes or visit their actual 31348 page after the corresponding city exit."""
from pathlib import Path
from datetime import datetime, timezone
import fcntl, hashlib, json, os, runpy, shutil, subprocess, sys, tempfile

here=Path(__file__).resolve().parent
host=Path('/tmp/shanghai-main-283')
work=Path('/tmp/mingfu348-study')
parent=Path('/tmp/shaoxing9-347')
project=Path('/workspace/e-resource/projects/shanghai')
model='huangpu-mingfu-library-science-society-relief-columns'
slug='mingfu-library-science-society-relief-columns'
assets=project/'assets/models/candidates'/model
audit=project/'data/audit'/(slug+'-v1')
source=project/'source/precise'/model/'source'
def sha(f):
    with Path(f).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(f):return json.loads(Path(f).read_bytes())
def put(f,row):
    temp=f.with_suffix('.pending')
    temp.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');temp.replace(f)
def publish(f,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.is_file():
        try:os.link(f,target)
        except OSError:shutil.copy2(f,target)
    assert sha(f)==sha(target)
def now():return datetime.now(timezone.utc).isoformat()
kind=sys.argv[1]
phase={'native':'before','viewer':'phone'}[kind]
ticket=Path(sys.argv[2]);assert ticket.samefile(host/'evidence'/phase/'closed.json')
event=read(ticket);r=read(event['report'])
assert event['order']==283 and event['phase']==phase and event['exit_code']==0 and event['exit']==0
assert event['node_closed'] and event['chromium_pids'] and event['remaining']==event['remaining_chromium']==[]
assert event['report_sha256']==sha(event['report']) and r['section']==phase and r['completed']
contract_path=work/'mapping/handoff/dispatch-live.json';contract=read(contract_path)
for f,sig in contract['programs_and_inputs'].items():assert sha(f)==sig,f
registrar=Path(r['source_code']) if r.get('source_code') else ticket.parent/'actual-driver.cjs'
if not registrar.is_file():
    registrar=host/'evidence/283'/('separate/phone' if phase=='phone'else'before')/'actual-driver.cjs'
assert sha(registrar)==event['driver_sha256']==r['scriptSha256']
assert event.get('source_code_sha256',event['driver_sha256'])==event['driver_sha256']
assert event['driver_sha256'] in contract['phase_drivers'][phase]
raw=read(parent/'raw-347-confirmed.json');assert raw['order']==347 and raw['sha256']==sha(raw['snapshot'])
for check in [parent/'native-closed.json']+([parent/'viewer-closed.json',work/'native-closed.json'] if kind=='viewer' else []):
    q=read(check);assert q['passed'] and q.get('exit',q.get('exit_code'))==0 and all(not v for k,v in q.items() if k.startswith('remaining'))
fixed=read(contract['fixed_source_register']);origin=Path(contract['fixed_source_register']).parent/'projects/shanghai'
ma=origin/'assets/models/candidates'/model; manifest=read(ma/'manifest.json');roles=manifest['assets'];proof=origin/'data/audit'/(slug+'-v1')/'development-native'
assert set(roles)=={'raw','full','lod','native'}
ref=read(audit/'preflight/model-review.json')
for role,item in roles.items():
    f=ma/item['file'];assert sha(f)==item['sha256'] and f.stat().st_size==item['bytes']
    if role!='native':assert ref['assets'][role]['sha256']==item['sha256']
family=runpy.run_path(str(here/'observed_family.py'))
with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lk:
    fcntl.flock(lk,fcntl.LOCK_EX)
    temp=Path(tempfile.mkdtemp(prefix=kind+'-',dir=work/'attempts'))
    result=dict(order=348,host=283,kind=kind,started=now(),host_receipt_sha256=sha(ticket),host_report_sha256=sha(event['report']),parent_snapshot_sha256=raw['sha256'],parent_receipt_sha256=sha(parent/'raw-347-confirmed.json'),dispatch_sha256=sha(contract_path))
    processes=[]
    def run(label,command,env):
        with (temp/(label+'.log')).open('xb') as stream:
            proc=subprocess.Popen(['taskset','-c',str(min(os.sched_getaffinity(0))),*map(str,command)],env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            observed=family['watch'](proc);code=proc.wait()
        remaining=[pid for pid,item in observed.items() if family['still_alive'](pid,item['birth'])]
        rec=dict(stage=label,pid=proc.pid,exit=code,wrapper_closed=True,remaining=remaining,children=observed,log_sha256=sha(temp/(label+'.log')))
        processes.append(rec);put(temp/'processes.json',processes)
        assert code==0 and not remaining,(label,temp)
    env=dict(os.environ,TMPDIR=str(temp),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    if kind=='native':
        blend=ma/roles['native']['file'];glb=ma/roles['raw']['file'];report=temp/'verified-editable.json'
        run('reopen-geometry',['blender','-b','--threads','1','--python-exit-code','1','--python',project/'tools/verify_editable_model.py','--',blend,glb,report],env)
        run('reopen-science-society-piers',['blender','-b',blend,'--threads','1','--python-exit-code','1','--python',source/'verify_reopened.py','--',blend,glb,report],env)
        measured=read(report);original=read(proof/'verified-editable.json')
        for k in ('match_raw','mesh_count','triangles','materials','surface_sha256_by_material','hall_piers'):assert measured[k]==original[k],k
        assert measured['mesh_count']==187 and measured['triangles']==100840 and measured['hall_piers']['uv_loops']==72
        for f in [ma/i['file'] for i in roles.values()]+[ma/'manifest.json']:publish(f,assets/f.name)
        publish(report,audit/'formal-reopened-348.json')
        g=proof/'geometry-native.json';publish(g,audit/'geometry-native.json')
        preview=read(g)['preview'];publish(proof/preview,audit/preview)
        result.update(assets=roles,files=list(roles.values()),blender_pids=[r['pid'] for r in processes],group_count=187,remaining_blender=[],remaining_oidn=[],geometry_native_sha256=sha(g),native_stages=processes,reopened_sha256=sha(report))
    else:
        actual=runpy.run_path(str(here/'signed-viewer-inputs.py'))['inputs'](348,work/'raw-348-confirmed.json',model,manifest['viewer_page'],here/'signed-31348-viewer')
        put(here/'viewer-inputs.json',actual);env.update(MODEL_BASE_URL='http://127.0.0.1:31348/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
        run('ordinary-viewer',[sys.executable,'-Bu',here/'run-348-devices.py',model,temp],env)
        viewer=read(temp/'viewer.json');assert viewer['passed'] and not viewer['pageErrors'] and len(viewer['views'])==6
        camera=work/'current-standalone-31348'
        for v in viewer['views']:
            f=temp/v['filename'];assert sha(f)==v['sha256'];publish(f,camera/f.name)
        for role,d in viewer['downloads'].items():
            f=temp/'saved'/roles[role]['file'];assert d['saveAsVerified'] and sha(f)==roles[role]['sha256']==d['sha256'] and f.stat().st_size==d['bytes']
        assert set(viewer['downloads'])==set(roles);publish(temp/'viewer.json',camera/'viewer.json')
        chrome=[int(i) for i,v in processes[0]['children'].items() if v['name'] in ('chromium','chrome','headless_shell','chrome-headless-shell')]
        assert chrome
        devices=[read(temp/(k+'-node-exit.json'))for k in ('desktop','mobile')]
        assert len({n['node']for n in devices})==2 and all(n['node_executable']=='node' and n['exit']==0 and str(n['node']) in {str(x) for x in processes[0]['children']} for n in devices)
        result.update(chromium_pids=chrome,node_pids=[v['node']for v in devices],independent_processes=devices,views=6,downloads=4,remaining_chromium=[],node=devices[0]['node'],report=str(camera/'viewer.json'),receipt_sha256=sha(camera/'viewer.json'),saved_files=str(temp/'saved'))
    result.update(all_processes_closed=True,attempt=temp.name,passed=True,exit=0,exit_code=0,finished=now(),wrapper_closed=True,remaining=[],observed=processes)
    put(work/(kind+'-closed.json'),result)
