"""Make separate editable groups and preserve photographed material UVs, colors and image bytes."""
from pathlib import Path
import bpy,json,sys
from mathutils import Vector
source,out=map(Path,sys.argv[sys.argv.index('--')+1:]);doc=json.loads(source.read_bytes())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene['model_scope']=doc['scope']
materials={}
for name,s in doc['palette'].items():
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*s['color'],s.get('alpha',1));nodes=m.node_tree.nodes
 shader=nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=m.diffuse_color
 shader.inputs['Alpha'].default_value=s.get('alpha',1);shader.inputs['Roughness'].default_value=s.get('roughness',.75);shader.inputs['Metallic'].default_value=s.get('metallic',0)
 if s.get('texture'):
  image=bpy.data.images.load(s['texture'],check_existing=True);image.pack();tex=nodes.new('ShaderNodeTexImage');tex.image=image
  tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=m.diffuse_color
  m.node_tree.links.new(tex.outputs['Color'],tint.inputs[1]);m.node_tree.links.new(tint.outputs['Color'],shader.inputs['Base Color'])
 materials[name]=m
for name,g in doc['groups'].items():
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(g['v'],[],g['f']);mesh.update();ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
 for key in g['materials']:mesh.materials.append(materials[key])
 mesh.polygons.foreach_set('material_index',g['face_materials'])
 if g['uv'] is not None:
  uv=mesh.uv_layers.new(name='Architectural surface UV')
  for loop in mesh.loops:
   u,v=g['uv'][loop.vertex_index];uv.data[loop.index].uv=(u,1-v)
x,y,z=doc['center'];target=Vector((x,-z,y));e=max(doc['size']);bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Facade camera';cam.data.type='ORTHO';cam.data.ortho_scale=e*1.19
cam.location=target+Vector((.57,-2.3,.20))*e;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=target+Vector((-1,-1.4,1.7))*e);lamp=bpy.context.object;lamp.data.energy=100*e*e;lamp.data.shape='DISK';lamp.data.size=e;lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Neutral sky');scene.world.color=(.32,.32,.32);scene.render.engine='CYCLES';scene.cycles.device='CPU'
for scr in bpy.data.screens:
 for area in scr.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
scene.cycles.samples=24
scene.cycles.use_adaptive_sampling=False
scene.cycles.use_denoising=False
scene.render.resolution_x,scene.render.resolution_y=512,576
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
for name,eye,focus,scale in [('Front elevation',(3.75,-26,5.70),(3.75,.1,5.70),12.58),('End return',(17.,-24.,7.),(3.75,.2,5.55),13.6),('Recessed steel sash',(3.,-8.,6.85),(1.88,.12,6.45),3.18)]:
 data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob)
 ob.location=Vector(eye);ob.rotation_euler=(Vector(focus)-ob.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
