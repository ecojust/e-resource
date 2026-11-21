"""Frame the round street facade and the upper drum before the editable file is saved."""
import bpy
from bpy.app.handlers import persistent
from mathutils import Vector

@persistent
def tower_camera(*_):
    scene=bpy.context.scene
    camera=scene.camera
    if camera is None:
        return
    corners=[ob.matrix_world@Vector(v) for ob in scene.objects if ob.type=='MESH' for v in ob.bound_box]
    lower=Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    upper=Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    direction=Vector((.13,-1,.075)).normalized()
    target=(lower+upper)*.5
    camera.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
    right=camera.rotation_euler.to_matrix()@Vector((1,0,0))
    up=camera.rotation_euler.to_matrix()@Vector((0,1,0))
    us=[(v-target).dot(right) for v in corners]
    vs=[(v-target).dot(up) for v in corners]
    target+=right*((min(us)+max(us))*.5)+up*((min(vs)+max(vs))*.5)
    scene.render.resolution_x=820
    scene.render.resolution_y=820
    camera.name='Round tower at 102 Guangdong Road'
    camera.data.ortho_scale=max(max(us)-min(us),max(vs)-min(vs))*1.12
    camera.location=target+direction*43
    scene['preview_camera_scope']='Flat southwest portal, three curved window bays and roof railing'

bpy.app.handlers.save_pre.append(tower_camera)
