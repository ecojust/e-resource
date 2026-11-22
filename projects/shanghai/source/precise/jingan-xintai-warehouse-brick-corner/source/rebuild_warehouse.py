"""Package and verify near, far and Blender representations using the same public sources."""
from pathlib import Path
import argparse, json, shutil, subprocess, sys
from build_model import Builder,META,PALETTE,ID,SOURCE,add_building,make_texture
from package_architectural_model import glb_stats,check_pair,retain_metadata
from package_editable import sha,write,package

def run():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--decoded',type=Path)
    p.add_argument('--blender',default='blender');p.add_argument('--gltfpack',default='gltfpack');p.add_argument('--oidn',default='oidnDenoise');p.add_argument('--magick',default='magick')
    a=p.parse_args();dest=a.out.resolve();audit=a.audit.resolve();decoded=(a.decoded or audit/'decoded').resolve()
    for d in [dest,audit,decoded]:d.mkdir(exist_ok=True,parents=True)
    make_texture();assets={};comparisons={};raw=dest/(ID+'-raw.glb')
    for role,filename,source,far in [('full','web',raw,False),('lod','lod',decoded/'original-far.glb',True)]:
        b=Builder(PALETTE);add_building(b,far);b.save(source,META)
        if not far:assets['raw']={'file':raw.name,'bytes':raw.stat().st_size,'sha256':sha(raw),**glb_stats(raw)}
        wire=dest/(ID+'-'+filename+'.glb')
        subprocess.run([a.gltfpack,'-i',source,'-o',wire,'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
        retain_metadata(wire,source);comparisons[role]=check_pair(source,wire,decoded/(role+'.glb'))
        assets[role]=dict(file=wire.name,bytes=wire.stat().st_size,sha256=sha(wire),**glb_stats(wire))
    write(audit/'mesh-assets.json',assets);write(audit/'decoded-surfaces.json',comparisons)
    subprocess.run([sys.executable,SOURCE/'check_openings.py','--raw',raw,'--decoded-web',decoded/'full.glb','--decoded-lod',decoded/'lod.glb','--report',audit/'three-mesh-probes.json'],check=True)
    package(dest,audit,assets,a.blender,a.oidn,a.magick)
if __name__=='__main__':run()
