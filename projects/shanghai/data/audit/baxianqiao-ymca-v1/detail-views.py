"""Reopen the delivered native scene for two independent detail views."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

model,folder=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
scene=bpy.context.scene
scene.render.resolution_percentage=100
scene.render.resolution_x=680
scene.render.resolution_y=520
scene.cycles.samples=14
camera=scene.camera
camera.data.type='ORTHO'
folder.mkdir(parents=True,exist_ok=True)
for title,focus,eye,span in [
    ('eaves',(-11.8,1.1,30.13),(-28,-32,28.5),19.2),
    ('entrance',(0,-.20,4.8),(-2.5,-27,4.8),12.8)]:
    camera.location=Vector(eye)
    camera.rotation_euler=(Vector(focus)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=span
    scene.render.filepath=str((folder/(title+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
