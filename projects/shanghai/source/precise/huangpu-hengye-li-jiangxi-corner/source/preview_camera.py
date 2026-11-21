"""Pack both original masonry materials into Blender and frame the two street elevations."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from brickwork import texture_uv

@bpy.app.handlers.persistent
def prepare_native(_):
    source = Path(__file__).resolve().parent
    material_files = {'charcoal grey face brick':'grey-brick.png','dull red face brick':'red-brick.png'}
    for name,file in material_files.items():
        mat = bpy.data.materials.get(name)
        if not mat:continue
        tree = mat.node_tree
        if not tree.nodes.get('Hengye running bond'):
            node = tree.nodes.new('ShaderNodeTexImage')
            node.name = 'Hengye running bond'
            node.image = bpy.data.images.load(str(source/file),check_existing=True)
            node.image.pack()
            tree.links.new(node.outputs['Color'],tree.nodes.get('Principled BSDF').inputs['Base Color'])
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or not any(mat and mat.name in material_files for mat in obj.data.materials):
            continue
        mesh = obj.data
        uv = mesh.uv_layers.get('Brick courses') or mesh.uv_layers.new(name='Brick courses')
        for loop in mesh.loops:
            uv.data[loop.index].uv = texture_uv(*mesh.vertices[loop.vertex_index].co)
    scene = bpy.context.scene
    if not scene.camera:return
    camera = scene.camera
    direction = Vector((1.10,-1.52,.32)).normalized()
    rotation = (-direction).to_track_quat('-Z','Y')
    corners = [rotation.inverted() @ (obj.matrix_world @ Vector(v))
               for obj in scene.objects if obj.type=='MESH' for v in obj.bound_box]
    low = Vector([min(c[i] for c in corners) for i in range(3)])
    high = Vector([max(c[i] for c in corners) for i in range(3)])
    center = rotation @ ((low+high)/2)
    camera.location = center + direction * 90
    camera.rotation_euler = rotation.to_euler()
    camera.name = 'Middle Jiangxi Road and Sijing Road'
    scene.render.resolution_x,scene.render.resolution_y = 950,760
    camera.data.ortho_scale = 1.
    aperture = camera.data.view_frame(scene=scene)
    span = [max(p[i] for p in aperture) - min(p[i] for p in aperture) for i in range(2)]
    camera.data.ortho_scale = 1.10 * max((high[i]-low[i])/span[i] for i in range(2))
    for obj in scene.objects:
        if obj.type=='LIGHT' and obj.data.type=='SUN':
            obj.location = Vector((28,-42,48))
            obj.rotation_euler = (-obj.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(prepare_native)
