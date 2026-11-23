"""Render the original Fuzhou Road stone façade at two heights without a map overlay.

blender -b building.blend --threads 2 --python-exit-code 8 --python render-stone-arches.py -- output-directory
"""
from pathlib import Path
import hashlib,json,sys
import bpy
from mathutils import Vector

out=Path(sys.argv[sys.argv.index('--')+1])
scene=bpy.context.scene
stone=bpy.data.materials['Weathered dark granite ashlar']
nodes=[n for n in stone.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.packed_file]
assert nodes and any(link.to_socket.name=='Base Color' for n in nodes for link in n.outputs['Color'].links)
image=nodes[0].image
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(image.packed_file.data)=='287b769fc4b4409e95832d6b9bf115d6bb1b289974dc1fc0fc5be8ca1ca85549'
assert len([o for o in scene.objects if o.type=='MESH' and o.active_material==stone and o.data.uv_layers])>0
# Source axes run west, inward, upward. Door platform Z=1.56, lower crown Z=4.75,
# window shoulders Z=7.85 and three stone arch tips Z=9.58. East steps start at X=.32.
source_camera=scene.camera
camera=source_camera.copy();camera.data=source_camera.data.copy();scene.collection.objects.link(camera);scene.camera=camera
camera.data.type='ORTHO';camera.data.clip_end=250;camera.data.shift_x=0;camera.data.shift_y=0
for lamp in [o for o in scene.objects if o.type=='LIGHT']:
 lamp.hide_render=True
world=bpy.data.worlds.new('North street skylight');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.66,.72,.81,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.58
scene.world=world
def area(name,source,target,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size
 light=bpy.data.objects.new(name,d);scene.collection.objects.link(light);light.location=source
 light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
area('Upper east reflected daylight',(-2.5,-6,13.2),(4.4,0,5.7),1950,6.0)
area('West street fill',(11,-7,8.2),(4.5,0,5.0),940,7.0)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.cycles.use_denoising=False;scene.render.resolution_x=960;scene.render.resolution_y=600
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
views={}
for name,target,eye,span in [
 ('three-round-arches-and-east-steps',(4.34,-.99,2.8),(-.8,-20,6.4),9.72),
 ('three-pointed-arches-and-corbelled-sills',(4.48,-.16,7.57),(.86,-20.1,9.17),9.50)]:
 camera.location=Vector(eye);camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
 camera.data.ortho_scale=span;scene.render.filepath=str(out/(name+'.png'))
 bpy.ops.render.render(write_still=True)
 views[name]=dict(eye=eye,target=target,orthographic_width_m=span,output_sha256=sha((out/(name+'.png')).read_bytes()))
s=dict(source_blend_sha256=sha(Path(bpy.data.filepath).read_bytes()),packed_image_sha256=sha(image.packed_file.data),
       image_size=list(image.size),mesh_objects=sum(o.type=='MESH'for o in scene.objects),original_camera=source_camera.name,
       render_engine=scene.render.engine,resolution=[960,600],views=views)
(out/'camera-and-material-check.json').write_text(json.dumps(s,indent=2)+'\n')
