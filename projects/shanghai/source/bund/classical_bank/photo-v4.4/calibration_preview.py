import bpy,json,numpy as np,math,sys,argparse
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
ap=argparse.ArgumentParser();ap.add_argument('--photo',default=str(P/'hsbc-20250501-original.jpg'));args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);im=bpy.data.images.load(args.photo)
m=bpy.data.materials.new('Calibration original photo');m.use_nodes=True
nd=m.node_tree.nodes;nd.clear();tex=nd.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Linear';em=nd.new('ShaderNodeEmission');out=nd.new('ShaderNodeOutputMaterial');m.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);m.node_tree.links.new(em.outputs[0],out.inputs[0])
def Hquad(q):
 A=[];b=[]
 for (s,t),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],q):A.extend([[s,t,1,0,0,0,-s*x,-t*x],[0,0,0,s,t,1,-s*y,-t*y]]);b.extend([x,y])
 return np.append(np.linalg.solve(np.array(A),np.array(b)),1).reshape(3,3)
for i,w in enumerate(json.loads((P/'calibration.json').read_text())['windows']):
 H=Hquad(w['quad_display']);verts=[];uvs=[];fs=[];N=10
 for y in range(N+1):
  for x in range(N+1):
   s=x/N;t=y/N;p=H@np.array([s,t,1]);uvs.append((p[0]/p[2]/1920,1-p[1]/p[2]/1280));verts.append(((i%3)*1.5+s,0,3-(i//3)*1.8-t*1.6))
 for y in range(N):
  for x in range(N):a=y*(N+1)+x;fs.append((a,a+N+1,a+N+2,a+1))
 me=bpy.data.meshes.new(w['id']);me.from_pydata(verts,[],fs);me.materials.append(m);o=bpy.data.objects.new(w['id'],me);bpy.context.collection.objects.link(o);uv=me.uv_layers.new()
 for p in me.polygons:
  for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
camd=bpy.data.cameras.new('calibration');cam=bpy.data.objects.new('calibration',camd);bpy.context.collection.objects.link(cam);cam.location=(2,-10,1.4);cam.rotation_euler=(Vector((2,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=4.5
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.use_denoising=False;s.render.resolution_x=1400;s.render.resolution_y=1150;s.render.resolution_percentage=100;s.world.color=(0,0,0);s.view_settings.view_transform='Standard';s.render.image_settings.file_format='PNG';s.render.filepath=str(P/'calibration-preview.png');bpy.ops.render.render(write_still=True)
