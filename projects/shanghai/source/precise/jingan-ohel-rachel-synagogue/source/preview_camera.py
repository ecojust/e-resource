"""Frame the east portico and long row of round-headed side windows."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_ohel_rachel(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # This angle includes the portico, its setback, the long windows and the roof.
    direction=Vector((1.40,-2.65,1.10)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Light the ionic volutes from the entrance courtyard.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((35,-25,42))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Ohel Rachel portico and side windows'
    scene.render.resolution_x=760
    scene.render.resolution_y=570
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the Ohel Rachel portico and side windows',scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_ohel_rachel)
