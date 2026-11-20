"""Install the Yueyang Road stepped apartment row scene camera before Blender first saves the editable file."""
import bpy
from bpy.app.handlers import persistent
from mathutils import Vector


@persistent
def fit_yueyang_camera(_scene):
    scene=bpy.context.scene
    camera=scene.camera
    if camera is None:
        return
    camera.name='Yueyang Road stepped apartment row street elevation'
    direction=Vector((-.52,-1,.16)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    right=rotation @ Vector((1,0,0))
    up=rotation @ Vector((0,1,0))
    points=[obj.matrix_world @ Vector(p) for obj in scene.objects if obj.type=='MESH' for p in obj.bound_box]
    def extent(axis):
        return min(p.dot(axis) for p in points),max(p.dot(axis) for p in points)
    x0,x1=extent(right);y0,y1=extent(up);z0,z1=extent(direction)
    center=right*((x0+x1)/2)+up*((y0+y1)/2)+direction*((z0+z1)/2)
    camera.location=center+direction*155
    camera.rotation_euler=rotation.to_euler()
    scene.render.resolution_x=980
    scene.render.resolution_y=735
    camera.data.ortho_scale=1.16*max(x1-x0,(y1-y0)*980/735)


bpy.app.handlers.save_pre.append(fit_yueyang_camera)
