"""Set the Blender preview beneath the one-bay archival ceiling."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def set_preview(_):
    scene=bpy.context.scene
    camera=scene.camera
    target=Vector((0,0,1.05))
    camera.name='Underside of archival ceiling'
    camera.location=target+Vector((2.7,-4.5,-9.1))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=900
    scene.render.resolution_y=690
    camera.data.type='ORTHO'
    camera.data.ortho_scale=8.25
    for lamp in scene.objects:
        if lamp.type!='LIGHT':
            continue
        lamp.location=Vector((lamp.location.x,lamp.location.y,-abs(lamp.location.z)))
        lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
    scene['source_view']='Looking up at the single photographed round ceiling panel and its coved returns.'

bpy.app.handlers.save_pre.append(set_preview)
