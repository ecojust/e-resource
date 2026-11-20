"""Fit the editable camera to both street wings and the signed southeast entrance."""
import sys
from pathlib import Path

import bpy
from mathutils import Vector

blend, output = map(Path,sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()))
scene=bpy.context.scene
camera=scene.camera
camera.name="Tiantong and North Sichuan Road corner"
direction=Vector((1.42,-1,.18)).normalized()
rotation=(-direction).to_track_quat("-Z","Y")
right=rotation @ Vector((1,0,0))
up=rotation @ Vector((0,1,0))
points=[ob.matrix_world @ Vector(corner) for ob in scene.objects if ob.type=="MESH" for corner in ob.bound_box]
minmax=lambda axis:(min(p.dot(axis) for p in points),max(p.dot(axis) for p in points))
x0,x1=minmax(right);y0,y1=minmax(up);z0,z1=minmax(direction)
centre=right*((x0+x1)/2)+up*((y0+y1)/2)+direction*((z0+z1)/2)
camera.location=centre+direction*130
camera.rotation_euler=rotation.to_euler()
scene.render.resolution_x=1120
scene.render.resolution_y=900
camera.data.ortho_scale=1.13*max(x1-x0,(y1-y0)*1120/900)
scene.render.filepath="//"+output.name
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()))
bpy.context.scene.render.filepath=str(output.resolve())
bpy.ops.render.render(write_still=True)
