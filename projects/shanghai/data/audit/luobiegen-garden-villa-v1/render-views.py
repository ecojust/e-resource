"""Use the saved Blender scene, orthographic cameras and lighting for both exterior views."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

native,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(native.resolve()))
scene=bpy.context.scene;camera=scene.camera
scene.render.resolution_x=920;scene.render.resolution_y=660;scene.cycles.samples=32
for name,offset,direction in [('garden-oblique',(17,-33,14),(-12,-21,26)),('rear-roofs',(-16,31,27),(-12,20,29))]:
    target=Vector((0,.2,5.4));camera.location=target+Vector(offset)
    camera.rotation_euler=(-Vector(offset)).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=31.6
    sun=next(obj for obj in scene.objects if obj.type=='LIGHT' and obj.data.type=='SUN')
    sun.rotation_euler=(-Vector(direction)).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
