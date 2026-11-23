"""Prepare editable part groups and run two independent Blender processes against the verified GLB."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from build_model import Builder, PALETTE, PROJECT, META, ID, HERE, add_building
sys.path.insert(0,str(HERE))
from build_blender_source import helpers, digest, attribution
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import group_parts

def write(path,data):
    tmp=path.with_suffix(path.suffix+'.partial')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(path)
def read(path):return json.loads(path.read_bytes())

def prepare(out,raw):
    if META.get('id') != ID or ID != 'xuhui-gaoan-77-curved-veranda':
        raise ValueError('The editable package requires the authored No. 77 garden residence')
    b=Builder(PALETTE);add_building(b,False)
    authored = group_parts(b)
    groups,aliases = {},{}
    for label,part in authored.items():
        name = label
        if len(name.encode())>63:
            name = label.removeprefix('Gaoan 77 | ')
        if name in groups or len(name.encode())>63:
            from hashlib import sha256
            tail = sha256(label.encode()).hexdigest()[:9]
            name = name.encode()[:51].decode(errors='ignore').rstrip()+' '+tail
        if name!=label:
            aliases[name] = label
        groups[name] = part
    if len(groups) != len(authored):
        raise ValueError('The short Blender names collide')
    names = helpers.editable_groups(groups.keys())
    signatures=('main timber post','veranda grille scroll','cropped front hip course')
    if any(not any(word in label for label in authored) for word in signatures):
        raise ValueError('The principal timber, coiled railing or formed roof courses are missing')
    regen=out/'regenerated.glb';b.save(regen,META)
    assert digest(regen)==digest(raw)
    assert META['camera_views']==read(HERE/'cameras.json')
    parts=out/'editable-parts.json'
    write(parts,{'groups':groups,'palette':b.palette,'metadata':dict(META)})
    images={m:{'sha256':digest(p),'corners':3*len(helpers.texture_faces(raw,m))} for m,p in helpers.source_materials(raw).items()}
    record={'raw_sha256':digest(raw),'editable_groups':names,'original_names':aliases,'parts_sha256':digest(parts),'triangles':sum(len(v['f']) for v in groups.values()),
            'cameras_sha256':digest(HERE/'cameras.json'),'materials':images,'metadata':attribution(raw)}
    write(out/'editable-inputs.json',record)
    return record

def run(pack,out,raw,manifest):
    record=read(out/'editable-inputs.json');parts=out/'editable-parts.json';assert digest(parts)==record['parts_sha256'] and digest(raw)==record['raw_sha256']
    assert record['triangles']==manifest['assets']['raw']['triangles'] and digest(HERE/'cameras.json')==record['cameras_sha256']
    if manifest.get('id') != ID or not {'raw','full','lod'} <= set(manifest['assets']):
        raise ValueError('The three production assets must be present in the current manifest')
    for k,v in manifest['assets'].items():
        if k!='native':assert digest(pack/v['file'])==v['sha256'] and (pack/v['file']).stat().st_size==v['bytes']
    blender=os.getenv('BLENDER') or shutil.which('blender')
    if not blender:raise FileNotFoundError('Blender executable')
    base=[blender,'-b','--threads','1','--python-exit-code','1'];script=HERE/'build_blender_source.py'
    maker=PROJECT/'source/precise/jingan-country-hospital/source/make_native.py'
    checker=PROJECT/'tools/verify_editable_model.py'
    blend=out/(ID+'-editable.blend');proof=out/'reopened.json';preview=out/'native-preview.png'
    jobs={'make':[*base,'--python',script,'--python',maker,'--',parts,blend,preview],
          'reopen':[*base,'--python',checker,'--python',script,'--',blend,raw,proof]}
    history=[]
    for kind,command in jobs.items():
        env=dict(os.environ,GAOAN_77_STAGE=kind,GAOAN_77_RAW=str(raw),GAOAN_77_GROUPS=str(out/'editable-inputs.json'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        log=out/(kind+'.log');start=datetime.now(timezone.utc).isoformat()
        with log.open('w') as stream:
            proc=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,env=env);exitcode=proc.wait()
        history.append(dict(phase=kind,pid=proc.pid,start=start,finish=datetime.now(timezone.utc).isoformat(),exit=exitcode,log_sha256=digest(log)))
        write(out/'blender-exits.json',history)
        if exitcode:raise RuntimeError(f'{kind} exited {exitcode}; see {log}')
    report=read(proof);re=report['gaoan_77'];assert report['match_raw'] and report['triangles']==record['triangles'] and re['editable_groups']==record['editable_groups']
    assert re['cameras']==META['camera_views'] and re['metadata']==record['metadata']
    for m,v in record['materials'].items():
        actual=re['textured_materials'][m];assert actual['textured_corners']==v['corners'] and actual['packed_png_sha256']==v['sha256'] and actual['extension']=='REPEAT'
    final=pack/blend.name
    if final.exists():
        if digest(final)!=digest(blend):raise ValueError('The output already contains a different editable file')
    else:
        try:os.link(blend,final)
        except OSError:shutil.copyfile(blend,final)
    native=dict(file=blend.name,bytes=blend.stat().st_size,sha256=digest(blend))
    result=dict(manifest,assets=dict(manifest['assets'],native=native));write(out/'four-role-manifest.json',result);write(pack/'manifest.json',result)
    return dict(native=native,triangles=report['triangles'],groups=report['mesh_count'],textures=re['textured_materials'])

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('stage',choices=['prepare','run']);cli.add_argument('pack',type=Path);cli.add_argument('out',type=Path);a=cli.parse_args()
    pack=a.pack.resolve();out=a.out.resolve();out.mkdir(exist_ok=True,parents=True)
    manifest=read(pack/'manifest.json');raw=pack/manifest['assets']['raw']['file']
    result=prepare(out,raw) if a.stage=='prepare' else run(pack,out,raw,manifest)
    print(json.dumps(result,ensure_ascii=False))
