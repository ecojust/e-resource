"""Render the east return and entrance independently from the saved .blend.

blender -b -t 2 --python-exit-code 1 --python render-inspection.py -- MODEL.blend OUTPUT_DIR
"""
from pathlib import Path
import sys

import bpy
from mathutils import Vector

native, directory = map(Path, sys.argv[sys.argv.index('--')+1:])
directory.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(native.resolve()))
scene = bpy.context.scene
camera = scene.camera
scene.render.resolution_x, scene.render.resolution_y = 960, 680
scene.render.resolution_percentage = 100
# Use the same native studio and materials. Only the inspection camera moves.
for label, focus, offset, width in [
    ('north-east', (0,7,9.7), (-38,-58,17), 45.0),
    ('entrance', (0,-1.8,3.56), (.45,-26,1.15), 11.1),
]:
    camera.location = Vector(focus) + Vector(offset)
    camera.rotation_euler = (-Vector(offset)).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale = width
    scene.render.filepath = str((directory/(label+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
