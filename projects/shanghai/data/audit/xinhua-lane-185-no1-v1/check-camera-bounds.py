"""Check the saved native camera against every editable object's projected bounds.

blender -b <house.blend> -t 1 --python-exit-code 1 --python check-camera-bounds.py -- <report.json>
"""
import json
import sys
from hashlib import sha256
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

scene = bpy.context.scene
camera = scene.camera
objects = [o for o in scene.objects if o.type == 'MESH']
points = [world_to_camera_view(scene, camera, o.matrix_world @ Vector(corner))
          for o in objects for corner in o.bound_box]
xs = [p.x for p in points]
ys = [p.y for p in points]
assert min(p.z for p in points) > 0
margins = {'left': min(xs), 'right': 1-max(xs), 'bottom': min(ys), 'top': 1-max(ys)}
assert min(margins.values()) > .035, margins
source = Path(bpy.data.filepath)
out = Path(sys.argv[sys.argv.index('--')+1])
out.write_text(json.dumps({'blend_sha256': sha256(source.read_bytes()).hexdigest(),
                           'editable_objects': len(objects), 'bound_corners': len(points),
                           'pixels': [scene.render.resolution_x, scene.render.resolution_y],
                           'normalized_image_margins': margins}, indent=2)+'\n')
