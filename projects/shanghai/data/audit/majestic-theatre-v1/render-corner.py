"""Render the street corner and a roof overview from a reopened native project."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
native,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=str(native.resolve()))
s=bpy.context.scene
cam=s.camera
for name,target,offset,size,height in [
        ('street-corner',(-21.40,-27.70,9.2),(-6.7,-33,-5.2),28,660),
        ('roof',(-.5,.5,8.),(-40,-70,46),90,535)]:
    cam.location=Vector(target)+Vector(offset)
    cam.rotation_euler=(-Vector(offset)).to_track_quat('-Z','Y').to_euler()
    s.render.resolution_x=840
    s.cycles.samples=32
    s.render.resolution_y=height
    cam.data.ortho_scale=size
    s.render.filepath=str((out/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
