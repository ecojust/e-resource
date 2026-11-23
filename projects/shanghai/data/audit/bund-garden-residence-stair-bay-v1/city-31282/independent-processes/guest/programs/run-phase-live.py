"""Run the admitted Shaoxing Road photographed arched entrance production or viewer, retaining evidence from any failed attempt."""
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

from receipts_live import (ASSETS,AUDIT,HERE,ID,PROJECT,WORK,digest,frozen,read,write)

kind=sys.argv[1]
assert kind in ('native','viewer')
grant=read(HERE/(kind+'-window.json'))
frozen()
assert grant['authorized'] and grant['order']==347 and grant['host']==282 and grant['kind']==kind
assert digest(Path(grant['receipt']))==grant['sha256']
from receipts_live import raw,native
parent=raw(Path('/tmp/jingu-shaoxing346/raw-346-confirmed.json'),346)
assert parent['sha256']==grant['parent_snapshot_sha256']
native(Path('/tmp/jingu-shaoxing346/native-closed.json'),346)
source=PROJECT/'source/precise'/ID/'source'
manifest=Path('/tmp/shaoxing9-347/mesh/manifest.json')
ref=read(manifest)['assets']
begin=datetime.datetime.now(datetime.timezone.utc).isoformat()
stamp=begin.replace(':','').replace('+','-')
attempt=HERE/(kind+'-attempt-'+stamp)
physical=Path('/run/lock/j347/work/attempts')/attempt.name;physical.mkdir();attempt.symlink_to(physical,target_is_directory=True)
log=attempt/'run.log'
def live(pid):
    try:return (Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[0] not in ('Z','X')
    except FileNotFoundError:return False

def observed(p):
    children={}
    while p.poll() is None:
        parents={}
        for f in Path('/proc').glob('[0-9]*/stat'):
            try:
                values=f.read_text().rsplit(')',1)[1].split()
                if values[0] not in ('Z','X'):
                    parents[int(f.parent.name)]=(int(values[1]),(f.parent/'comm').read_text().strip())
            except OSError:
                continue
        family=set(children)|{p.pid}
        while True:
            additions={pid for pid,(parent,name) in parents.items() if parent in family and pid not in family}
            if not additions:break
            family.update(additions)
            children.update({pid:parents[pid][1] for pid in additions})
        time.sleep(.20)
    for _ in range(30):
        if not any(live(pid)for pid in children):break
        time.sleep(.1)
    return children

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
    areas=[Path('/run/lock/j347/work/t')]
    free=lambda p:shutil.disk_usage(p).free
    area=areas[0]
    with tempfile.TemporaryDirectory(dir=area,prefix='shaoxing9-347-'+kind+'-') as scratch,log.open('xb') as stream:
        env={**os.environ,'TMPDIR':scratch,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
             'PYTHONDONTWRITEBYTECODE':'1','LD_LIBRARY_PATH':'/tmp/country-tools/oidn/lib:'+os.environ.get('LD_LIBRARY_PATH','')}
        if kind=='native':
            env['SHAOXING_ENTRANCE_NATIVE_EVENTS']=str(attempt/'native-stages.ndjson')
            affinity=['taskset','-c',str(min(os.sched_getaffinity(0)))]
            cmd=[*affinity,sys.executable,'-Bu',HERE/'anonymous-intermediates.py',source/'build_model.py','--out',ASSETS,'--audit',AUDIT,
                 '--blender',HERE/'blender-one','--gltfpack','/workspace/.e-resource-recovery/toolchain/node_modules/gltfpack/cli.js',
                 '--oidn',HERE/'oidn-one']
        else:
            from signed_page_live import fetch_page
            official=attempt/'ordinary-page';page_binding=fetch_page(347,ID,official)
            env['MODEL_FROZEN_ROOT']=str(official)
            env.update(MODEL_BASE_URL='http://127.0.0.1:31347/',NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
            cmd=[sys.executable,'-Bu',HERE/'run-347-devices.py',ID,attempt]
        env['TMPDIR']=str(Path('/run/lock/j347/m/t')/Path(scratch).name)
        cmd=['nsenter','--target',Path('/run/lock/j347/pid').read_text().strip(),'--user','--mount','--preserve-credentials',*cmd]
        child=subprocess.Popen(cmd,env=env,start_new_session=True,stdout=stream,stderr=subprocess.STDOUT)
        children=observed(child)
    remaining=[k for k in children if live(k)]
    common={'order':347,'exit':child.returncode,'exit_code':child.returncode,'remaining':remaining,
            'wrapper_pid':child.pid,'wrapper_closed':not live(child.pid),'observed_processes':children,
            'started':begin,'finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log_sha256':digest(log),
            'admitted_from':grant['sha256'],'parent_snapshot_sha256':grant['parent_snapshot_sha256']}
    write(attempt/'process-exit.json',common)
    assert child.returncode==0 and common['wrapper_closed'] and not remaining
    done=read(ASSETS/'manifest.json')
    assert done['copyright']==read(manifest)['copyright']
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
        assert reopened['mesh_count']==read(WORK/'author-counts.json')['editable_groups'],reopened
        subprocess.run([sys.executable,'-B',AUDIT/'check-delivered-surfaces.py','--manifest',ASSETS/'manifest.json'],check=True)
        rays=read(AUDIT/'surface-checks.json')
        assert rays['passed'] and rays['total_checks']==read(AUDIT/'preflight-surface-checks.json')['total_checks']
        assert receipt['preview_sha256']==digest(AUDIT/receipt['preview'])
        native_stages=[json.loads(line)for line in (attempt/'native-stages.ndjson').read_text().splitlines()]
        assert [item['stage']for item in native_stages]==['render','reopen','denoise'] and all(item['exit']==0 and not live(item['pid']) for item in native_stages)
        result={**common,'passed':True,'native_stages':native_stages,'manifest':str(ASSETS/'manifest.json'),'geometry_native':str(AUDIT/'geometry-native.json'),'blender_pids':seen,'remaining_blender':[],'remaining_oidn':[],
                'geometry_native_sha256':digest(AUDIT/'geometry-native.json'),'manifest_sha256':digest(ASSETS/'manifest.json'),
                'group_count':reopened['mesh_count'],'assets':done['assets'],'files':list(done['assets'].values())}
    else:
        seen=[pid for pid,s in children.items() if s in ('chromium','chrome')]
        assert seen
        report=read(attempt/'viewer.json')
        assert report['base']==env['MODEL_BASE_URL'] and report['passed'] and not report['pageErrors']
        assert report['actual_inputs_sha256']==digest(attempt/'ordinary-page/three-http-inputs.json')
        assert all(item.get('savedAs')==item['file'] for item in report['downloads'].values())
        assert report['scriptSHA256']==digest(HERE/'six-view-live.cjs') and report['manifestSHA256']==digest(ASSETS/'manifest.json')
        assert len(report['views'])==6 and len(report['downloads'])==4
        assert {v['viewport']['width']for v in report['views']}=={1250,390}
        archive=AUDIT/'standalone-31347';archive.mkdir(exist_ok=True)
        for v in report['views']:
            f=attempt/v['filename'];assert digest(f)==v['sha256']
            publish(f,archive/f.name);publish(f,AUDIT/f.name)
        for role,v in report['downloads'].items():assert all(v[k]==done['assets'][role][k]for k in ('file','bytes','sha256'))
        publish(attempt/'viewer.json',archive/'viewer.json')
        publish(attempt/'viewer.json',AUDIT/'viewer.json')
        devices=[read(attempt/(d+'-node-exit.json')) for d in ('desktop','mobile')]
        assert len(set(x['node']for x in devices))==2 and all(x['exit']==0 and x['node_executable']=='node' and x['node'] in children for x in devices)
        for item in report['downloads'].values():
            actual=attempt/'saved'/item['file'];assert item['saveAsVerified'] and actual.stat().st_size==item['bytes'] and digest(actual)==item['sha256']
        result={**common,'passed':True,'node':devices[0]['node'],'node_pids':[x['node']for x in devices],'independent_processes':devices,'chromium_pids':seen,'remaining_chromium':[],
                'views':6,'downloads':4,'receipt_sha256':digest(archive/'viewer.json'),'viewer_sha256':digest(archive/'viewer.json'),'report_sha256':digest(archive/'viewer.json'),'report':str(archive/'viewer.json'),'server':report['base']}
    result['host_receipt_sha256']=grant['sha256']
    result['host_report_sha256']=grant['report_sha256']
    result['all_processes_closed']=True
    if kind=='native':
        result['assets']={role:{**rec,'path':str(ASSETS/rec['file'])} for role,rec in done['assets'].items()}
    write(WORK/(kind+'-closed.json'),result)
