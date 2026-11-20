from pathlib import Path
import sys,bpy
from mathutils import Vector
filename,preview=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(filename))
s=bpy.context.scene;c=s.camera
target=Vector((0,.1,10.25))
c.location=Vector((-17.3,-36.5,5.1))
c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
c.data.type='PERSP';c.data.lens=45
s.render.resolution_x=680;s.render.resolution_y=600;s.render.resolution_percentage=100
s.cycles.samples=12
s.render.filepath=str(preview)
bpy.ops.render.render(write_still=True)
