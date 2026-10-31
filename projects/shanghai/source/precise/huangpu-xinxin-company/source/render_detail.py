"""Render a low south detail of the saved Xinxin native file, without editing it."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--blend',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--samples',type=int,default=32);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
before=hashlib.sha256(a.blend.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(a.blend.resolve()))
scene=bpy.context.scene;assert scene['candidate_id']=='huangpu-xinxin-company'
camera=scene.camera;camera.location=(12,-40,23.5);target=Vector((1,-11.5,27.0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=52
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.cycles.samples=a.samples
scene.render.filepath=str(a.out.resolve());a.out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
assert hashlib.sha256(a.blend.read_bytes()).hexdigest()==before
report={'id':scene['candidate_id'],'native_file_sha256':before,'source_raw_sha256':bpy.data.objects[scene['model_mesh_names'][0]]['source_raw_sha256'],'camera_position':list(camera.location),'camera_target':list(target),'lens_mm':camera.data.lens,'samples':a.samples,'file':a.out.name,'bytes':a.out.stat().st_size,'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'native_file_unchanged':True,'scope':'Detail of final saved native geometry: upper windows and paired wall panels, true setback gallery, brackets and black railings, current open central tower. Not a source photograph.'}
a.out.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
