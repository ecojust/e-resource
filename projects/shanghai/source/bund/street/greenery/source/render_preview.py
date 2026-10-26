from pathlib import Path
import bpy, json, math, sys
from mathutils import Vector
P=Path(__file__).resolve().parent.parent;out=P/'output';data=json.loads((P/'data/greenery-v4.5.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(out/'bund17-18-greenery-candidate.glb'))
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.91;return m
lawn=material('Preview lawn underlying scanned grass omitted',(.08,.12,.032));stone=material('Preview existing low stone border',(.43,.44,.40));paving=material('Preview neutral pavement',(.34,.36,.37))
def polygon(name,points,height,mat):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([(x,-z,height) for x,z in points],[],[tuple(range(len(points)))]);mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat);return obj
for b in data['beds']:
 polygon('Existing bed interior '+b['id'],b['local_inside'],.088,lawn)
 outer=b['local_outer'];inner=b['local_inside']
 # Rendering-only low edge; external ring front face doesn't alter candidate geometry.
 for i in range(4):
  a,c=outer[i],outer[(i+1)%4];v=Vector((c[0]-a[0],-(c[1]-a[1]),0));mid=Vector(((c[0]+a[0])/2,-(c[1]+a[1])/2,.1075))
  bpy.ops.mesh.primitive_cube_add(size=1,location=mid);obj=bpy.context.object;obj.name='Preview existing stone bed edge';obj.dimensions=(v.length,.18,.215);obj.rotation_euler.z=math.atan2(v.y,v.x);obj.data.materials.append(stone)
xs=[t['x'] for t in data['trees']];zs=[t['z'] for t in data['trees']];cx=sum(xs)/len(xs);cz=sum(zs)/len(zs)
bpy.ops.mesh.primitive_plane_add(size=250,location=(cx,-cz,.03));bpy.context.object.data.materials.append(paving)
world=bpy.data.worlds.new('Overcast preview');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.67,.73,.79,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;bpy.context.scene.world=world
bpy.ops.object.light_add(type='AREA',location=(cx+12,-cz-15,30));bpy.context.object.data.energy=4500;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=18
bpy.context.object.rotation_euler=(Vector((cx,-cz,0))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='SUN',location=(cx+10,-cz-10,20));bpy.context.object.data.energy=1.5;bpy.context.object.data.angle=.12;bpy.context.object.rotation_euler=(.65,-.35,.45)
bpy.ops.object.camera_add();camera=bpy.context.object;bpy.context.scene.camera=camera;camera.data.lens=40
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=1280;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
for name,at,target,lens in [('greenery-overview',(cx+34,-cz+17,4.8),(cx,-cz,4.5),33),('north-near',(data['trees'][-2]['x']+12,-data['trees'][-2]['z']-10,2.1),(data['trees'][-2]['x'],-data['trees'][-2]['z'],4.4),40)]:
 camera.location=at;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens;scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
