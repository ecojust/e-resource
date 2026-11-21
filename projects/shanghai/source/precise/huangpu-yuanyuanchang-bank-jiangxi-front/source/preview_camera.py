"""Frame the brick bank facade, the tall fluted pilasters and the crest."""
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from masonry import blender_uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_bank(_):
    source = Path(__file__).resolve().parent
    material_files = {'brown firebrick and pale joints':'brown-firebrick.png'}
    for name,file in material_files.items():
        mat = bpy.data.materials.get(name)
        if not mat:continue
        tree = mat.node_tree
        if not tree.nodes.get('Bank firebrick courses'):
            node = tree.nodes.new('ShaderNodeTexImage')
            node.name = 'Bank firebrick courses'
            node.image = bpy.data.images.load(str(source/file),check_existing=True)
            node.image.pack()
            tree.links.new(node.outputs['Color'],tree.nodes.get('Principled BSDF').inputs['Base Color'])
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or not any(mat and mat.name in material_files for mat in obj.data.materials):
            continue
        mesh = obj.data
        uv = mesh.uv_layers.get('Brick courses') or mesh.uv_layers.new(name='Brick courses')
        for loop in mesh.loops:
            uv.data[loop.index].uv = blender_uv(*mesh.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # The low oblique view keeps the whole crest and both street returns visible.
    direction=Vector((.33,-2.24,.31)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Oblique daylight preserves the window reveals on the light street elevation.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((-20,-29,43))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='Yuanyuanchang Bank, east street elevation'
    camera.data.name='源源长银行圆徽东立面'
    scene.render.resolution_x=960
    scene.render.resolution_y=650
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.13*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the eastern brick facade and roundel. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_bank)
