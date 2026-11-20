"""Render the three-bay museum entrance and two wing heights from the editable riverfront office."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
model,folder=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
scene=bpy.context.scene;scene.render.resolution_percentage=100
scene.render.resolution_x=700;scene.render.resolution_y=520;scene.cycles.samples=14
camera=scene.camera;camera.data.type='ORTHO';folder.mkdir(parents=True,exist_ok=True)
for name,focus,eye,span in [('archive-portal',(0,0,4.60),(4,-39,6),23),
                            ('riverfront-crown',(0,5,36.1),(17,-43,49),34.5)]:
    camera.location=Vector(eye)
    camera.rotation_euler=(Vector(focus)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=span;scene.render.filepath=str((folder/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
