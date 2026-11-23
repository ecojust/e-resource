"""Install a verified Blender file beside its corresponding three published GLBs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def register(work,models):
    manifest_file=models/'manifest.json'
    data=json.loads(manifest_file.read_bytes())
    proof=json.loads((work/'reopened.json').read_bytes())
    name=data['id'];source=work/(name+'.blend')
    if not proof['match_raw'] or proof['raw_sha256']!=data['assets']['raw']['sha256'] or sha(source)!=proof['blend_sha256']:
        raise ValueError('The Blender verification and the installed raw GLB must describe the same building.')
    dest=models/(name+'-editable.blend')
    if not dest.exists() or sha(dest)!=proof['blend_sha256']:
        temp=dest.with_suffix('.blend.installing')
        shutil.copyfile(source,temp);temp.replace(dest)
    data['assets']['native']=dict(file=dest.name,bytes=dest.stat().st_size,sha256=proof['blend_sha256'],
        triangles=proof['triangles'],editable_meshes=proof['mesh_count'],format='Blender',
        cameras=len(proof['cameras']),packed_images=len(proof['packed_texture_checks']))
    temp=manifest_file.with_suffix('.json.installing');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(manifest_file)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('native_dir',type=Path);p.add_argument('model_dir',type=Path)
    args=p.parse_args();register(args.native_dir,args.model_dir)
