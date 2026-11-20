"""Reopen the delivered blend and photograph the central portal at pedestrian height."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

model,output=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
scene=bpy.context.scene
camera=scene.camera
target=Vector((0,-.1,9.8))
camera.location=Vector((-4.25,-28.5,5.1))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'
camera.data.ortho_scale=24
scene.render.resolution_x,scene.render.resolution_y=760,820
scene.cycles.samples=20
scene.render.filepath=str(output.resolve())
bpy.ops.render.render(write_still=True)
