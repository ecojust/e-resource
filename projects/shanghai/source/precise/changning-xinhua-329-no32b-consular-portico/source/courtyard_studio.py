"""Set up the native courtyard scene for inspection and ordinary camera renders."""
import bpy
from mathutils import Vector

def set_up(scene):
    scene.name='新华路329弄32号乙庭院'
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=1
    scene.render.resolution_x=900
    scene.render.resolution_y=700
    scene.render.resolution_percentage=100
    world=scene.world or bpy.data.worlds.new('Courtyard daylight')
    scene.world=world
    world.use_nodes=True
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    bg.inputs['Color'].default_value=(.71,.76,.80,1)
    bg.inputs['Strength'].default_value=.67
    lights=bpy.data.collections.new('庭院展示照明')
    scene.collection.children.link(lights)
    for name,position,power,size,tint in [
        ('Courtyard daylight',(-8,-13,18),7800,10,(1,.91,.80)),
        ('Roof skylight',(8,4,16),4300,9,(.81,.89,1))]:
        light=bpy.data.lights.new(name,'AREA')
        light.energy=power;light.shape='DISK';light.size=size;light.color=tint
        obj=bpy.data.objects.new(name,light);lights.objects.link(obj);obj.location=position
        obj.rotation_euler=(Vector((0,3,5))-obj.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU';scene.cycles.samples=24
    scene.cycles.use_denoising=False
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.region_3d.view_perspective='CAMERA'
                space.shading.color_type='MATERIAL'
    bpy.context.preferences.filepaths.save_version=0
    if hasattr(bpy.context.preferences.filepaths,'file_preview_type'):
        bpy.context.preferences.filepaths.file_preview_type='NONE'
    bpy.context.view_layer.update()
