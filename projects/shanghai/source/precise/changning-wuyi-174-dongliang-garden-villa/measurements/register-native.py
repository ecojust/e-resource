"""Add a downloadable editable model only after its independently reopened meshes match the raw GLB."""
import argparse
import hashlib
import json
from pathlib import Path


def register(models,report):
    path=models/'manifest.json'
    manifest=json.loads(path.read_bytes());checked=json.loads(report.read_bytes())
    native=models/(manifest['id']+'-editable.blend')
    with native.open('rb')as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    assert checked['match_raw'] and checked['blend_sha256']==digest
    assert checked['source_glb_sha256']==manifest['assets']['raw']['sha256']
    assert checked['triangles']==manifest['assets']['raw']['triangles']
    manifest['assets']['native']=dict(file=native.name,bytes=native.stat().st_size,sha256=digest,
        editable_groups=checked['editable_groups'],triangles=checked['triangles'],cameras=checked['cameras'],
        format='Blender')
    tmp=path.with_suffix('.new')
    tmp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');tmp.replace(path)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('models',type=Path);p.add_argument('report',type=Path)
    a=p.parse_args();register(a.models,a.report)
