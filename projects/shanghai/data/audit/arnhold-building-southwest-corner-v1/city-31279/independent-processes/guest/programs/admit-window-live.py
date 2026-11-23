"""Reopen the published Guangci meshes or visit their actual 31344 page after the corresponding city exit."""
from pathlib import Path
from datetime import datetime, timezone
import fcntl, hashlib, json, os, runpy, shutil, subprocess, sys, tempfile

here=Path(__file__).resolve().parent
host=Path('/tmp/shanghai-main-279')
work=Path('/tmp/guangci344')
parent=Path('/tmp/wanyi343')
project=Path('/workspace/e-resource/projects/shanghai')
model='huangpu-guangci-maternity-pavilion-twin-stair'
slug='guangci-maternity-pavilion-twin-stair'
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
assert event['order']==279 and event['phase']==phase and event['exit_code']==0 and event['exit']==0
assert event['node_closed'] and event['chromium_pids'] and event['remaining']==event['remaining_chromium']==[]
assert event['report_sha256']==sha(event['report']) and r['section']==phase and r['completed']
contract_path=work/'mapping/handoff/dispatch-live.json';contract=read(contract_path)
for f,sig in contract['programs_and_inputs'].items():assert sha(f)==sig,f
assert sha(Path(event['report']).parent/'actual-driver.cjs')==event['driver_sha256']==r['scriptSha256']==contract['host_driver_sha256'][phase]
assert len(contract['previous_parent'])==5
for filename,digest in contract['previous_parent'].items():assert sha(filename)==digest,filename
raw=read(parent/'raw-343-confirmed.json');assert raw['order']==343 and raw['sha256']==sha(raw['snapshot'])
for check in [parent/'native-closed.json']+([parent/'viewer-closed.json',work/'native-closed.json'] if kind=='viewer' else []):
    q=read(check);assert q['passed'] and q.get('exit',q.get('exit_code'))==0 and all(not v for k,v in q.items() if k.startswith('remaining'))
fixed=read(contract['fixed_source_register']);origin=Path(fixed['project_root'])
ma=origin/'assets/models/candidates'/model; manifest=read(ma/'manifest.json');roles=manifest['assets'];proof=origin/'data/audit'/(slug+'-v1')/'development-native'
assert set(roles)=={'raw','full','lod','native'}
ref=read(audit/'preflight/model-review.json')
for role,item in roles.items():
    f=ma/item['file'];assert sha(f)==item['sha256'] and f.stat().st_size==item['bytes']
    if role!='native':assert ref['assets'][role]['sha256']==item['sha256']
family=runpy.run_path(str(here/'observed_family.py'))
with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lk:
    fcntl.flock(lk,fcntl.LOCK_EX)
    temp=Path(tempfile.mkdtemp(prefix='guangci344-'+kind+'-',dir='/dev/shm'))
    result=dict(order=344,host=279,kind=kind,started=now(),host_receipt_sha256=sha(ticket),host_report_sha256=sha(event['report']),parent_snapshot_sha256=raw['sha256'],parent_receipt_sha256=sha(parent/'raw-343-confirmed.json'),dispatch_sha256=sha(contract_path))
    tmp=temp/'t';tmp.mkdir()
    envdirs={name:temp/key for name,key in [('XDG_CONFIG_HOME','cf'),('XDG_RUNTIME_DIR','rt'),('XDG_CACHE_HOME','ca')]}
    for path in envdirs.values():path.mkdir(mode=0o700)
    processes=[]
    def run(label,command,env):
        with (temp/(label+'.log')).open('xb') as stream:
            proc=subprocess.Popen(['taskset','-c',str(min(os.sched_getaffinity(0))),*map(str,command)],env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            observed=family['watch'](proc);code=proc.wait()
        remaining=[pid for pid,item in observed.items() if family['still_alive'](pid,item['birth'])]
        rec=dict(stage=label,pid=proc.pid,exit=code,wrapper_closed=True,remaining=remaining,children=observed,log_sha256=sha(temp/(label+'.log')))
        processes.append(rec);put(temp/'processes.json',processes)
        assert code==0 and not remaining,(label,temp)
    env=dict(os.environ,TMPDIR=str(tmp),**{k:str(v) for k,v in envdirs.items()},PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    if kind=='native':
        blend=ma/roles['native']['file'];glb=ma/roles['raw']['file'];report=temp/'verified-editable.json'
        run('reopen-geometry',['blender','-b','--threads','1','--python-exit-code','1','--python',project/'tools/verify_editable_model.py','--',blend,glb,report],env)
        run('reopen-courtyard',['blender','-b',blend,'--threads','1','--python-exit-code','1','--python',source/'verify_reopened.py','--',blend,glb,report],env)
        measured=read(report);original=read(proof/'verified-editable.json')
        for k in ('match_raw','mesh_count','triangles','materials','surface_sha256_by_material','courtyard_section'):assert measured[k]==original[k],k
        assert measured['mesh_count']==400 and measured['triangles']==92962 and measured['courtyard_section']['uv_loops']==1896
        for f in [ma/i['file'] for i in roles.values()]+[ma/'manifest.json']:publish(f,assets/f.name)
        publish(report,audit/'formal-reopened-344.json')
        g=proof/'geometry-native.json';publish(g,audit/'geometry-native.json')
        preview=read(g)['preview'];publish(proof/preview,audit/preview)
        result.update(assets=roles,files=list(roles.values()),blender_pids=[r['pid'] for r in processes],group_count=400,remaining_blender=[],remaining_oidn=[],geometry_native_sha256=sha(g),native_stages=processes,reopened_sha256=sha(report))
    else:
        actual=runpy.run_path(str(here/'signed-viewer-inputs.py'))['inputs'](344,work/'raw-344-confirmed.json',model,manifest['viewer_page'],here/'signed-31344-viewer')
        frozen=here/'signed-31344-viewer'
        put(frozen/'three-http-inputs.json',actual)
        from urllib.request import urlopen
        css_name='src/dacheng-hall.css'
        css_sha='3c1c69c786687e13d4703aa44a85ecf1c7cec4808468168f39f6b9f615c51c2e'
        for port in (31343,31344):
            with urlopen(f'http://127.0.0.1:{port}/{css_name}',timeout=40) as response:
                style=response.read()
                assert response.status==200 and response.headers.get_content_type()=='text/css' and hashlib.sha256(style).hexdigest()==css_sha
        (frozen/css_name).write_bytes(style)
        put(here/'viewer-inputs.json',actual);env.update(MODEL_FROZEN_ROOT=str(frozen),MODEL_BASE_URL='http://127.0.0.1:31344/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
        run('ordinary-viewer',[sys.executable,here/'run-344-devices.py',model,temp],env)
        viewer=read(temp/'viewer.json');assert viewer['passed'] and not viewer['pageErrors'] and len(viewer['views'])==6
        camera=audit/'standalone-31344'
        for v in viewer['views']:
            f=temp/v['filename'];assert sha(f)==v['sha256'];publish(f,camera/f.name)
        for role,d in viewer['downloads'].items():
            f=temp/'saved'/roles[role]['file'];assert d['saveAsVerified'] and sha(f)==roles[role]['sha256']==d['sha256'] and f.stat().st_size==d['bytes']
        assert set(viewer['downloads'])==set(roles);publish(temp/'viewer.json',camera/'viewer.json')
        chrome=[int(i) for i,v in processes[0]['children'].items() if v['name'] in ('chromium','chrome','headless_shell','chrome-headless-shell')]
        assert chrome
        dev=[read(temp/(d+'-node-exit.json')) for d in ('desktop','mobile')]
        assert len({r['node'] for r in dev})==2 and all(r['exit']==0 for r in dev)
        for run in dev:assert processes[0]['children'][run['node']]['name']=='node'
        result.update(device_nodes=dev,actual_directory=str(temp))
        result.update(chromium_pids=chrome,views=6,downloads=4,remaining_chromium=[],node=processes[0]['pid'],report=str(camera/'viewer.json'),receipt_sha256=sha(camera/'viewer.json'),saved_files=str(temp/'saved'))
    result.update(passed=True,exit=0,exit_code=0,finished=now(),wrapper_closed=True,remaining=[],observed=processes)
    put(work/(kind+'-closed.json'),result)
