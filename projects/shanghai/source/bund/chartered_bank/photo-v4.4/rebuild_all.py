"""One-command rebuild using a bundled immutable native baseline; no download."""
import argparse,json,subprocess,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--blender',default='blender');ap.add_argument('--gltfpack',default='gltfpack');ap.add_argument('--project',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);work=out/'work';work.mkdir(exist_ok=True)
def run(args):subprocess.run([str(x) for x in args],check=True)
def blend(script,*args):run([a.blender,'--background','--threads','2','--python',ROOT/script,'--',*args])
baseline=work/'bund18-v4.3.glb';blend('export_baseline.py','--output',baseline)
run([sys.executable,ROOT/'check_wall_inputs.py','--geometry-source',ROOT/'baseline/build_geometry-v4.3.py','--output',out/'source-input-check.json'])
patch=work/'patch';blend('repair_wall_core.py','--input-native',ROOT/'baseline/bund18-v4.3.blend','--input-raw',baseline,'--output',patch)
for old,new in [('bund18-wall-core.glb','bund18-photo.glb'),('bund18-wall-core.blend','bund18-photo.blend'),('wall-core-report.json','wall-core-report.json')]:shutil.copyfile(patch/old,out/new)
run([sys.executable,ROOT/'check_wall_core_glb.py','--baseline',baseline,'--candidate',out/'bund18-photo.glb','--output',out/'glb-preservation-report.json'])
run([sys.executable,ROOT/'compress_models.py','--input',out/'bund18-photo.glb','--output',out,'--gltfpack',a.gltfpack])
blend('audit_native.py','--input',out/'bund18-photo.blend','--output',out/'native-validation.json')
run([sys.executable,ROOT/'audit_assets.py','--directory',out])
project=a.project
if project is None:
 for ancestor in ROOT.parents:
  if (ancestor/'tools/qa/compare_model_compression.mjs').exists():project=ancestor;break
if project is not None:
 run(['node',project/'tools/qa/compare_model_compression.mjs',project,out/'bund18-photo.glb',out/'bund18-photo-web.glb',out/'compression-validation.json'])
print(json.dumps({'output':str(out),'geometry_and_photograph_checks':'passed','cpu_loader_check':bool(project),'browser_visual_validation':'separate acceptance step; source rebuilding does not launch a browser'}))
