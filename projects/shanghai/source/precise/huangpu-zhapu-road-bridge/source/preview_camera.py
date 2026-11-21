"""Frame the three openings and both exposed cutwaters from the river."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_bridge(_):
    scene = bpy.context.scene
    camera = scene.camera
    if not camera:
        return
    direction = Vector((-1.9, -.65, .52)).normalized()
    rotation = (-direction).to_track_quat('-Z', 'Y')
    corners = [rotation.inverted() @ (ob.matrix_world @ Vector(v))
               for ob in scene.objects if ob.type == 'MESH' for v in ob.bound_box]
    lower = Vector([min(v[i] for v in corners) for i in range(3)])
    upper = Vector([max(v[i] for v in corners) for i in range(3)])
    camera.location = rotation @ ((lower + upper) / 2) + 180 * direction
    camera.rotation_euler = rotation.to_euler()
    camera.name = '乍浦路桥 · 上游三跨'
    camera.data.name = '乍浦路桥滨河正交相机'
    for light in scene.objects:
        if light.type == 'LIGHT' and light.data.type == 'SUN':
            light.location = Vector((-45, -35, 58))
            light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
    scene.cycles.samples = 12
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 520
    camera.data.ortho_scale = 1
    frame = camera.data.view_frame(scene=scene)
    width = max(v.x for v in frame) - min(v.x for v in frame)
    height = max(v.y for v in frame) - min(v.y for v in frame)
    camera.data.ortho_scale = 1.11 * max((upper.x-lower.x)/width, (upper.y-lower.y)/height)
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(frame_bridge)
