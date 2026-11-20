"""Reopen the completed native model; inspect the north-side entry and roof from a second angle."""
from pathlib import Path
import sys

import bpy
from mathutils import Vector

native, output = map(Path, sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(native.resolve()))
s=bpy.context.scene
cam=s.camera
target=Vector((0,1.0,4.45))
cam.location=target+Vector((-13.,36.,15.))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.ortho_scale=27.5
sun=next(ob for ob in s.objects if ob.type=='LIGHT' and ob.data.type=='SUN')
sun.location=(8,22,27)
sun.rotation_euler=(-sun.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=810
s.render.resolution_y=580
s.render.resolution_percentage=100
s.cycles.samples=20
s.render.filepath=str(output.resolve())
bpy.ops.render.render(write_still=True)
