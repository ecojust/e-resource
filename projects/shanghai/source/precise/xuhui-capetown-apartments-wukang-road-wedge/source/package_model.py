"""Compress near and far GLBs, independently decode them, and verify each oriented surface."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from build_model import ID, META, PROJECT

postal=PROJECT/'source/precise/hongkou-general-post-office/source'
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-gongyi-fang-975-987-sichuan-road/source'))
from asset_rights import retain_metadata
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source_dir',type=Path);cli.add_argument('out',type=Path)
    cli.add_argument('--gltfpack',default=os.environ.get('GLTFPACK','gltfpack'))
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    raw=args.out/(ID+'-raw.glb');shutil.copyfile(args.source_dir/'full-source.glb',raw)
    assets={};pair_checks={}
    def info(p,n):
        return dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),triangles=n)
    for role,suffix in [('full','web'),('lod','lod')]:
        source=args.source_dir/(role+'-source.glb');dest=args.out/(ID+'-'+suffix+'.glb');decoded=args.out/('decoded-'+role+'.glb')
        subprocess.run([args.gltfpack,'-i',str(source),'-o',str(dest),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
        retain_metadata(dest,source)
        subprocess.run(['node',str(postal/'decode_meshopt.mjs'),str(dest),str(decoded),str(PROJECT/'vendor/meshopt_decoder.module.js')],check=True)
        reference=SerialScene(source);actual=SerialScene(decoded)
        digest=actual.surface_digest()
        if digest!=reference.surface_digest():raise ValueError(role+' oriented surface or material changed after decoding')
        if role=='full':assets['raw']=info(raw,len(reference.tri))
        assets[role]=info(dest,len(actual.tri))
        pair_checks[role]={'source':reference.asset,'decoded':actual.asset,'oriented_surfaces':digest}
    manifest={'id':ID,'model_id':ID,'name':META['name'],'address':META['address'],'period':META['period'],'geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'assets':assets}
    for name,data in [('manifest.json',manifest),('mesh-decode-comparisons.json',pair_checks)]:
        (args.out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
