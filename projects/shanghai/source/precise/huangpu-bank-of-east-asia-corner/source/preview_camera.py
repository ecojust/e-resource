"""Frame the four-column entrance, setback corner windows and small square crown."""
import bpy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from aggregate import texture_uv
from mathutils import Vector

@bpy.app.handlers.persistent
def frame_east_asia(_):
    material=bpy.data.materials.get('grey aggregate stone')
    if material and not material.node_tree.nodes.get('East Asia aggregate'):
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.name='East Asia aggregate'
        texture.image=bpy.data.images.load(str(Path(__file__).with_name('aggregate.png')))
        texture.image.pack()
        shader=material.node_tree.nodes.get('Principled BSDF')
        material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or material.name not in obj.data.materials:continue
            mesh=obj.data
            uv=mesh.uv_layers.new(name='Grey dressed stone')
            for loop in mesh.loops:
                uv.data[loop.index].uv=texture_uv(*mesh.vertices[loop.vertex_index].co)
    scene=bpy.context.scene
    camera=scene.camera
    if not camera:return
    # From the northeast junction, slightly toward the Jiujiang Road wing.
    direction=Vector((.18,-1.72,.14)).normalized()
    rotation=(-direction).to_track_quat('-Z','Y')
    corners=[rotation.inverted() @ (obj.matrix_world @ Vector(coord))
             for obj in scene.objects if obj.type=='MESH' for coord in obj.bound_box]
    if not corners:return
    lower=Vector([min(corner[i] for corner in corners) for i in range(3)])
    upper=Vector([max(corner[i] for corner in corners) for i in range(3)])
    center=rotation @ ((lower+upper)/2)
    camera.location=center+direction*130
    camera.rotation_euler=rotation.to_euler()
    # Raking light separates the four stone shafts from the entrance behind.
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type=='SUN':
            light.location=Vector((24,-35,47))
            light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    camera.name='东亚大楼 · 四川中路与九江路'
    camera.data.name='转角正交相机'
    scene.cycles.samples=12
    scene.render.resolution_x=760
    scene.render.resolution_y=900
    camera.data.ortho_scale=1
    frame=camera.data.view_frame(scene=scene)
    unit_width=max(v.x for v in frame)-min(v.x for v in frame)
    unit_height=max(v.y for v in frame)-min(v.y for v in frame)
    camera.data.ortho_scale=1.11*max((upper.x-lower.x)/unit_width,(upper.y-lower.y)/unit_height)
    bpy.context.view_layer.update()
    print('Framed the four-column portico and stepped corner. Scale',camera.data.ortho_scale)

bpy.app.handlers.save_pre.append(frame_east_asia)
