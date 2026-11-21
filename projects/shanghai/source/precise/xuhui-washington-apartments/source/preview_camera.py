"""Frame the Washington Apartments corner and Gaoan Road facade."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_street_corner(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # View from the junction across the clipped corner and the long Gaoan Road frontage.
    direction=Vector((-1.27,-1.61,.38)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Light the entrance relief and the facets of the oriels.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((-30,-32,51))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Washington Apartments street corner and Gaoan Road entrance'
    camera.data.name='华盛顿公寓街角与高安路廊门'
    scene.render.resolution_x=1200
    scene.render.resolution_y=680
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed Washington Apartments street corner and Gaoan Road. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_street_corner)
