"""Inspect the entrance fanlight and plaque, and the restored roof dormers on the west section."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
model,folder=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
scene=bpy.context.scene;scene.render.resolution_percentage=100
scene.render.resolution_x=680;scene.render.resolution_y=520;scene.cycles.samples=14
camera=scene.camera;camera.data.type='ORTHO';folder.mkdir(parents=True,exist_ok=True)
for name,focus,eye,span in [('entrance-fanlight',(.15,.0,5.05),(-1.2,-35,5.84),12.3),
                            ('west-shop-roof',(15.7,2.5,11.2),(10,-33,19),23.1)]:
    camera.location=Vector(eye)
    camera.rotation_euler=(Vector(focus)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=span;scene.render.filepath=str((folder/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
