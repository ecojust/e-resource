"""Frame the street window, its pediment and stone apron."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_windows(_):
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:
        return
    eye=Vector((4.,-14.,1.4)).normalized()
    rotation=(-eye).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (o.matrix_world @ Vector(p)) for o in scene.objects if o.type=='MESH' for p in o.bound_box]
    if not corners:
        return
    lo=Vector([min(v[i] for v in corners) for i in range(3)])
    hi=Vector([max(v[i] for v in corners) for i in range(3)])
    camera.rotation_euler=rotation.to_euler()
    camera.location=rotation @ ((lo+hi)/2)+eye*30
    camera.name='Anting street window and carved garland'
    camera.data.type='ORTHO'
    scene.render.resolution_x=800
    scene.render.resolution_y=640
    camera.data.ortho_scale=max((hi.x-lo.x)*1.13,(hi.y-lo.y)*800/640*1.13)
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(frame_windows)
