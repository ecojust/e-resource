"""Inspect the Nanjing Road stair end and the two entrances on the curved bank frontage."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
model,folder=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
scene=bpy.context.scene;scene.render.resolution_percentage=100
scene.render.resolution_x=680;scene.render.resolution_y=520;scene.cycles.samples=14
camera=scene.camera;camera.data.type='ORTHO';folder.mkdir(parents=True,exist_ok=True)
for name,focus,eye,span in [('bank-and-residential-doors',(14.55,-1.10,3.70),(38.2,-22.8,4.56),18.9),
                            ('tower-and-terrace',(4.88,2.31,30.35),(14.0,-32,40),32.8)]:
    camera.location=Vector(eye)
    camera.rotation_euler=(Vector(focus)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=span;scene.render.filepath=str((folder/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
