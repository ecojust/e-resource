"""Frame the two street elevations and corner entrance in the editable Blender scene."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_streets(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # Look toward both streets from the northwestern corner shown in the 2014 photograph.
    direction=Vector((.64,-1.12,.185)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # The common studio sun is southwest. Light the two documented street
    # elevations from the northwest while retaining the studio's original power.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((24,-35,47))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='East Daming Road and corner pavilion'
    scene.render.resolution_x=1000
    scene.render.resolution_y=720
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the complete bank and both street elevations:',scene.render.resolution_x,scene.render.resolution_y,camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_streets)
