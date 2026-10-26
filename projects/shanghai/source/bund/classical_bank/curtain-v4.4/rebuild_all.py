"""Offline wall→curtain reconstruction; inputs are bundled immutable wall files."""
import argparse,subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--blender',default='blender');ap.add_argument('--gltfpack',default='gltfpack');ap.add_argument('--project',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
def run(args):subprocess.run([str(x) for x in args],check=True)
run([a.blender,'--background','--threads','2','--python',ROOT/'build_curtain_fix.py','--','--output',out])
run([sys.executable,ROOT/'audit_curtain_preservation.py','--directory',out])
run([sys.executable,ROOT/'compress_models.py','--input',out/'bund15-curtain-raw.glb','--output',out,'--gltfpack',a.gltfpack])
run([sys.executable,ROOT/'audit_assets.py','--directory',out])
project=a.project
if project is None:
 for ancestor in ROOT.parents:
  if (ancestor/'tools/qa/compare_model_compression.mjs').exists():project=ancestor;break
if project is not None:run(['node',project/'tools/qa/compare_model_compression.mjs',project,out/'bund15-curtain-raw.glb',out/'bund15-curtain-web.glb',out/'compression-validation.json'])
print(json.dumps({'output':str(out),'preservation_checks':'passed','cpu_loader_check':bool(project),'visual_acceptance':'Requires separate matched-camera browser A/B; no browser launched here.'}))
