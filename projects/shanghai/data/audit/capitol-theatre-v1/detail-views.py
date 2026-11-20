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
    ('entrance-tower',(-16.6,-.7,33.4),(-34,-30,34.7),23.2),
    ('theatre-door-and-relief',(-17.0,-5,8.4),(-34,-29,10.6),24.2)]:
    camera.location=Vector(eye)
    camera.rotation_euler=(Vector(focus)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=span
    scene.render.filepath=str((folder/(title+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
