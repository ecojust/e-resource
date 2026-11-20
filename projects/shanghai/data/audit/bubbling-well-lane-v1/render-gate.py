"""Reopen the native gatehouse at the street corner and along the through-passage."""
from pathlib import Path
import sys,bpy
from mathutils import Vector
native,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=True,parents=True);bpy.ops.wm.open_mainfile(filepath=str(native.resolve()));s=bpy.context.scene;c=s.camera
s.render.resolution_x=850;s.render.resolution_y=660;s.cycles.samples=28
for name,eye,target,mm in [('street-oblique',(8,-23,7.9),(0,1.5,6.85),32),('passage',(0.68,-4.6,1.79),(0,4.4,2.04),21)]:
 c.data.type='PERSP';c.data.lens=mm;c.location=Vector(eye);c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
