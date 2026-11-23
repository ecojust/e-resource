"""Compress both mesh levels and verify their decoded geometry, UVs and embedded textures."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parent/'source'
sys.path.insert(0,str(SOURCE))
local_model=runpy.run_path(str(SOURCE/'build_model.py'))
ID,META=local_model['ID'],local_model['META']
from fabric import PROJECT, GRAY, RED
from courtyard_roofs import TILE
from package_architectural_model import glb_stats,check_pair

PRECISE=PROJECT/'source/precise'
sys.path.insert(0,str(PRECISE/'hongkou-gongyi-fang-975-987-sichuan-road/source'))
from asset_rights import retain_metadata
Model=runpy.run_path(str(PRECISE/'changning-hengchang-li-yuyuan-road-gatehouse/measurements/check_render_uv.py'))['Model']


def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def asset(path):
    return dict(file=path.name,bytes=path.stat().st_size,sha256=sha(path),**glb_stats(path))


def write(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def pack(input_dir, output, audit, encoder):
    output.mkdir(parents=True,exist_ok=True);audit.mkdir(parents=True,exist_ok=True)
    assets={};reports={};closures={}
    for level,role,suffix in [('near','full','web'),('far','lod','lod')]:
        raw=input_dir/(level+'.glb');decoded=input_dir/('decoded-'+level+'.glb')
        result=output/(ID+'-'+suffix+'.glb')
        closure=json.loads((input_dir/(level+'-closure.json')).read_bytes())
        assert not closure['failures'] and closure['sha256']==sha(raw)
        subprocess.run([encoder,'-i',str(raw),'-o',str(result),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
        retain_metadata(result,raw)
        geometry=check_pair(raw,result,decoded)
        records=[Model(p)for p in (raw,result,decoded)]
        original,web,unpacked=records
        try:
            assert all(m.doc['extras']==META and m.doc['asset']['copyright']==META['copyright']for m in records)
            textures=original.textures(SOURCE)
            assert set(textures)=={GRAY,RED,TILE} and all(m.textures(SOURCE)==textures for m in records)
            for m in records:
                for tex in m.doc['textures']:
                    sampler=m.doc['samplers'][tex['sampler']]
                    assert all(sampler.get(axis,10497)==10497 for axis in ['wrapS','wrapT'])
            surfaces=original.surfaces(SOURCE);assert surfaces==unpacked.surfaces(SOURCE)
            assert all(surfaces[material]['nondegenerate_texture_triangles']>0 for material in textures)
            assets[role]=asset(result);assert assets[role]['triangles']==closure['triangles']
            reports[role]=dict(source=sha(raw),packed=sha(result),decoded=sha(decoded),geometry=geometry,
                               material_and_uv=surfaces,embedded_images=textures)
            closures[role]=closure
        finally:
            for record in records:record.data.close()
    raw_out=output/(ID+'-raw.glb')
    shutil.copyfile(input_dir/'near.glb',raw_out);assets['raw']=asset(raw_out)
    assert assets['full']['triangles']==assets['raw']['triangles']>assets['lod']['triangles']
    write(audit/'closed-solids.json',closures)
    write(audit/'web-model-verification.json',reports)
    write(output/'manifest.json',{**META,'model_id':ID,'assets':assets,'all_dimensions_estimated':True})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_dir',type=Path);parser.add_argument('output',type=Path);parser.add_argument('audit',type=Path)
    parser.add_argument('--gltfpack',default='gltfpack')
    args=parser.parse_args();pack(args.input_dir,args.output,args.audit,args.gltfpack)
