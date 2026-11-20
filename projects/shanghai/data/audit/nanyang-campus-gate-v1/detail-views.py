"""Render the gate’s painted timberwork, campus windows and free-standing guardian."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
model,folder=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
scene=bpy.context.scene;scene.render.resolution_percentage=100
scene.render.resolution_x=700;scene.render.resolution_y=540;scene.cycles.samples=16
camera=scene.camera;camera.data.type='ORTHO';folder.mkdir(parents=True,exist_ok=True)
for name,focus,eye,span in [('east-painted-gate',(2.5,1.1,4.09),(3.6,-20,4.13),6.70),
                            ('stone-guardian',(-4.97,-1.12,1.49),(-7.70,-10.9,3.36),3.7),
                            ('campus-reverse',(0,9.8,4.22),(-.2,34,6.5),17.95)]:
    camera.location=Vector(eye)
    camera.rotation_euler=(Vector(focus)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=span;scene.render.filepath=str((folder/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
