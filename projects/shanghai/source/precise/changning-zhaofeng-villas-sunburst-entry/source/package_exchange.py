"""Build FBX, OBJ/MTL with textures, and binary STL from the verified editable street gate."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
HERE=Path(__file__).absolute().parent
def summary(path):return dict(file=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def write(path,value):
    temp=path.with_suffix('.partial');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temp.replace(path)
def main(pack,out):
    doc=json.loads((pack/'manifest.json').read_bytes());id=doc['id'];blend=pack/doc['assets']['native']['file']
    assert summary(blend)==doc['assets']['native'];out.mkdir(exist_ok=True,parents=True)
    script=HERE/'exchange_blender.py';blender=os.environ.get('BLENDER')or shutil.which('blender')
    processes=[]
    for stage in ('export','fbx','obj','stl'):
        log=out/(stage+'.log');begin=datetime.now(timezone.utc).isoformat()
        args=[blender,'-b','--threads','1','--python-exit-code','1','-P',script,'--',stage,blend,out,id]
        with log.open('w')as stream:
            p=subprocess.Popen(args,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'));code=p.wait()
        processes.append(dict(stage=stage,pid=p.pid,exit=code,started=begin,finished=datetime.now(timezone.utc).isoformat(),log_sha256=summary(log)['sha256']))
        write(out/'exchange-exits.json',processes)
        if code:raise RuntimeError('See '+str(log))
    finalize(pack, out, doc)


def finalize(pack, out, doc):
    id=doc['id']
    wave=out/(id+'-obj-mtl.zip')
    with ZipFile(wave,'w')as archive:
        for p in sorted((out/'obj').iterdir()):
            if p.suffix.lower()not in ('.obj','.mtl','.png'):continue
            item=ZipInfo(p.name,(1980,1,1,0,0,0));item.external_attr=0o100644<<16
            item.compress_type=ZIP_DEFLATED;archive.writestr(item,p.read_bytes())
    interchange={}
    for role,source in [('fbx',out/(id+'.fbx')),('obj',wave),('stl',out/(id+'.stl'))]:
        final=pack/source.name
        if final.exists():
            if summary(final)!=summary(source):raise ValueError('Conflicting exchange file: '+source.name)
        else:
            try:os.link(source,final)
            except OSError:shutil.copyfile(source,final)
        proof=json.loads((out/(role+'-reopened.json')).read_bytes())
        interchange[role]=dict(**summary(final),triangles=proof['oriented_triangles'],units='metres')
    doc['interchange']=interchange;write(pack/'manifest.json',doc)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('pack',type=Path);cli.add_argument('out',type=Path);args=cli.parse_args()
    main(args.pack.absolute(),args.out.absolute())
