"""Store the glass cover transparency and two additional camera positions in the blend."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def before_save(_):
    scene=bpy.context.scene
    skin=bpy.data.materials.get('Trust skylight grey weather glass')
    if skin:
        shader=skin.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Alpha'].default_value=.27
        skin.diffuse_color=(*skin.diffuse_color[:3],.27)
    cam=scene.camera
    if cam:
        target=Vector((10.62,1.6,15.2))
        cam.location=Vector((27.,-75.,23.5))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.ortho_scale=43.7
        cam.name='Beijing Road elevation'
        scene.render.resolution_x=900
        scene.render.resolution_y=760
        scene.cycles.samples=16
    for title,position,aim,lens in [
        ('Banking hall glazed ceiling',(8.1,13.2,4.23),(8.8,19.3,10.72),22),
        ('Open lightwell and pitched cover',(7.60,27.0,23.78),(9.1,16.0,12.32),29)]:
        camera=bpy.data.objects.get(title)
        if not camera:
            camera=bpy.data.objects.new(title,bpy.data.cameras.new(title))
            scene.collection.objects.link(camera)
        camera.location=Vector(position)
        camera.rotation_euler=(Vector(aim)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.lens=lens
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(before_save)
