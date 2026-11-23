"""Encode the courtyard facade meshes and verify decoded surfaces, UVs, relief and transparent glazing."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys
from build_model import PROJECT
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_blender_source import helpers


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
            raise ValueError('Opacity or alpha mode changed during mesh encoding')
        def emission(path):
            return {m['name']:m['emissiveFactor'] for m in helpers.raw_document(path)['materials'] if 'emissiveFactor' in m and any(m['emissiveFactor'])}
        original_emission=emission(a.source_dir/(role+'-source.glb'))
        decoded_emission=emission(a.out/('decoded-'+role+'.glb'))
        if original_emission.keys()!=decoded_emission.keys() or any(max(abs(a-b) for a,b in zip(original_emission[k],decoded_emission[k]))>0.004 for k in original_emission):
            raise ValueError('The vestibule pendant emission changed during encoding')
        proof[role]={'source':raw,'decoded':decoded,'source_emission':original_emission,'decoded_emission':decoded_emission}
    (a.out/'decoded-glazing-comparisons.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
