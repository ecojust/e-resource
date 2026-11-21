"""Frame the clipped facade at 115 Wukang Road."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_clipped_corner(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # Look from the street crossing toward the recessed window and short returns.
    direction=Vector((.12,-2.0,-.24)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Raking light on the paired stepped corbels.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((-20,-29,43))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Midget Apartments clipped corner'
    camera.data.name='密丹公寓街角立面'
    scene.render.resolution_x=790
    scene.render.resolution_y=890
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the Wukang and Hunan Road corner. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_clipped_corner)
