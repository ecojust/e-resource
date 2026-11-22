"""Frame both rooftop lanterns, the recessed portico, and the two street wings."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_yangtze(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # The oblique street view retains the two roof pavilions, windows and recessed portico.
    direction=Vector((.27,-2.20,.38)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Oblique daylight preserves the window reveals on the light street elevation.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((-20,-29,43))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Yangtze Insurance, east Bund elevation'
    camera.data.name='扬子大楼'
    scene.render.resolution_x=640
    scene.render.resolution_y=780
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the east Bund elevation and paired attic pavilions. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_yangtze)
