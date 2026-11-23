"""Build the editable apartment block from its grouped source, then reopen and compare it to the published GLB."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from build_model import Builder, PALETTE, META, ID, PROJECT, SOURCE, add_building
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import group_parts
sys.path.insert(0,str(SOURCE))
from build_blender_source import editable_groups,source_materials,raw_document

def digest(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def write(p,j):
    tmp=p.with_name(p.name+'.partial')
    tmp.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(p)

def prepare(pack,out,manifest,raw):
    b=Builder(dict(PALETTE))
    add_building(b,False)
    bodies=group_parts(b); counts=editable_groups(bodies.keys())
    tri=sum(len(v['f'])for v in bodies.values())
    assert tri==manifest['assets']['raw']['triangles']
    generated=out/'regenerated.glb'; b.save(generated,META)
    assert digest(generated)==digest(raw)
    views=raw_document(raw)['extras']['camera_views']
    assert views==json.loads((SOURCE/'cameras.json').read_bytes()) and views
    write(out/'editable-parts.json',dict(groups=bodies,palette=b.palette,metadata={**META,'scope':'白赛仲公寓两侧街翼、转角阳台、水磨石双跑楼梯与屋顶'}))
    record=dict(groups=counts,triangles=tri,raw_sha256=digest(raw),parts_sha256=digest(out/'editable-parts.json'),
                cameras_sha256=digest(SOURCE/'cameras.json'),materials={name:digest(path)for name,path in source_materials(raw).items()})
    write(out/'editable-inputs.json',record)
    return record

def run(pack,out,manifest,raw):
    record=json.loads((out/'editable-inputs.json').read_bytes())
    for role,row in manifest['assets'].items():
        if role!='native': assert digest(pack/row['file'])==row['sha256']
    assert digest(out/'editable-parts.json')==record['parts_sha256'] and digest(raw)==record['raw_sha256']
    maker=PROJECT/'source/precise/jingan-country-hospital/source/make_native.py'
    checker=PROJECT/'tools/verify_editable_model.py'
    script=SOURCE/'build_blender_source.py'
    blend=out/(ID+'-editable.blend'); proof=out/'reopened.json'; preview=out/'native-preview.png'
    env=dict(os.environ,BOISSEZON_RAW=str(raw),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    base=[str(script),'-b','--threads','1','--python-exit-code','1','--python']
    commands=[('make',base+[maker,'--',out/'editable-parts.json',blend,preview]),('reopen',base+[checker,'--',blend,raw,proof])]
    events=[]
    for name,cmd in commands:
        when=datetime.now(timezone.utc).isoformat(); log=out/(name+'.log')
        with log.open('w')as stream:
            proc=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,env=env);rc=proc.wait()
        events.append({'phase':name,'pid':proc.pid,'start':when,'finished':datetime.now(timezone.utc).isoformat(),'exit':rc,'log_sha256':digest(log)})
        write(out/'blender-exits.json',events)
        if rc:raise RuntimeError(f'{name} exited {rc}. Read {log}')
    report=json.loads(proof.read_bytes())
    assert report['match_raw'] and report['mesh_count']==record['groups']['count']
    assert report['triangles']==record['triangles'] and report['boissezon']['cameras']==json.loads((SOURCE/'cameras.json').read_bytes())
    assert all(m['extension']=='REPEAT' for m in report['boissezon']['textured_materials'].values())
    assert report['boissezon']['editable_groups']==record['groups']
    assets=dict(manifest['assets']);assets['native']={'file':blend.name,'bytes':blend.stat().st_size,'sha256':digest(blend)}
    write(out/'four-role-manifest.json',{**manifest,'assets':assets})
    print(json.dumps(dict(passed=True,editable=assets['native'],meshes=report['mesh_count'],triangles=record['triangles'],preview_sha256=digest(preview))))

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('stage',choices=['prepare','run'])
    cli.add_argument('pack',type=Path);cli.add_argument('out',type=Path)
    args=cli.parse_args();out=args.out.resolve();out.mkdir(exist_ok=True,parents=True);pack=args.pack.resolve()
    manifest=json.loads((pack/'manifest.json').read_bytes())
    raw=pack/manifest['assets']['raw']['file']
    if args.stage=='prepare':print(json.dumps(prepare(pack,out,manifest,raw),ensure_ascii=False))
    else:run(pack,out,manifest,raw)
