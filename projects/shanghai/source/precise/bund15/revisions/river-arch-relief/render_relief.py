"""Render the inherited and modified editable scene with identical inspection cameras."""
from pathlib import Path
import json, sys
import bpy
from mathutils import Vector

here=Path(__file__).resolve().parent
source,out,prefix=sys.argv[sys.argv.index('--')+1:]
out=Path(out);out.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=source)
frame=json.loads((here/'facade-frame.json').read_bytes())
u=Vector((*frame['world_basis_u'],0));outward=-Vector((*frame['world_basis_v'],0))
cx,cy=frame['front_center']
mid=u*(cx+frame['left_bay_center_u_m'])-outward*cy
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
scene.cycles.samples=8;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=1
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for obj in list(scene.objects):
    if obj.type=='LIGHT':obj.hide_render=True
world=bpy.data.worlds.new('Neutral daylight');world.use_nodes=True;scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.70,.72,.76,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.29

def light(name,pos,aim,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(aim-pos).to_track_quat('-Z','Y').to_euler()

aim=mid+Vector((0,0,10.25))
light('Raking light',aim+outward*6-u*4+Vector((0,0,6)),aim,1200,3.2)
light('Street fill',aim+outward*5+u*4+Vector((0,0,2)),aim,240,5)
cam_data=bpy.data.cameras.new('Frontal inspection')
cam=bpy.data.objects.new('River window comparison',cam_data);scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO'
for label,x,z,span,w,h in [('whole-arch',0,9.72,6.10,680,390),
                           ('wing-and-keystone',-1.14,10.69,3.43,620,350)]:
    target=mid+u*x+Vector((0,0,z))
    cam.location=target+outward*11-u*.25+Vector((0,0,-.36))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=span;scene.render.resolution_x=w;scene.render.resolution_y=h
    scene.render.filepath=str(out/(prefix+'-'+label+'.png'));bpy.ops.render.render(write_still=True)
