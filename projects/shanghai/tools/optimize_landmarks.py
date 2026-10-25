#!/usr/bin/env python3
"""Create compact web copies while preserving the original editable landmarks.
Requires gltfpack (npm install -g gltfpack). No triangle simplification is requested.
16-bit local positions add centimetre-scale numerical quantization, not survey accuracy.
"""
from pathlib import Path
import argparse,json,shutil,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gltfpack',default=shutil.which('gltfpack'));p.add_argument('--only',nargs='*');args=p.parse_args()
if not args.gltfpack:p.error('Install gltfpack, or use --gltfpack /path/to/gltfpack')
folder=ROOT/'assets/models';out=folder/'optimized';out.mkdir(exist_ok=True)
report=[]
def info(path):
 b=path.read_bytes();length=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+length]);return {'bytes':len(b),'primitives':sum(len(m['primitives']) for m in g['meshes']),'draw_primitives':sum(len(g['meshes'][node['mesh']]['primitives']) for node in g.get('nodes',[]) if 'mesh' in node)}
for source in sorted(folder.glob('*.glb')):
 if args.only and source.stem not in args.only:continue
 target=out/source.name
 subprocess.run([args.gltfpack,'-i',str(source),'-o',str(target),'-cc','-vp','16','-vn','12','-km','-ke','-mi'],check=True)
 if target.stat().st_size>=100_000_000:raise ValueError('Model exceeds repository file limit')
 report.append({'id':source.stem,'original':info(source),'web':info(target)})
 print(json.dumps(report[-1]))
if not args.only:(out/'optimization.json').write_text(json.dumps(report,indent=2)+'\n')
