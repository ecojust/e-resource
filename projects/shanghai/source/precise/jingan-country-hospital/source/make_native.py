"""Create the editable native model and render from the reopened blend."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

source,filename,preview=map(Path,sys.argv[sys.argv.index('--')+1:])
data=json.loads(source.read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
materials={}
collections={}
for name,spec in data['palette'].items():
    mat=bpy.data.materials.new(name)
    color=(*spec['color'],1)
    mat.diffuse_color=color
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=color
    shader.inputs['Metallic'].default_value=spec.get('metallic',0)
    shader.inputs['Roughness'].default_value=spec.get('roughness',.78)
    materials[name]=mat
scene['model_scope']=data['metadata']['scope']
for name,parts in data['groups'].items():
    category=name.split('/')[0]
    if category not in collections:
        collections[category]=bpy.data.collections.new(category)
        scene.collection.children.link(collections[category])
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(parts['v'],[],parts['f'])
    mesh.update()
    for material in parts['materials']:
        mesh.materials.append(materials[material])
    mesh.polygons.foreach_set('material_index',parts['face_materials'])
    ob=bpy.data.objects.new(name,mesh)
    collections[category].objects.link(ob)
mesh_count=len(data['groups'])
triangles=sum(len(ob.data.polygons) for ob in scene.objects)
bounds=[Vector(v) for ob in scene.objects for v in ob.bound_box]
width=max(v.x for v in bounds)-min(v.x for v in bounds)
height=max(v.z for v in bounds)
stage=bpy.data.collections.new('Preview lighting and camera')
scene.collection.children.link(stage)
def move_to_stage(ob):
    for old in list(ob.users_collection):
        old.objects.unlink(ob)
    stage.objects.link(ob)
bpy.ops.object.camera_add()
cam=bpy.context.object
move_to_stage(cam)
scene.camera=cam
cam.name='Garden elevation'
cam.data.type='ORTHO'
cam.data.clip_end=300
target=Vector((0,.8,height*.49))
cam.location=target+Vector((-.09*width,-2.22*width,.17*height))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1280 if width/height>2 else 820
scene.render.resolution_y=540 if width/height>2 else 900
scene.render.resolution_percentage=100
cam.data.ortho_scale=max(width*1.09,height*1.12*scene.render.resolution_x/scene.render.resolution_y) * max(1.,scene.render.resolution_y/scene.render.resolution_x)
bpy.ops.object.light_add(type='SUN',location=(-20,-25,42))
sun=bpy.context.object
move_to_stage(sun)
sun.data.energy=3.3
sun.data.angle=.12
sun.rotation_euler=(-sun.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Slate studio')
scene.world.use_nodes=True
background=scene.world.node_tree.nodes['Background']
background.inputs['Color'].default_value=(.20,.25,.30,1)
background.inputs['Strength'].default_value=.58
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_adaptive_sampling=False
scene.cycles.sample_clamp_indirect=2.0
scene.cycles.use_denoising=False
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
scene.render.filepath='//'+preview.name
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(filename),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(filename))
reopened=[ob for ob in bpy.context.scene.objects if ob.type=='MESH']
assert len(reopened)==mesh_count
assert sum(len(ob.data.polygons) for ob in reopened)==triangles
assert {ob.name for ob in reopened}==set(data['groups'])
bpy.context.scene.render.filepath=str(preview.resolve())
bpy.ops.render.render(write_still=True)
print(f'Reopened {mesh_count} editable meshes and {triangles} triangles. Rendered {preview.name}.')
