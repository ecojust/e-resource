"""Render the same close architectural view from an old or revised editable scene using Cycles on the CPU."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
source,out=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(source))
record=json.loads((root/'geometry-input.json').read_bytes())
points=[Vector((x,y,0))for x,y in record['polygon_local_east_north']]
start,end=points[9:11];t=(end-start).normalized();normal=Vector((t.y,-t.x,0));mid=(start+end)/2
target=mid+t*(-.45)+Vector((0,0,7.16))
scene=bpy.context.scene
cam=scene.camera
cam.location=target+normal*18-t*2.8+Vector((0,0,1.15))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=10.9
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=10
scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=1
scene.render.resolution_x=792;scene.render.resolution_y=330;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out)
bpy.ops.render.render(write_still=True)
