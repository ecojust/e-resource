"""Render the school plaque, open galleries and paired windows of the 1913 west end."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
model,folder=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
scene=bpy.context.scene;scene.render.resolution_percentage=100
scene.render.resolution_x=680;scene.render.resolution_y=520;scene.cycles.samples=14
camera=scene.camera;camera.data.type='ORTHO';folder.mkdir(parents=True,exist_ok=True)
for name,focus,eye,span in [('courtyard-gallery',(0,.4,9.2),(-15,-34.0,12.2),31.5),
                            ('west-street-end',(-41.4,11.6,7.3),(-75,7,11.4),29.8)]:
    camera.location=Vector(eye)
    camera.rotation_euler=(Vector(focus)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=span;scene.render.filepath=str((folder/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
