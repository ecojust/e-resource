"""Orient the editable project's cameras towards the photographed Beijing–Guizhou street corner."""
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from theatre_stucco import IMAGE,MATERIAL,uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_huangpu_theatre(*_):
    scene=bpy.context.scene
    material=bpy.data.materials[MATERIAL]
    image=bpy.data.images.load(str(IMAGE),check_existing=True)
    if not image.packed_file:
        image.pack()
    nodes=material.node_tree.nodes
    texture=nodes.get('Huangpu Theatre textured facade') or nodes.new('ShaderNodeTexImage')
    texture.name='Huangpu Theatre textured facade'
    texture.image=image
    texture.extension='EXTEND'
    material.node_tree.links.new(texture.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
    for obj in scene.objects:
        if obj.type!='MESH' or material.name not in obj.data.materials:
            continue
        mesh=obj.data
        layer=mesh.uv_layers.get('Huangpu mineral finish') or mesh.uv_layers.new(name='Huangpu mineral finish')
        for face in mesh.polygons:
            if mesh.materials[face.material_index]!=material:
                continue
            for index in face.loop_indices:
                world=obj.matrix_world@mesh.vertices[mesh.loops[index].vertex_index].co
                u,v=uv(world)
                layer.data[index].uv=u,1.-v
    camera=scene.camera
    if camera:
        camera.location=Vector((2,40,11.3))
        camera.rotation_euler=(Vector((0,6.0,9.55))-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO'
        camera.data.ortho_scale=25.5
        scene.render.resolution_x=860
        scene.render.resolution_y=750
        scene.cycles.samples=20
    for light in (o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN'):
        light.location=Vector((-16,35,36))
        light.rotation_euler=(Vector((0,6,9.55))-light.location).to_track_quat('-Z','Y').to_euler()
    for name,eye,target in [('Huangpu canopy and stairs',(1.3,16,1.60),(.25,5.5,1.55)),
                            ('Five glazed lights',(3,23,9.5),(.2,7.8,9.46))]:
        extra=bpy.data.objects.get(name)
        if not extra:
            extra=bpy.data.objects.new(name,bpy.data.cameras.new(name))
            scene.collection.objects.link(extra)
        extra.location=Vector(eye)
        extra.rotation_euler=(Vector(target)-extra.location).to_track_quat('-Z','Y').to_euler()
        extra.data.lens=35
bpy.app.handlers.save_pre.append(frame_huangpu_theatre)
