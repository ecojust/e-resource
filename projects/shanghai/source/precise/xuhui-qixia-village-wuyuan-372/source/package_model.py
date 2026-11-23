"""Encode each courtyard model and verify decoded surfaces, UVs, relief and transparent glazing."""
import argparse
import json
import os
from pathlib import Path
import runpy
from build_blender_source import helpers
from build_model import PROJECT


def glass_bindings(path):
    doc=helpers.raw_document(path)
    return {m['name']:{'mode':m['alphaMode'],'alpha':m['pbrMetallicRoughness']['baseColorFactor'][3]}
            for m in doc['materials'] if m.get('alphaMode')=='BLEND'}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source_dir',type=Path);cli.add_argument('out',type=Path)
    cli.add_argument('--gltfpack',default=os.environ.get('GLTFPACK','gltfpack'))
    a=cli.parse_args();shared=runpy.run_path(str(PROJECT/'source/precise/xuhui-shaanxi-222-no20-residence-gate/source/package_model.py'))
    shared['packager'].package(a.source_dir,a.out,a.gltfpack)
    proof={}
    for role in ('full','lod'):
        raw=glass_bindings(a.source_dir/(role+'-source.glb'));decoded=glass_bindings(a.out/('decoded-'+role+'.glb'))
        if raw.keys()!=decoded.keys() or any(abs(raw[n]['alpha']-decoded[n]['alpha'])>1.e-6 for n in raw):
            raise ValueError('Opacity mode or alpha changed in the decoded courtyard model')
        proof[role]={'source':raw,'decoded':decoded}
    (a.out/'decoded-glazing-comparisons.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
