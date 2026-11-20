"""Reopen the native gatehouse at the street corner and along the through-passage."""
from pathlib import Path
import sys,bpy
from mathutils import Vector
native,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=True,parents=True);bpy.ops.wm.open_mainfile(filepath=str(native.resolve()));s=bpy.context.scene;c=s.camera
s.render.resolution_x=760;s.render.resolution_y=550;s.cycles.samples=18
for name,eye,target,mm in [('tablet-and-gable',(1.3,-11.2,10.5),(0,0,10.28),46),('passage',(0.12,-5,1.54),(0,4.4,1.7),24)]:
 c.data.type='PERSP';c.data.lens=mm;c.location=Vector(eye);c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
