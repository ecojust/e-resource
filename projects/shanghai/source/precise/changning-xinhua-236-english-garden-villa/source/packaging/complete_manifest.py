"""Seal eight physical roles after their individual checks have succeeded."""
import argparse
import hashlib
import json
from pathlib import Path

def read(p):
    return json.loads(p.read_bytes())

def verified(folder,r):
    path=folder/r['file']
    if path.parent!=folder or not path.is_file():raise ValueError(path)
    with path.open('rb') as stream:h=hashlib.file_digest(stream,'sha256').hexdigest()
    if h!=r['sha256'] or path.stat().st_size!=r['bytes']:raise ValueError(path)
    return dict(file=path.name,sha256=h,bytes=path.stat().st_size)

p=argparse.ArgumentParser(description=__doc__)
for name in ['manifest','native_make','native_reopen','fbx','obj_stl','source_zip','independent_out']:p.add_argument(name,type=Path)
args=p.parse_args();m=read(args.manifest);folder=args.manifest.parent
assert set(m['assets'])=={'raw','full','lod'}
build,reopen=read(args.native_make),read(args.native_reopen)
for k in ('reference_sha256','sha256','parts','images','triangles','uv_corners','cameras','materials'):
    assert build[k]==reopen[k],k
assert reopen['reference_sha256']==m['assets']['raw']['sha256']
fbx,other,source=map(read,(args.fbx,args.obj_stl,args.source_zip))
assert fbx['oriented_positions_and_uv_checked'] and set(fbx['embedded_images'].values())==set(reopen['images'].values())
assert other['obj_material_uv_corner_records_verified'] and other['stl_oriented_triangles_verified']
assert source['offline'] and source['workspace_hidden'] and source['rebuild']['full-source.glb']['sha256']==m['assets']['raw']['sha256']
actual={k:verified(folder,r) for k,r in m['assets'].items()}
more={'native':reopen,'fbx':fbx,**other['assets'],'source':source}
actual.update({k:verified(folder,r) for k,r in more.items()})
assert len(actual)==8
m['assets']['native']=actual['native']
m['interchange']={k:actual[k] for k in ['fbx','obj','stl']}
m['source_archive']=actual['source']
args.independent_out.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
