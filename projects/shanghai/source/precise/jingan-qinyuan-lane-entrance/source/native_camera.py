"""Pack the timber and rendered wall finishes, and save the six editing views."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
source=Path(__file__).resolve().parent
sys.path.insert(0,str(source))
from native_layout import CAMERAS,MAIN,MATERIALS,UV_NAME,uv_for_face

@bpy.app.handlers.persistent
def prepare_qinyuan(_):
    scene=bpy.context.scene
    for material,(filename,label) in MATERIALS.items():
        graph=bpy.data.materials[material].node_tree
        texture=graph.nodes.get(label)
        if texture is None:
            texture=graph.nodes.new('ShaderNodeTexImage');texture.name=label
            texture.image=bpy.data.images.load(str(source/filename),check_existing=True);texture.image.pack()
            texture.extension='EXTEND';graph.links.new(texture.outputs['Color'],graph.nodes['Principled BSDF'].inputs['Base Color'])
    for obj in scene.objects:
        if obj.type!='MESH' or not any(mat.name in MATERIALS for mat in obj.data.materials):continue
        mesh=obj.data
        layer=mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
        for face in mesh.polygons:
            material=mesh.materials[face.material_index].name
            if material not in MATERIALS:continue
            points=[mesh.vertices[mesh.loops[i].vertex_index].co for i in face.loop_indices]
            for i,uv in zip(face.loop_indices,uv_for_face(material,points,obj.name)):layer.data[i].uv=uv
        mesh.uv_layers.active=layer;layer.active_render=True
    collection=bpy.data.collections['Preview lighting and camera']
    for name,(eye,focus,scale) in CAMERAS.items():
        cam=scene.camera if name==MAIN else bpy.data.objects.get(name)
        if cam is None:
            cam=bpy.data.objects.new(name,bpy.data.cameras.new(name));collection.objects.link(cam)
        cam.name=cam.data.name=name;cam.location=Vector(eye)
        cam.rotation_euler=(Vector(focus)-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.type='ORTHO';cam.data.ortho_scale=scale;cam.data.clip_start=.05;cam.data.clip_end=300
        cam['aim_local_m']=focus
    scene.render.resolution_x=880;scene.render.resolution_y=760;scene.render.resolution_percentage=100
    sun=next(o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN')
    sun.location=Vector((-25,-22,32));sun.rotation_euler=(-sun.location).to_track_quat('-Z','Y').to_euler()
    scene['reference_state']='Street exterior checked against the 2018 hanging sign, the February 2021 street survey, the 2021 plaque photograph, and Tang Min’s 2022 entrance photograph.'
    bpy.context.view_layer.update()

bpy.app.handlers.save_pre.append(prepare_qinyuan)
