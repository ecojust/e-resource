"""Frame the five roof domes from the corner of Xinle and Xiangyang North roads."""
import bpy
from mathutils import Vector


@bpy.app.handlers.persistent
def frame_street_corner(_):
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        return
    direction = Vector((.59, 1.0, .37)).normalized()
    rotation = (-direction).to_track_quat('-Z', 'Y')
    inverse = rotation.inverted()
    points = [inverse @ (obj.matrix_world @ Vector(point))
              for obj in scene.objects if obj.type == 'MESH' for point in obj.bound_box]
    if not points:
        return
    low = Vector([min(point[i] for point in points) for i in range(3)])
    high = Vector([max(point[i] for point in points) for i in range(3)])
    camera.location = rotation @ ((low + high) / 2) + direction * 100
    camera.rotation_euler = rotation.to_euler()
    camera.name = 'Xinle Road entrance and east window elevation'
    scene.render.resolution_x = 820
    scene.render.resolution_y = 900
    camera.data.ortho_scale = 1
    corners = camera.data.view_frame(scene=scene)
    width = max(p.x for p in corners) - min(p.x for p in corners)
    height = max(p.y for p in corners) - min(p.y for p in corners)
    camera.data.ortho_scale = 1.10 * max((high.x-low.x)/width, (high.y-low.y)/height)
    for obj in scene.objects:
        if obj.type == 'LIGHT' and obj.data.type == 'SUN':
            obj.location = Vector((19, 35, 43))
            obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()


bpy.app.handlers.save_pre.append(frame_street_corner)
