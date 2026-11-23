"""Reopen precisely the bound Blender file twice during the physical 275 admission."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from receipts_recovered import ASSETS, AUDIT, HERE, ID, PROJECT, digest, frozen, prereqs, read, write

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def publish(source,destination,expected):
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():
        temp=destination.with_name('.'+destination.name+'.'+str(os.getpid())+'.new')
        try:
            try:os.link(source.resolve(),temp)
            except OSError:shutil.copyfile(source,temp)
            assert digest(temp)==expected
            try:os.link(temp,destination)
            except FileExistsError:pass
        finally:temp.unlink(missing_ok=True)
    assert digest(destination)==expected,destination

def execute(stage,args,attempt):
    start=now()
    path=attempt/(stage+'.log')
    with path.open('xb') as out:
        child=subprocess.Popen([str(a) for a in args],stdout=out,stderr=subprocess.STDOUT)
        code=child.wait()
    entry=dict(stage=stage,started=start,finished=now(),pid=child.pid,exit=code,
               log=str(path),log_sha256=digest(path),args=[str(a) for a in args])
    with (attempt/'native-stages.ndjson').open('a') as trace:
        trace.write(json.dumps(entry)+'\n')
    if code:raise subprocess.CalledProcessError(code,args)
    return entry

def main(attempt):
    assert attempt.parent==HERE and attempt.is_dir()
    grant=read(HERE/'native-window.json')
    assert prereqs('native',Path(grant['receipt']))==grant
    acceptance=frozen()['accepted_development']
    assert digest(acceptance['path'])==acceptance['sha256']
    binding=read(acceptance['path'])
    assert binding['id']==ID and binding['author_sha256']==grant['author_review_sha256']
    unavailable=frozen()['historical_inputs_unavailable']
    proof_path=Path(frozen()['recovery_evidence'])
    original_report=read(proof_path)
    assert original_report['original_dispatch_sha256']==digest(HERE/'dispatch-contract.json')
    assert original_report['editable_meshes']==329 and original_report['original_files_verified']==220
    now=read(frozen()['current_historical_input_check'])
    assert now['original_dispatch_sha256']==original_report['original_dispatch_sha256']
    for row in now['matched'].values():assert digest(row['source'])==row['sha256']
    for name,stamp in original_report['geometry_files'].items():
        public_file=Path('/dev/shm/340-historical-readbacks')/name
        if public_file.is_file():assert digest(public_file)==stamp
    for p,sha in binding['files'].items():
        if p in unavailable and not Path(p).is_file():
            assert unavailable[p]==sha,p
            continue
        assert digest(p)==sha,p
    mpath=Path(binding['manifest']);manifest=read(mpath)
    gpath=Path(binding['geometry']);geometry=read(gpath)
    folder=mpath.parent;source=PROJECT/'source/precise'/ID/'source'
    assets=manifest['assets']
    native=folder/assets['native']['file'];raw=folder/assets['raw']['file']
    report=attempt/'reopened.json'
    ver=PROJECT/'tools/verify_editable_model.py'
    cmd=['blender','-b','--threads','1','--python-exit-code','1']
    first=execute('reopen-geometry',[*cmd,'--python',ver,'--',native,raw,report],attempt)
    metrics=read(report)
    assert metrics['match_raw'] and metrics['mesh_count']==329
    second=execute('reopen-materials-cameras',['blender','-b',native,'--threads','1','--python-exit-code','1',
                    '--python',source/'verify_reopened.py','--',native,raw,report],attempt)
    formal=read(report);dev=geometry['native_reopened_and_compared']
    for key in ('match_raw','materials','triangles','surface_sha256_by_material','mesh_count','villa_roof_and_elevations'):
        assert formal[key]==dev[key],key
    items=[(folder/info['file'],ASSETS/info['file'],info['sha256']) for info in assets.values()]
    items.extend([(mpath,ASSETS/'manifest.json',digest(mpath)),(gpath,AUDIT/'geometry-native.json',digest(gpath)),
                  (folder/geometry['preview'],AUDIT/geometry['preview'],geometry['preview_sha256'])])
    for src,dst,signature in items:
        assert digest(src)==signature and (not dst.exists() or digest(dst)==signature),dst
    for src,dst,signature in items:publish(src,dst,signature)
    write(attempt/'reuse-proof.json',dict(order=340,host=275,passed=True,source_binding_sha256=acceptance['sha256'],
          source_manifest_sha256=digest(mpath),source_geometry_sha256=digest(gpath),development_finished=binding['development_end'],
          admitted_from=grant['sha256'],host_report_sha256=grant['report_sha256'],reopened=str(report),reopened_sha256=digest(report),
          stages=[first,second],geometry_native_sha256=digest(AUDIT/'geometry-native.json')))
if __name__=='__main__':main(Path(sys.argv[1]))
