"""Rebuild only Bund19/20/23 from the package's frozen original models."""
import argparse,json,subprocess,sys
from pathlib import Path
from arguments import PACKAGE,verify_baselines

parser=argparse.ArgumentParser()
parser.add_argument('--workdir',type=Path,required=True)
parser.add_argument('--blender',default='blender')
parser.add_argument('--gltfpack',type=Path,required=True)
parser.add_argument('--project',type=Path,help='Shanghai project with vendored Three/Meshopt, for decoder validation')
args=parser.parse_args();verify_baselines();work=args.workdir.resolve();work.mkdir(parents=True,exist_ok=True)
commands=[]
def run(command):
    commands.append(command);subprocess.run(command,check=True,cwd=PACKAGE)
for name in ['inspect_capture.py','capture_windows.py']:
    run([args.blender,'--background','--threads','2','--python-exit-code','1','--python',str(PACKAGE/name),'--','--workdir',str(work)])
run([sys.executable,str(PACKAGE/'union_panels.py'),'--workdir',str(work)])
for name in ['apply_union.py','audit_surfaces.py']:
    run([args.blender,'--background','--threads','2','--python-exit-code','1','--python',str(PACKAGE/name),'--','--workdir',str(work)])
run([sys.executable,str(PACKAGE/'finalize_assets.py'),'--workdir',str(work),'--gltfpack',str(args.gltfpack.resolve())])
if args.project:
    for bid in ['bund19','bund20','bund23']:
        d=work/'candidate'/bid
        comparator='compare_compression.mjs' if bid=='bund19' else 'compare_transformed.mjs'
        run(['node',str(PACKAGE/comparator),str(args.project.resolve()),str(d/f'{bid}.glb'),str(d/f'{bid}-web.glb'),str(d/'compression-validation.json')])
    run(['node',str(PACKAGE/'decode_assets.mjs'),str(args.project.resolve()),str(work)])
(work/'rebuild-commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
