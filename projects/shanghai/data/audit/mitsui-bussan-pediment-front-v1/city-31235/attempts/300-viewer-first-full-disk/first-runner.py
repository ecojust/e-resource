"""Run the admitted tower production or viewer, retaining evidence from any failed attempt."""
from pathlib import Path
import datetime
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from receipts import (ASSETS,AUDIT,HERE,ID,PROJECT,WORK,digest,prereqs,read,write)

kind=sys.argv[1]
assert kind in ('native','viewer')
grant=read(Path('/tmp/xiaonanmen300/mapping/handoff/235-supplement-actual-inputs.json'));assert digest(Path('/tmp/xiaonanmen300/mapping/handoff/235-supplement-actual-inputs.json'))=='ad49b4455c0ffbe447a44dafc22c5ecd64ad9d3931d83a0aafa2dde891ed8ae0'
assert digest(Path(grant['receipt']))==grant['sha256'] and digest(Path('/tmp/shanghai-main-235/formal-31235/actual-31235-standalone/20261122T054115142256Z/viewer.json'))==grant['report_sha256']
source=PROJECT/'source/precise'/ID/'source'
manifest=Path(read(HERE/'dispatch-contract.json')['accepted_manifest'])
ref=read(manifest)['assets']
begin=datetime.datetime.now(datetime.timezone.utc).isoformat()
stamp=begin.replace(':','').replace('+','-')
attempt=HERE/(kind+'-attempt-'+stamp)
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

with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as physical:
    fcntl.flock(physical,fcntl.LOCK_EX)
    for f in Path('/proc').glob('[0-9]*/comm'):
        try:active=f.read_text().strip() in {'blender','chromium','chrome'} and live(f.parent.name)
        except OSError:continue
        assert not active,f
    areas=[Path('/tmp'),Path('/run/codex-docker/user'),Path('/dev/shm')]
    free=lambda p:shutil.disk_usage(p).free
    # The two temp roots hold the three canonical exports/Blender file and
    # the transient editable JSON respectively. Output on the root disk
    # must still accommodate all four assets if the primary is elsewhere.
    available=sorted(areas,key=free,reverse=True)
    area=available[0]
    secondary=available[1]
    if area!=Path('/tmp') and secondary==Path('/tmp') and free(available[2])>=22*1024**2:
        secondary=available[2]
    with tempfile.TemporaryDirectory(dir=area,prefix='xiaonanmen300-'+kind+'-') as scratch,log.open('xb') as stream:
        env={**os.environ,'TMPDIR':scratch,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
             'PYTHONDONTWRITEBYTECODE':'1','LD_LIBRARY_PATH':'/tmp/country-tools/oidn/lib:'+os.environ.get('LD_LIBRARY_PATH','')}
        if kind=='native':
            affinity=['taskset','-c',str(min(os.sched_getaffinity(0)))]
            env['XIAONANMEN_SECONDARY']=str(secondary/'xiaonanmen300-parts')
            cmd=[*affinity,sys.executable,'-Bu',HERE/'split-scratch.py','--out',ASSETS,'--audit',AUDIT,
                 '--blender',HERE/'blender-one','--gltfpack','/tmp/country-tools/node_modules/.bin/gltfpack',
                 '--oidn','/tmp/american-school127/oidn-single.py']
        else:
            subprocess.run([sys.executable,'-B',HERE/'signed-viewer-inputs.py'],env=env,check=True,stdout=stream,stderr=stream)
            env.update(MODEL_BASE_URL='http://127.0.0.1:31300/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
            cmd=['node','-r',PROJECT/'data/audit/brunner-mond-v1/viewer-timeout.cjs',HERE/'six-view-download.cjs',ID,attempt]
        child=subprocess.Popen(cmd,env=env,start_new_session=True,stdout=stream,stderr=subprocess.STDOUT)
        children,remaining,starts=observed(child)
    common={'order':300,'exit':child.returncode,'exit_code':child.returncode,'remaining':remaining,
            'wrapper_pid':child.pid,'wrapper_closed':not live(child.pid),'observed_processes':children,'observed_process_births':starts,
            'started':begin,'finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log_sha256':digest(log),
            'admitted_from':grant['sha256'],'parent_snapshot_sha256':grant['parent_snapshot_sha256']}
    write(attempt/'process-exit.json',common)
    assert child.returncode==0 and common['wrapper_closed'] and not remaining
    done=read(ASSETS/'manifest.json')
    assert done['geometry_license']=='MIT' and done['photos_embedded'] is False
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
        proof=reopened['tower_reopened']
        assert proof['raw_sha256']==done['assets']['raw']['sha256'] and len(proof['orthographic_cameras'])==6
        assert proof['group_material_faces_sha256']==read(WORK/'native-viewer-preflight.json')['material_face_schedule_sha256']
        assert proof['packed_png_sha256']==digest(source/'weathered-concrete.png')
        assert reopened['mesh_count']==read(WORK/'native-viewer-preflight.json')['editable_groups']
        assert proof['uv_loops']>100 and all(x['maximum_error']<.000003 for x in proof['texture_coordinates'])
        assert receipt['preview_sha256']==digest(AUDIT/receipt['preview'])
        result={**common,'passed':True,'all_processes_closed':True,'blender_pids':seen,'remaining_blender':[],'remaining_oidn':[],
                'geometry_native_sha256':digest(AUDIT/'geometry-native.json'),'manifest':str(ASSETS/'manifest.json'),'manifest_sha256':digest(ASSETS/'manifest.json'),
                'group_count':reopened['mesh_count'],'assets':done['assets'],'files':list(done['assets'].values())}
    else:
        seen=[pid for pid,s in children.items() if s in ('chromium','chrome')]
        assert seen
        report=read(attempt/'viewer.json')
        assert report['base']==env['MODEL_BASE_URL'] and report['passed'] and not report['pageErrors']
        assert report['scriptSHA256']==digest(HERE/'six-view-download.cjs') and report['manifestSHA256']==digest(ASSETS/'manifest.json')
        assert len(report['views'])==6 and len(report['downloads'])==4
        assert {v['viewport']['width']for v in report['views']}=={1250,390}
        archive=AUDIT/'standalone-31300';archive.mkdir(exist_ok=True)
        evidence=read(HERE/'viewer-inputs.json')
        assert evidence['order']==300 and report['rawSnapshotSHA256']==grant['own_snapshot_sha256']==evidence['raw_snapshot_sha256']
        assert report['productionSHA256']==grant['highest_stage']==evidence['production_sha256']
        assert all(evidence['inputs'][k]==v for k,v in report['files'].items())
        assert report['manifestSHA256']==evidence['inputs'][f'assets/models/candidates/{ID}/manifest.json']
        assert set(report['downloads'])=={'raw','full','lod','native'} and all(item['saveAsVerified'] for item in report['downloads'].values())
        publish(HERE/'viewer-inputs.json',archive/'signed-inputs.json')
        for v in report['views']:
            pixels=v['rgba'];assert pixels['width']*pixels['height']==pixels['opaque'] and pixels['foreground_pixels']>100 and pixels['quantized_colors']>=8
            f=attempt/v['filename'];assert digest(f)==v['sha256']
            publish(f,archive/f.name);publish(f,AUDIT/f.name)
        for role,v in report['downloads'].items():assert all(v[k]==done['assets'][role][k]for k in ('file','bytes','sha256'))
        publish(attempt/'viewer.json',archive/'viewer.json')
        publish(attempt/'viewer.json',AUDIT/'viewer.json')
        result={**common,'passed':True,'all_processes_closed':True,'node':child.pid,'chromium_pids':seen,'remaining_chromium':[],
                'processes':{'node':{'pids':[child.pid],'closed':True},'chromium':{'pids':seen,'closed':True}},
                'files':report['downloads'],'views':6,'downloads':4,'receipt_sha256':digest(archive/'viewer.json'),
                'report_sha256':digest(archive/'viewer.json'),'report':str(archive/'viewer.json'),'server':report['base']}
    write(WORK/(kind+'-closed.json'),result)
