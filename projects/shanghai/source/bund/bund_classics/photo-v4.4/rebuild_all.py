"""Rebuild structural wall topology, photo/roof model and compressed variants."""
import argparse, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--project',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--blender',default='blender')
p.add_argument('--gltfpack',required=True)
p.add_argument('--render',action='store_true')
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
baseline=a.output/'bund17-clean-base.blend'
def blend(script,opts):
 subprocess.run([a.blender,'--background','--threads','1','--python',str(HERE/script),'--',*map(str,opts)],check=True)
blend('clean_wall_baseline.py',['--input',HERE/'bund17-base.blend','--output',baseline,'--report',a.output/'wall-validation.json'])
opts=['--project',a.project,'--output',a.output,'--base-model',baseline]
if a.render:opts.append('--render')
blend('build_photo_windows.py',opts)
subprocess.run([sys.executable,str(HERE/'compress_models.py'),'--output',str(a.output),'--gltfpack',a.gltfpack],check=True)
for path in a.output.iterdir():
 if path.is_file():assert path.stat().st_size<100_000_000,path
