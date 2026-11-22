"""Render the same original masonry and the finished elevated detail in the saved .blend."""
import sys,json
from pathlib import Path
from mathutils import Vector
import bpy
src=Path(__file__).resolve().parent
native,out=map(Path,sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=str(native))
cfg=json.loads((src/'geometry-input.json').read_bytes());f=cfg['front']
mid=Vector((*f['center_local_east_north_m'],0));t=Vector((*f['tangent_east_north'],0));n=Vector((*f['outward_normal_east_north'],0))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=5;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=1;scene.render.resolution_percentage=100
scene.render.resolution_x=552;scene.render.resolution_y=467;scene.render.image_settings.file_format='PNG'
world=bpy.data.worlds.new('Overcast Bund sky');world.use_nodes=True;scene.world=world
bg=world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.69,.76,.84,1);bg.inputs[1].default_value=1.0
for obj in list(scene.objects):
 if obj.type=='LIGHT':obj.hide_render=True
light=bpy.data.lights.new('Roof daylight','SUN');light.energy=2.15;light.angle=.16;obj=bpy.data.objects.new('Roof daylight',light);scene.collection.objects.link(obj);obj.rotation_euler=(.55,-.62,-.38)
def at(u,d,z):return mid+t*u+n*d+Vector((0,0,z))
cam=bpy.data.cameras.new('Roof comparison');obj=bpy.data.objects.new('Roof comparison camera',cam);scene.collection.objects.link(obj);scene.camera=obj
new=[x for x in scene.objects if x.name.startswith('Bund14 |')];assert len(new)==3
for shot,eye,aim,lens in [('roof-prior',(12,10,28),(0,-2.1,32.5),52),('roof-revised',(12,10,28),(0,-2.1,32.5),52),('river-view',(1,36,4),(0,-1.3,27.3),68)]:
 obj.location=at(*eye);obj.rotation_euler=(at(*aim)-obj.location).to_track_quat('-Z','Y').to_euler();cam.lens=lens
 for x in new:x.hide_render=shot=='roof-prior'
 scene.render.filepath=str(out/(shot+'.png'));bpy.ops.render.render(write_still=True)
