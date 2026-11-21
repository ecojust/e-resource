"""Frame the complete bridge including all four lamps and both sidewalks."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_bridge(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # Use the same oblique sense as the dated 2010 overview.
    direction=Vector((-.55,-1.38,.49)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Raking light separates the openings, fascia, pavement and lamps.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((24,-35,47))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='四川路桥 · 河侧双步道'
    camera.data.name='三孔桥身正交相机'
    scene.cycles.samples=12
    scene.render.resolution_x=900
    scene.render.resolution_y=560
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the bridge deck, across-river openings and all four standards. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_bridge)
