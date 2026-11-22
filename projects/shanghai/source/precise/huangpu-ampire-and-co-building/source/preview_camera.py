"""Frame the rounded wings and the oriel on Yuanmingyuan Road."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_ampire(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # Eye looking west from the pedestrian street.
    direction=Vector((.12,-1.58,.13)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Cross light picks out the brick pilasters and projecting oriel.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((24,-35,47))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='安培洋行 · 圆明园路'
    camera.data.name='街面正交相机'
    scene.cycles.samples=12
    scene.render.resolution_x=900
    scene.render.resolution_y=560
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed both rounded wings, the oriel and the central doorway. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_ampire)
