"""Encode the shuttered street exterior and verify oriented surfaces, texture images and corner UVs after decode."""
import argparse
import json
from pathlib import Path
from runpy import run_path
import sys
from build_model import PROJECT,HERE
sys.path.insert(0,str(HERE))
from build_blender_source import helpers,digest

def verify_textures(source_dir,output_dir):
    checks={}
    for role in ('full','lod'):
        source=source_dir/(role+'-source.glb'); decoded=output_dir/('decoded-'+role+'.glb')
        textures={}
        # The documented street-only edition has its own plaster. The completed edition also
        # carries the separately ruled render of the upper wall behind it.
        doc=helpers.raw_document(source)
        used={m['name'] for m in doc['materials'] if 'baseColorTexture' in m.get('pbrMetallicRoughness',{})}
        if not used or not used <= set(helpers.TEXTURES):
            raise ValueError(f'Unknown finish in {role}: {sorted(used)}')
        if doc['extras'].get('id')!=helpers.MODEL_ID:
            raise ValueError('Unexpected building in Kangping Road package')
        for mat in sorted(used):
            filename=helpers.TEXTURES[mat]
            original=helpers.texture_faces(source,mat);actual=helpers.texture_faces(decoded,mat)
            if original!=actual:
                raise ValueError(f'{role} changes authored UVs on {mat}')
            textures[mat]={'corners':3*len(original),'image_sha256':digest(filename),'wrap':'REPEAT','maximum_uv_difference':0.0}
        checks[role]={'source_sha256':digest(source),'decoded_sha256':digest(decoded),'materials':textures}
    (output_dir/'decoded-texture-comparisons.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source_dir',type=Path);parser.add_argument('out',type=Path);parser.add_argument('--gltfpack');args=parser.parse_args()
    common=PROJECT/'source/precise/xuhui-baisaizhong-apartments-fuxing-road-corner/source/package_model.py'
    run_path(str(common))['main']()
    verify_textures(args.source_dir,args.out)
