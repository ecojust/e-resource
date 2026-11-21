"""Orient the editable project's cameras towards the photographed north street frontage."""
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from taishan_brick import IMAGE, MATERIAL, uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_school_facade(*_):
    scene=bpy.context.scene
    material=bpy.data.materials[MATERIAL]
    image=bpy.data.images.load(str(IMAGE),check_existing=True)
    if not image.packed_file:
        image.pack()
    nodes=material.node_tree.nodes
    texture=nodes.get('Original Taishan brick bond') or nodes.new('ShaderNodeTexImage')
    texture.name='Original Taishan brick bond'
    texture.image=image
    texture.extension='EXTEND'
    material.node_tree.links.new(texture.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
    for obj in scene.objects:
        if obj.type!='MESH' or material.name not in obj.data.materials:
            continue
        mesh=obj.data
        layer=mesh.uv_layers.get('Jiujiang brickwork') or mesh.uv_layers.new(name='Jiujiang brickwork')
        for face in mesh.polygons:
            if mesh.materials[face.material_index]!=material:
                continue
            for index in face.loop_indices:
                world=obj.matrix_world@mesh.vertices[mesh.loops[index].vertex_index].co
                u,v=uv(world)
                layer.data[index].uv=u,1.-v
    camera=scene.camera
    if camera:
        camera.location=Vector((49,56,17))
        camera.rotation_euler=(Vector((37.7,0,11.8))-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO'
        camera.data.ortho_scale=39.0
        scene.render.resolution_x=860
        scene.render.resolution_y=750
        scene.cycles.samples=20
    for light in (o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN'):
        light.location=Vector((26,35,46))
        light.rotation_euler=(Vector((37,0,9))-light.location).to_track_quat('-Z','Y').to_euler()
    for name,eye,target in [('Pointed entrance and plaques',(38.9,12.5,3.3),(37.7,0,2.9)),
                            ('East gable stonework',(51,13,19),(48.6,.45,19.8))]:
        extra=bpy.data.objects.get(name)
        if not extra:
            extra=bpy.data.objects.new(name,bpy.data.cameras.new(name))
            scene.collection.objects.link(extra)
        extra.location=Vector(eye)
        extra.rotation_euler=(Vector(target)-extra.location).to_track_quat('-Z','Y').to_euler()
        extra.data.lens=35
bpy.app.handlers.save_pre.append(frame_school_facade)
