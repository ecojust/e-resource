"""View the gate from the public Yuyuan Road pavement."""
import bpy
from mathutils import Vector


@bpy.app.handlers.persistent
def frame_lane_entrance(_):
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        return
    direction = Vector((.17, -1.0, .13)).normalized()
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
    camera.name = '愚园路361弄北门'
    camera.data.name = '愚谷邨北弄门外侧相机'
    scene.render.resolution_x = 1050
    scene.render.resolution_y = 660
    camera.data.ortho_scale = 1
    corners = camera.data.view_frame(scene=scene)
    width = max(p.x for p in corners) - min(p.x for p in corners)
    height = max(p.y for p in corners) - min(p.y for p in corners)
    camera.data.ortho_scale = 1.10 * max((high.x-low.x)/width, (high.y-low.y)/height)
    for obj in scene.objects:
        if obj.type == 'LIGHT' and obj.data.type == 'SUN':
            obj.location = Vector((18, -30, 40))
            obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()


bpy.app.handlers.save_pre.append(frame_lane_entrance)
