"""Render actual NE porch and NW double-height arch from native; never resave it. MIT."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--view',choices=['entrance','arch','passage'],required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);before=hashlib.sha256(a.native.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(a.native.resolve()));scene=bpy.context.scene;assert scene['candidate_id']=='huangpu-shanghai-municipal-council'
camera=scene.camera
position,target,lens={'entrance':((94,95,26),(53,53,10),55),'arch':((-88,94,24),(-56,56,10),55),'passage':((83,-79,10),(52,-47,6),55)}[a.view]
camera.location=position;target=Vector(target);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
scene.render.resolution_x=1100;scene.render.resolution_y=950;scene.render.resolution_percentage=100;scene.cycles.samples=24;scene.render.filepath=str(a.out.resolve());a.out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
assert hashlib.sha256(a.native.read_bytes()).hexdigest()==before
report={'id':scene['candidate_id'],'native_file_sha256':before,'source_raw_sha256':bpy.data.objects[scene['model_mesh_names'][0]]['source_raw_sha256'],'camera_position':list(camera.location),'camera_target':list(target),'lens_mm':lens,'samples':24,'file':a.out.name,'bytes':a.out.stat().st_size,'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'native_file_unchanged':True,'scope':'Detail of actual frozen model geometry: '+('NE concave main entrance, actual open folded porch and small glazed oriel with pierced balustrade.' if a.view=='entrance' else 'NW concave corner, actual double-height arched opening, paired Ionic columns and attic arch.' if a.view=='arch' else 'SE concave corner, actual unglazed arched passage to the inner court; plain internal closures and outlet profile are author estimates.')+' All dimensions are author estimates. This is a model render, not a source photograph.'}
a.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
