"""Run from Blender with the delivered blend open to check framing of every editable mesh."""
import bpy
import hashlib
import json
import sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

data=Path(bpy.data.filepath)
out=Path(sys.argv[sys.argv.index('--')+1])
assert out.suffix=='.json' and out.resolve()!=data.resolve()
scene=bpy.context.scene
camera=scene.camera
assert camera.name=='Shanghai American School entrance and bell tower' and camera.data.type=='ORTHO'
assert (scene.render.resolution_x,scene.render.resolution_y)==(1000,720)
meshes=[obj for obj in scene.objects if obj.type=='MESH']
projections=[world_to_camera_view(scene,camera,obj.matrix_world @ Vector(corner))
             for obj in meshes for corner in obj.bound_box]
bounds=[min(p.x for p in projections),min(p.y for p in projections),
        max(p.x for p in projections),max(p.y for p in projections)]
assert min(bounds[:2])>.04 and max(bounds[2:])<.96 and min(p.z for p in projections)>0,bounds
view=camera.matrix_world.to_quaternion() @ Vector((0,0,-1))
assert view.x<-.15 and view.y>.83 and view.z<0,list(view)
out.write_text(json.dumps({'native_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),
                           'scene_camera':camera.name,'resolution':[1000,720],
                           'bounds_normalized_xy':bounds,'camera_direction_xyz':list(view),
                           'mesh_count':len(meshes),'corners_checked':len(projections),'passed':True},
                          indent=2)+'\n')
