"""Pack explicit public source paths; rebuild near and far with a hidden workspace and no network."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import site
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def bundle(project, roster, entry, reference_dir, output, mask):
    members=json.loads(roster.read_bytes())
    if not isinstance(members,list) or not all(isinstance(p,str) for p in members):
        raise ValueError('Source roster must be an array of project-relative strings')
    if len(set(members))!=len(members) or entry not in members:
        raise ValueError('Missing entry or duplicate paths')
    for name in members:
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts or not (project/rel).is_file():
            raise ValueError(name)
    output.parent.mkdir(parents=True,exist_ok=True)
    wrapper=("from pathlib import Path\nimport subprocess,sys\n"
             f"entry=Path(__file__).resolve().parent/{entry!r}\n"
             "out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)\n"
             "for role,extra in [('full',[]),('lod',['--lod'])]:\n"
             "    subprocess.run([sys.executable,'-B',entry,*extra,'--output',out/(role+'-source.glb')],check=True)\n")
    readme='解包后，在有项目 Python 建模依赖的环境中运行 python rebuild.py output。两级 GLB 的校验值在下载验证记录中。\n'
    with tempfile.TemporaryDirectory(dir=output.parent) as name:
        tmp=Path(name);archive=tmp/output.name
        with ZipFile(archive,'w') as z:
            for rel in sorted([*members,'rebuild.py','SOURCE-REBUILD.md']):
                if rel in ('rebuild.py','SOURCE-REBUILD.md') and rel in members:raise ValueError('Reserved basename')
                raw=wrapper.encode() if rel=='rebuild.py' else readme.encode() if rel=='SOURCE-REBUILD.md' else (project/rel).read_bytes()
                info=ZipInfo(rel,(1980,1,1,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
                z.writestr(info,raw)
        unpack=tmp/'unpacked';unpack.mkdir()
        with ZipFile(archive) as z:
            assert z.testzip() is None
            z.extractall(unpack)
        if mask.resolve() in unpack.resolve().parents:
            raise ValueError('Choose output outside the workspace to be hidden')
        command=['bwrap','--ro-bind','/','/','--bind',str(unpack),str(unpack),'--tmpfs',str(mask.resolve()),
                 '--unshare-net','--clearenv','--setenv','PATH',os.defpath,'--setenv','PYTHONUSERBASE',site.getuserbase(),
                 '--setenv','PYTHONDONTWRITEBYTECODE','1','--setenv','OPENBLAS_NUM_THREADS','1',
                 '--setenv','OMP_NUM_THREADS','1','--chdir',str(unpack),'--',sys.executable,'-B','rebuild.py','output']
        subprocess.run(command,check=True)
        checks={}
        for role in ('full','lod'):
            filename=role+'-source.glb'
            result=unpack/'output'/filename
            assert sha(result)==sha(reference_dir/filename)
            checks[filename]={'sha256':sha(result),'bytes':result.stat().st_size}
        archive.replace(output)
    report=dict(file=output.name,sha256=sha(output),bytes=output.stat().st_size,members=sorted(members),
                offline=True,workspace_hidden=True,rebuild=checks)
    output.with_suffix('.verification.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['project','roster','reference_dir','output','hide_workspace']:p.add_argument(k,type=Path)
    p.add_argument('--entry',required=True)
    a=p.parse_args()
    bundle(a.project,a.roster,a.entry,a.reference_dir,a.output,a.hide_workspace)
