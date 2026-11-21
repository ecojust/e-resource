"""Orient the editable project's cameras towards the photographed south street frontage."""
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from stone_finish import IMAGE, CARVED as MATERIAL, uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_jinling_facade(*_):
    scene=bpy.context.scene
    material=bpy.data.materials[MATERIAL]
    image=bpy.data.images.load(str(IMAGE),check_existing=True)
    if not image.packed_file:
        image.pack()
    nodes=material.node_tree.nodes
    texture=nodes.get('Original limewashed street facing') or nodes.new('ShaderNodeTexImage')
    texture.name='Original limewashed street facing'
    texture.image=image
    texture.extension='EXTEND'
    material.node_tree.links.new(texture.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
    for obj in scene.objects:
        if obj.type!='MESH' or material.name not in obj.data.materials:
            continue
        mesh=obj.data
        layer=mesh.uv_layers.get('Jinling plaster') or mesh.uv_layers.new(name='Jinling plaster')
        for face in mesh.polygons:
            if mesh.materials[face.material_index]!=material:
                continue
            for index in face.loop_indices:
                world=obj.matrix_world@mesh.vertices[mesh.loops[index].vertex_index].co
                u,v=uv(world)
                layer.data[index].uv=u,1.-v
    camera=scene.camera
    if camera:
        camera.location=Vector((20,39,12))
        camera.rotation_euler=(Vector((13.18,0,6.68))-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO'
        camera.data.ortho_scale=19.7
        scene.render.resolution_x=860
        scene.render.resolution_y=750
        scene.cycles.samples=20
    for light in (o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN'):
        light.location=Vector((26,35,46))
        light.rotation_euler=(Vector((13.6,0,6.8))-light.location).to_track_quat('-Z','Y').to_euler()
    for name,eye,target in [('Timber and iron entry',(15.4,10,2.7),(13.043,0,2.23)),
                            ('Paired trefoiled windows',(16.3,9.1,8.6),(13.208,0,6.6))]:
        extra=bpy.data.objects.get(name)
        if not extra:
            extra=bpy.data.objects.new(name,bpy.data.cameras.new(name))
            scene.collection.objects.link(extra)
        extra.location=Vector(eye)
        extra.rotation_euler=(Vector(target)-extra.location).to_track_quat('-Z','Y').to_euler()
        extra.data.lens=35
bpy.app.handlers.save_pre.append(frame_jinling_facade)
