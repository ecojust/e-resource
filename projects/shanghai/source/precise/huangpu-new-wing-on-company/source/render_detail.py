"""Render the actual NE thermometer and continuous facade, without hiding geometry."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--samples',type=int,default=20)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);s=bpy.context.scene
assert s['candidate_id']=='huangpu-new-wing-on-company'
t=Vector((1.80,25.35,26.));s.camera.location=t+Vector((.787415899,.616422098,.05))*65
s.camera.rotation_euler=(t-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=900;s.render.resolution_y=1000;s.cycles.samples=a.samples
a.out.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(a.out.resolve());bpy.ops.render.render(write_still=True)
data={'file':a.out.name,'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),
 'raw_sha256':bpy.data.objects[s['model_mesh_names'][0]]['source_raw_sha256'],
 'camera':list(s.camera.location),'target':list(t),
 'scope':'Actual Blender close view of the complete existing model. Cropped architectural detail; no object visibility or geometry changes. The temperature scale has no numeric readings.'}
a.out.with_suffix('.json').write_text(json.dumps(data,indent=2)+'\n')
