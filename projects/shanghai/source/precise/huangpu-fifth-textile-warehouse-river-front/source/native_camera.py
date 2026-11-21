"""Orient the editable project's cameras towards the photographed north front on South Suzhou Road."""
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from warehouse_brick import IMAGE,MATERIAL,uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_textile_warehouse(*_):
    scene=bpy.context.scene
    material=bpy.data.materials[MATERIAL]
    material['photographic_masonry_source']='Livelikerw, 1295 South Suzhou Rd. Shanghai.JPG (2015), Wikimedia Commons'
    material['license']='CC BY-SA 4.0 — https://creativecommons.org/licenses/by-sa/4.0/'
    material['changes']='Rectified brick sample, repeated and mixed with procedural lime and masonry.'
    image=bpy.data.images.load(str(IMAGE),check_existing=True)
    if not image.packed_file:
        image.pack()
    nodes=material.node_tree.nodes
    texture=nodes.get('Warehouse masonry') or nodes.new('ShaderNodeTexImage')
    texture.name='Warehouse masonry'
    texture.image=image
    texture.extension='EXTEND'
    material.node_tree.links.new(texture.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
    for obj in scene.objects:
        if obj.type!='MESH' or material.name not in obj.data.materials:
            continue
        mesh=obj.data
        layer=mesh.uv_layers.get('Riverfront brick UV') or mesh.uv_layers.new(name='Riverfront brick UV')
        for face in mesh.polygons:
            if mesh.materials[face.material_index]!=material:
                continue
            for index in face.loop_indices:
                world=obj.matrix_world@mesh.vertices[mesh.loops[index].vertex_index].co
                u,v=uv(world)
                layer.data[index].uv=u,1.-v
    camera=scene.camera
    if camera:
        camera.location=Vector((-7,-39,11.6))
        camera.rotation_euler=(Vector((0,.6,8.10))-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO'
        camera.data.ortho_scale=33.0
        scene.render.resolution_x=860
        scene.render.resolution_y=750
        scene.cycles.samples=20
    for light in (o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN'):
        light.location=Vector((-13,-30,34))
        light.rotation_euler=(Vector((0,0,8.2))-light.location).to_track_quat('-Z','Y').to_euler()
    for name,eye,target in [('Glass-block portal',(2.1,-8.6,2.4),(0,0,1.8)),
                            ('Twin levels of segmental windows',(-5.0,-14,8.3),(0,0,8.1))]:
        extra=bpy.data.objects.get(name)
        if not extra:
            extra=bpy.data.objects.new(name,bpy.data.cameras.new(name))
            scene.collection.objects.link(extra)
        extra.location=Vector(eye)
        extra.rotation_euler=(Vector(target)-extra.location).to_track_quat('-Z','Y').to_euler()
        extra.data.lens=35
bpy.app.handlers.save_pre.append(frame_textile_warehouse)
