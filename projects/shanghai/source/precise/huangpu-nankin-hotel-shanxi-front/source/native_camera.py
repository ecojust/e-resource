"""Orient the editable project's cameras towards the photographed west street frontage."""
import bpy
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_west_facade(*_):
    scene=bpy.context.scene
    camera=scene.camera
    if camera:
        camera.location=Vector((56,47,16))
        camera.rotation_euler=(Vector((45.8,0,11.1))-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO'
        camera.data.ortho_scale=29.0
        scene.render.resolution_x=860
        scene.render.resolution_y=750
        scene.cycles.samples=20
    for light in (o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN'):
        light.location=Vector((26,35,46))
        light.rotation_euler=(Vector((45,0,8))-light.location).to_track_quat('-Z','Y').to_euler()
    for name,eye,target in [('Street doors and postal box',(43,13,3),(44,0,2.65)),
                            ('Angled balconies and ironwork',(49,10,12),(46.5,.4,13.15))]:
        extra=bpy.data.objects.get(name)
        if not extra:
            extra=bpy.data.objects.new(name,bpy.data.cameras.new(name))
            scene.collection.objects.link(extra)
        extra.location=Vector(eye)
        extra.rotation_euler=(Vector(target)-extra.location).to_track_quat('-Z','Y').to_euler()
        extra.data.lens=35
bpy.app.handlers.save_pre.append(frame_west_facade)
