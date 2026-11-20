"""Open the actual editable file to inspect the cast spandrels and the roof wells."""
from pathlib import Path
import sys

import bpy
from mathutils import Vector

model,folder=map(Path,sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
scene=bpy.context.scene
scene.render.resolution_percentage=100
scene.render.resolution_x=680
scene.render.resolution_y=520
scene.cycles.samples=12
camera=scene.camera
camera.data.type='ORTHO'
folder.mkdir(parents=True,exist_ok=True)
for filename,focus,eye,width in [
    ('west-door-and-ironwork',(13.4,.1,7.8),(9,-36,9.8),19.5),
    ('double-court-roof',(0,14,19),(10,36,86),59)]:
    camera.location=Vector(eye)
    camera.rotation_euler=(Vector(focus)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=width
    if filename=='double-court-roof':
        corners=[ob.matrix_world @ Vector(pt) for ob in scene.objects if ob.type=='MESH' for pt in ob.bound_box]
        rotation=camera.rotation_euler.to_quaternion()
        values=[[pt.dot(rotation @ Vector(axis)) for pt in corners] for axis in ((1,0,0),(0,1,0))]
        dx,dy=[(min(v)+max(v))/2 for v in values]
        right=rotation @ Vector((1,0,0));up=rotation @ Vector((0,1,0))
        camera.location+=right*(dx-camera.location.dot(right))+up*(dy-camera.location.dot(up))
        camera.data.ortho_scale=1.09*max(max(values[0])-min(values[0]),(max(values[1])-min(values[1]))*680/520)
    scene.render.filepath=str((folder/(filename+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
