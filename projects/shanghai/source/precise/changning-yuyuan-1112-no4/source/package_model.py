"""Encode both Yuyuan Lane house 4 meshes, compare decoded geometry and check each colour and relief map."""
import argparse
import json
import os
import runpy
import shutil
from pathlib import Path
from build_model import PROJECT
import sys
sys.path.insert(0,str(Path(__file__).absolute().parent))
from build_blender_source import texture_bindings

def package(source, output, encoder):
    adapter = PROJECT/'source/precise/xuhui-shaanxi-222-no20-residence-gate/source/package_model.py'
    runpy.run_path(str(adapter))['packager'].package(source,output,encoder)
    shutil.copyfile(source/'full-source.geometry.json',output/'source-part-order.json')
    results={}
    for role in ('full','lod'):
        original=texture_bindings(source/(role+'-source.glb'))
        decoded=texture_bindings(output/('decoded-'+role+'.glb'))
        if original!=decoded or sum('normal' in binding for binding in original.values())!=5:
            raise ValueError('Five original albedo and normal pairs must survive decoding')
        results[role]=decoded
    (output/'decoded-yuyuan-no4-finishes.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source_dir',type=Path)
    cli.add_argument('out',type=Path)
    cli.add_argument('--gltfpack',default=os.environ.get('GLTFPACK','gltfpack'))
    args=cli.parse_args()
    package(args.source_dir,args.out,args.gltfpack)
