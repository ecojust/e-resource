"""Install the Shen Bao scene camera before Blender first saves the editable file."""
import bpy
from bpy.app.handlers import persistent
from mathutils import Vector


@persistent
def fit_office_camera(_scene):
    scene=bpy.context.scene
    camera=scene.camera
    if camera is None:
        return
    camera.name='Hankou and Shandong roads, Shen Bao corner entrance'
    direction=Vector((.11,-1,.12)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    right=rotation @ Vector((1,0,0))
    up=rotation @ Vector((0,1,0))
    points=[obj.matrix_world @ Vector(p) for obj in scene.objects if obj.type=='MESH' for p in obj.bound_box]
    def extent(axis):
        return min(p.dot(axis) for p in points),max(p.dot(axis) for p in points)
    x0,x1=extent(right);y0,y1=extent(up);z0,z1=extent(direction)
    center=right*((x0+x1)/2)+up*((y0+y1)/2)+direction*((z0+z1)/2)
    camera.location=center+direction*95
    camera.rotation_euler=rotation.to_euler()
    scene.render.resolution_x=960
    scene.render.resolution_y=850
    camera.data.ortho_scale=1.13*max(x1-x0,(y1-y0)*960/850)


bpy.app.handlers.save_pre.append(fit_office_camera)
