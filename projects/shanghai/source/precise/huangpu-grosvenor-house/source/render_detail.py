"""Render stepped terrace and crown detail from the frozen editable native without saving it. MIT."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);before=hashlib.sha256(a.native.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(a.native.resolve()));scene=bpy.context.scene;assert scene['candidate_id']=='huangpu-grosvenor-house'
camera=scene.camera;camera.location=(-48,-83,88);target=Vector((-4,-1,65));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=60
scene.render.resolution_x=1200;scene.render.resolution_y=850;scene.render.resolution_percentage=100;scene.cycles.samples=24;scene.render.filepath=str(a.out.resolve());a.out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
assert hashlib.sha256(a.native.read_bytes()).hexdigest()==before
report={'id':scene['candidate_id'],'native_file_sha256':before,'source_raw_sha256':bpy.data.objects[scene['model_mesh_names'][0]]['source_raw_sha256'],'camera_position':list(camera.location),'camera_target':list(target),'lens_mm':camera.data.lens,'samples':24,'file':a.out.name,'bytes':a.out.stat().st_size,'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'native_file_unchanged':True,'scope':'Detail of actual frozen model geometry: actual stepped roof terraces, continuous pale central fins between recessed windows, and deeply recessed crown grooves. Dimensions and floor datums are author estimates. This is a model render, not a source photograph.'}
a.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
