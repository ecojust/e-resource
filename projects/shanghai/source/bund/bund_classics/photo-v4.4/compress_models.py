"""Compress both variants, retaining photograph provenance gltfpack drops."""
from pathlib import Path
import argparse,subprocess,shutil
from glb_provenance import retain_provenance
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--gltfpack',default=shutil.which('gltfpack') or 'gltfpack');args=ap.parse_args();out=args.output
for original,result,options in [('bund17-photo.glb','bund17-photo-web.glb',['-cc','-noq','-km','-ke']),('bund17-untextured.glb','bund17-photo-lod.glb',['-cc','-si','0.6','-noq','-km','-ke'])]:
 subprocess.run([args.gltfpack,'-i',str(out/original),'-o',str(out/result),*options],check=True)
 retain_provenance(out/result)
 assert (out/result).stat().st_size<100_000_000
 print(result,(out/result).stat().st_size)
