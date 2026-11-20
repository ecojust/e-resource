"""Reopen the delivered .blend and render an archival court angle plus the opposite garden elevation."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
native,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=str(native.resolve()))
scene=bpy.context.scene;camera=scene.camera
scene.render.resolution_x=800;scene.render.resolution_y=820;scene.cycles.samples=32
for name,focus,offset,width in [
        ('southwest', (0,0,21), (4,-70,24),48),
        ('garden', (0,1,20.3), (17,64,18),52)]:
    if name=='garden':
        sun=next(obj for obj in scene.objects if obj.type=='LIGHT' and obj.data.type=='SUN')
        sun.rotation_euler=(-Vector((-23,36,48))).to_track_quat('-Z','Y').to_euler()
    camera.location=Vector(focus)+Vector(offset)
    camera.rotation_euler=(-Vector(offset)).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=width
    scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
