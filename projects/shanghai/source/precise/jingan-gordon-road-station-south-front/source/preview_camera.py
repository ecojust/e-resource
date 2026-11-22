"""Frame the south courtyard gable from the south courtyard."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mathutils import Vector


@bpy.app.handlers.persistent
def frame_street_front(_):
    scene = bpy.context.scene
    camera = scene.camera
    if not camera:
        return
    # A small lateral offset shows the open gallery and its short return.
    direction = Vector((.50, -5.55, .70)).normalized()
    rotation = (-direction).to_track_quat('-Z', 'Y')
    corners = [rotation.inverted() @ (obj.matrix_world @ Vector(coord))
               for obj in scene.objects if obj.type == 'MESH' for coord in obj.bound_box]
    if not corners:
        return
    lower = Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper = Vector([max(corner[i] for corner in corners) for i in range(3)])
    center = rotation @ ((lower + upper) / 2)
    camera.location = center + direction * 130
    camera.rotation_euler = rotation.to_euler()
    # Morning sun crosses the projecting timber grille from the south.
    for light in scene.objects:
        if light.type == 'LIGHT' and light.data.type == 'SUN':
            light.location = Vector((-22, -45, 39))
            light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
    camera.name = 'East courtyard of Xiangguang Hall'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 630
    camera.data.ortho_scale = 1
    frame = camera.data.view_frame(scene=scene)
    unit_width = max(v.x for v in frame) - min(v.x for v in frame)
    unit_height = max(v.y for v in frame) - min(v.y for v in frame)
    camera.data.ortho_scale = 1.09 * max((upper.x - lower.x) / unit_width,
                                         (upper.y - lower.y) / unit_height)
    bpy.context.view_layer.update()
    print('Framed the south courtyard gable', scene.render.resolution_x,
          scene.render.resolution_y, camera.data.ortho_scale)


bpy.app.handlers.save_pre.append(frame_street_front)
