"""Frame the garden gate, balustrade and upper iron terrace at 393 Yanan Road."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_loggia(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    direction=Vector((4.4,-15.7,2.6)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((35,-25,42))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='393 Yanan Road garden loggia'
    scene.render.resolution_x=820
    scene.render.resolution_y=820
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the 393 Yanan Road garden loggia',scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_loggia)
