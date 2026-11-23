"""Run the admitted entrance production or viewer, retaining evidence from any failed attempt."""
from pathlib import Path
from contextlib import ExitStack
import datetime
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from receipts_recovered import (ASSETS,AUDIT,HERE,ID,PROJECT,WORK,completed_viewer,digest,native,prereqs,read,write)

kind=sys.argv[1]
assert kind in ('native','viewer')
grant=read(HERE/(kind+'-window.json'))
assert prereqs(kind,Path(grant['receipt']))==grant
source=PROJECT/'source/precise'/ID/'source'
manifest=Path(read(HERE/'dispatch-recovered.json')['accepted_manifest'])
ref=read(manifest)['assets']
begin=datetime.datetime.now(datetime.timezone.utc).isoformat()
stamp=begin.replace(':','').replace('+','-')
attempt=Path('/run/codex-docker/user/field340/active')/(kind+'-attempt-'+stamp)
attempt.mkdir()
log=attempt/'run.log'
def live(pid):
    try:return (Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[0] not in ('Z','X')
    except FileNotFoundError:return False

def observed(p):
    import psutil
    known={}
    names={}
    while p.poll() is None:
        try:
            root=psutil.Process(p.pid)
            for child in root.children(recursive=True):
                try:
                    birth=child.create_time()
                    names[child.pid]=child.name()
                    known[child.pid]=birth
                except psutil.Error:
                    pass
        except psutil.Error:
            pass
        time.sleep(.10)
    def still_running(pid,birth):
        try:
            child=psutil.Process(pid)
            return child.create_time()==birth and child.status()!=psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False
    for _ in range(40):
        if not any(still_running(pid,birth) for pid,birth in known.items()):
            break
        time.sleep(.10)
    return names,[pid for pid,birth in known.items() if still_running(pid,birth)],known


def publish(path,target):
    if not target.is_file():
        try:os.link(path,target)
        except OSError:shutil.copyfile(path,target)
    assert digest(path)==digest(target)

with ExitStack() as locks:
    for name in (['/tmp/shanghai-standalone-viewer.lock','/tmp/yangshupu-historical-render.lock'] if kind=='native' else ['/tmp/shanghai-standalone-viewer.lock']):
        lock=locks.enter_context(Path(name).open('a'));fcntl.flock(lock,fcntl.LOCK_EX)
    for f in Path('/proc').glob('[0-9]*/comm'):
        try:active=f.read_text().strip() in {'blender','chromium','chrome'} and live(f.parent.name)
        except OSError:continue
        assert not active,f
    areas=[Path(name) for name in ('/tmp','/dev/shm','/dev/net') if Path(name).is_dir() and os.access(name,os.W_OK)]
    area=max(areas,key=lambda p:shutil.disk_usage(p).free)
    with tempfile.TemporaryDirectory(dir=area,prefix='liuyazi340-'+kind+'-') as scratch,log.open('xb') as stream:
        env={**os.environ,'TMPDIR':scratch,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
             'PYTHONDONTWRITEBYTECODE':'1','LD_LIBRARY_PATH':'/tmp/country-tools/oidn/lib:'+os.environ.get('LD_LIBRARY_PATH','')}
        if kind=='native':
            env['SINAN_BOOKS_NATIVE_EVENTS']=str(attempt/'native-stages.ndjson')
            affinity=['taskset','-c',str(min(os.sched_getaffinity(0)))]
            cmd=[*affinity,sys.executable,'-Bu',HERE/'split-scratch.py','--out',ASSETS,'--audit',AUDIT,
                 '--blender',HERE/'blender-one','--gltfpack','/workspace/.e-resource-recovery/toolchain/node_modules/gltfpack/cli.js',
                 '--oidn',HERE/'oidn-one']
            if read(HERE/'dispatch-recovered.json').get('accepted_development'):
                cmd=[*affinity,sys.executable,'-Bu',HERE/'reopen-development-recovered.py',str(attempt)]
        else:
            subprocess.run([sys.executable,'-B',HERE/'signed-viewer-inputs.py'],check=True)
            env.update(MODEL_BASE_URL='http://127.0.0.1:31340/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
            cmd=[sys.executable,'-Bu',HERE/'run-340-devices.py',ID,attempt]
        child=subprocess.Popen(cmd,env=env,start_new_session=True,stdout=stream,stderr=subprocess.STDOUT)
        children,remaining,starts=observed(child)
    common={'order':340,'exit':child.returncode,'exit_code':child.returncode,'remaining':remaining,
            'wrapper_pid':child.pid,'wrapper_closed':not live(child.pid),'observed_processes':children,'observed_process_births':starts,
            'started':begin,'finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log_sha256':digest(log),
            'admitted_from':grant['sha256'],'host_receipt_sha256':grant['sha256'],'host_report_sha256':grant['report_sha256'],'author_review_sha256':grant['author_review_sha256'],'physical_map_order':275,'parent_snapshot_sha256':grant['parent_snapshot_sha256']}
    write(attempt/'process-exit.json',common)
    assert child.returncode==0 and common['wrapper_closed'] and not remaining
    done=read(ASSETS/'manifest.json')
    assert done['photos_embedded'] is False
    assert done['third_party_models_embedded'] is False
    assert done['id']==ID and set(done['assets'])=={'raw','full','lod','native'}
    for role,item in done['assets'].items():
        f=ASSETS/item['file'];assert f.stat().st_size==item['bytes'] and digest(f)==item['sha256']
        if role!='native':assert item['sha256']==ref[role]['sha256']
    if kind=='native':
        seen=[pid for pid,s in children.items() if s.startswith('blender')]
        assert len(seen)>=2
        receipt=read(AUDIT/'geometry-native.json')
        reopened=receipt['native_reopened_and_compared']
        assert receipt['meshopt_decoded_oriented_surfaces_match'] and reopened['match_raw']
        proof=reopened['villa_roof_and_elevations']
        accepted_groups=read(WORK/'checked/raw.geometry.json')
        import runpy
        group_count=len(runpy.run_path(str(HERE/'editable-groups.py'))['verify_groups'](WORK/'checked'))
        assert reopened['mesh_count']==group_count==proof['groups']==329
        assert proof['cameras']==read(source/'cameras.json') and len(proof['cameras'])==9
        assert proof['texture_sha256']==digest(source/'pebble-dash.png') and proof['uv_loops']>0 and proof['max_uv_error']<.00001
        for role in ('raw','full','lod'):
            assert done['assets'][role]['triangles']==ref[role]['triangles']
        events=[json.loads(s) for s in (attempt/'native-stages.ndjson').read_text().splitlines()]
        expected_events=(['reopen-geometry','reopen-materials-cameras'] if read(HERE/'dispatch-recovered.json').get('accepted_development') else ['render','reopen','denoise'])
        assert [r['stage'] for r in events]==expected_events and all(r['exit']==0 for r in events)
        assert all(r['pid'] in children for r in events[:2])
        if 'preview' in receipt:assert receipt['preview_sha256']==digest(AUDIT/receipt['preview'])
        result={**common,'passed':True,'all_processes_closed':True,'blender_pids':seen,'remaining_blender':[],'remaining_oidn':[],
                'geometry_native_sha256':digest(AUDIT/'geometry-native.json'),'manifest':str(ASSETS/'manifest.json'),'manifest_sha256':digest(ASSETS/'manifest.json'),
                'native_stages':events,'camera_count':len(proof['cameras']),'texture_sha256':proof['texture_sha256'],'uv_loops':proof['uv_loops'],'development_source':receipt.get('development_source'),'group_count':reopened['mesh_count'],'assets':done['assets'],'files':list(done['assets'].values())}
        if read(HERE/'dispatch-recovered.json').get('accepted_development'):
            proof_path=attempt/'reuse-proof.json'
            formal=read(proof_path)
            assert formal['passed'] and digest(formal['reopened'])==formal['reopened_sha256']
            assert formal['stages']==events and formal['admitted_from']==grant['sha256']
            result['development_source']=formal
            result['host_reopening_sha256']=formal['reopened_sha256']
            result['reuse_proof_sha256']=digest(proof_path)
    else:
        seen=[pid for pid,s in children.items() if s in ('chromium','chrome')]
        assert seen
        report=read(attempt/'viewer.json')
        assert report['base']==env['MODEL_BASE_URL'] and report['passed'] and not report['pageErrors']
        assert report['scriptSHA256']==digest(HERE/'six-view-download-recovered.cjs') and report['manifestSHA256']==digest(ASSETS/'manifest.json')
        assert report['productionSHA256']==grant['highest_stage'] and report['rawSnapshotSHA256']==grant['own_snapshot_sha256']
        assert all(item['savedAs']==item['file'] for item in report['downloads'].values())
        assert len(report['views'])==6 and len(report['downloads'])==4
        assert {v['viewport']['width']for v in report['views']}=={770,390}
        for device_name in ('desktop','mobile'):
            node=read(attempt/(device_name+'-node-exit.json'));assert node['exit']==0 and digest(attempt/(device_name+'-viewer.json'))==node['report_sha256']
        archive=AUDIT/'standalone-31340';archive.mkdir(exist_ok=True)
        for v in report['views']:
            pixels=v['rgba'];assert pixels['width']*pixels['height']==pixels['opaque'] and pixels['foreground_pixels']>100 and pixels['quantized_colors']>=8
            f=attempt/v['filename'];assert digest(f)==v['sha256']
            publish(f,archive/f.name);publish(f,AUDIT/f.name)
        for role,v in report['downloads'].items():assert all(v[k]==done['assets'][role][k]for k in ('file','bytes','sha256'))
        publish(attempt/'viewer.json',archive/'viewer.json')
        publish(attempt/'viewer.json',AUDIT/'viewer.json')
        result={**common,'passed':True,'all_processes_closed':True,'node':read(attempt/'desktop-node-exit.json')['node'],'node_pids':[read(attempt/(v+'-node-exit.json'))['node'] for v in ('desktop','mobile')],'chromium_pids':seen,'remaining_chromium':[],
                'processes':{'node':{'pids':[read(attempt/(v+'-node-exit.json'))['node'] for v in ('desktop','mobile')],'closed':True},'chromium':{'pids':seen,'closed':True}},
                'files':report['downloads'],'views':6,'downloads':4,'receipt_sha256':digest(archive/'viewer.json'),
                'report_sha256':digest(archive/'viewer.json'),'report':str(archive/'viewer.json'),'server':report['base']}
    candidate=HERE/(kind+'-completed-'+grant['sha256']+'.json')
    write(candidate,result)
    (native if kind=='native' else completed_viewer)(candidate,340)
