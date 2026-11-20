"""Produce the original and revised clay-lit views with the actual editable materials, using Cycles CPU."""
from pathlib import Path
import json,sys,math
import bpy
from mathutils import Vector
s=Path(__file__).resolve().parent;prior,out,prefix=sys.argv[sys.argv.index('--')+1:];out=Path(out)
bpy.ops.wm.open_mainfile(filepath=prior)
p=json.loads((s/'news-footprint.json').read_bytes());a,b=[Vector((*q,0))for q in p['polygon_local_east_north'][2:4]]
axis=(b-a).normalized();normal=Vector((axis.y,-axis.x,0));mid=(a+b)/2;wing=(b-a).length/2-3.55/2
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=10;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=1;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
world=bpy.data.worlds.new('Review soft sky');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.63,.68,.74,1);world.node_tree.nodes['Background'].inputs[1].default_value=.43
def light(name,pos,aim,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos
 obj.rotation_euler=(aim-pos).to_track_quat('-Z','Y').to_euler()
light('Front softbox',mid+normal*12-axis*6+Vector((0,0,11)),mid+Vector((0,0,2)),4000,10)
light('Reflected street light',mid+normal*6+axis*9+Vector((0,0,6)),mid+axis*5+Vector((0,0,2.2)),1000,7)
camdata=bpy.data.cameras.new('Street-facing comparison');cam=bpy.data.objects.new('Door study camera',camdata)
scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO'
for label,u,h,span,xpx,ypx in [('north-wing',wing,1.98,3.85,430,470),('both-wings',0,3.03,18.6,850,310)]:
 aim=mid+axis*u+Vector((0,0,h))
 cam.location=aim+normal*14-axis*.38+Vector((0,0,.72))
 cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=span
 scene.render.resolution_x=xpx;scene.render.resolution_y=ypx;scene.render.filepath=str(out/(prefix+'-'+label+'.png'))
 bpy.ops.render.render(write_still=True)
