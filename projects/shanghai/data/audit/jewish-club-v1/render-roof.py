"""Reopen the packaged .blend and observe the junctions of the south roof from the rear."""
from pathlib import Path
import sys,bpy
from mathutils import Vector
native,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.parent.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=str(native.resolve()))
scene=bpy.context.scene
camera=scene.camera
scene.render.resolution_x=850
scene.render.resolution_y=580
scene.cycles.samples=30
camera.data.type='ORTHO'
camera.data.ortho_scale=64.5
camera.location=Vector((28,60,38))
camera.rotation_euler=(Vector((0,6.2,5.9))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(out.resolve())
bpy.ops.render.render(write_still=True)
