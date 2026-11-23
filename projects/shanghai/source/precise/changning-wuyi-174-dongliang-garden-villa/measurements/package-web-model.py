"""Encode two web models, decode again and compare geometry, textures and per-corner UVs."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

SOURCE=Path(__file__).resolve().parents[1]/'source'
sys.path.insert(0,str(SOURCE))
from build_model import ID, META, PROJECT
native=runpy.run_path(str(SOURCE/'build_blender_source.py'))
TEXTURES=native['TEXTURES']
texture_extension=native['texture_extension']
from package_architectural_model import glb_stats,check_pair
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-gongyi-fang-975-987-sichuan-road/source'))
from asset_rights import retain_metadata
Model=runpy.run_path(str(PROJECT/'source/precise/changning-hengchang-li-yuyuan-road-gatehouse/measurements/check_render_uv.py'))['Model']


def asset(path):
    with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(file=path.name,bytes=path.stat().st_size,sha256=digest,**glb_stats(path))


def write(path,record):
    path.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')


def package(exports,out,audit,encoder):
    out.mkdir(exist_ok=True,parents=True);audit.mkdir(exist_ok=True,parents=True)
    results={};closures={};assets={}
    for role,suffix in [('full','web'),('lod','lod')]:
        source=exports/(role+'-source.glb')
        packed=out/(ID+'-'+suffix+'.glb')
        decoded=exports/('decoded-'+role+'.glb')
        closure=json.loads((exports/(role+'-closure.json')).read_bytes())
        if closure['failures']:raise ValueError('Source contains non-closed components')
        subprocess.run([encoder,'-i',source,'-o',packed,'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
        retain_metadata(packed,source)
        surface=check_pair(source,packed,decoded)
        author,web,unpacked=[Model(path)for path in (source,packed,decoded)]
        try:
            assert author.doc['extras']==web.doc['extras']==unpacked.doc['extras']==META
            assert author.doc['asset']['copyright']==web.doc['asset']['copyright']
            images=author.textures(SOURCE)
            assert set(images)==set(TEXTURES) and images==web.textures(SOURCE)==unpacked.textures(SOURCE)
            for name in TEXTURES:
                assert all(texture_extension(model.doc,name)=='REPEAT' for model in [author,web,unpacked])
            faces=author.surfaces(SOURCE)
            assert faces==unpacked.surfaces(SOURCE)
            assert all(faces[n]['nondegenerate_texture_triangles']>0 for n in TEXTURES)
            assets[role]=asset(packed)
            assert closure['triangles']==assets[role]['triangles']
            closures[role]=dict(source_sha256=author.sha256,**closure)
            results[role]=dict(author_sha256=author.sha256,packed_sha256=web.sha256,
                               decoded_sha256=unpacked.sha256,triangles=closure['triangles'],
                               surfaces=surface,materials=faces,textures=images)
        finally:
            for model in (author,web,unpacked):model.data.close()
    raw=out/(ID+'-raw.glb')
    shutil.copyfile(exports/'full-source.glb',raw);assets['raw']=asset(raw)
    assert assets['raw']['triangles']==assets['full']['triangles']>assets['lod']['triangles']
    write(audit/'editable-parts-closure.json',closures)
    write(audit/'web-model-verification.json',results)
    write(out/'manifest.json',{**META,'model_id':ID,'assets':assets,'all_dimensions_estimated':True})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('exports',type=Path);p.add_argument('out',type=Path);p.add_argument('audit',type=Path)
    p.add_argument('--gltfpack',default='gltfpack');a=p.parse_args()
    package(a.exports,a.out,a.audit,a.gltfpack)
