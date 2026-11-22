"""Frame the Jiujiang arcades, roof openings and east corner."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_street_front(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # The municipal street photo looks northwest from the junction toward the rounded end.
    direction=Vector((.72,-3.25,.55)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Raking light separates the curved arch heads and recessed shopfronts.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((-22,-45,39))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Carlowitz and Co., Jiujiang Road arcade'
    scene.render.resolution_x=1120
    scene.render.resolution_y=700
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.09*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed Jiujiang Road elevation',scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_street_front)
