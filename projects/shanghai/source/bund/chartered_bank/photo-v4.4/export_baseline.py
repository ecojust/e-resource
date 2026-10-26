"""Reproduce the frozen v4.3 raw GLB from its independently stored native file."""
import argparse,bpy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
p=ROOT/'baseline/bund18-v4.3.blend';provenance=json.loads((ROOT/'baseline/provenance.json').read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==provenance['native_sha256']
bpy.ops.wm.open_mainfile(filepath=str(p));a.output.parent.mkdir(parents=True,exist_ok=True)
model=bpy.data.collections['MODEL_Bund18_Chartered_Bank'];bpy.ops.object.select_all(action='DESELECT')
for ob in model.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=next(iter(model.objects))
bpy.ops.export_scene.gltf(filepath=str(a.output),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_copyright=provenance['asset']['copyright'])
sha=hashlib.sha256(a.output.read_bytes()).hexdigest();print(json.dumps({'raw_bytes':a.output.stat().st_size,'raw_sha256':sha,'expected_sha256':provenance['raw_sha256']}));assert sha==provenance['raw_sha256'],'Use Blender 4.3.2 with glTF exporter 4.3.47 to reproduce this frozen baseline.'
