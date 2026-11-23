"""Render the Sichuan Road entrance at its authored coordinates from the original BLEND.

Usage: blender -b path/to/original.blend -t 1 --python-exit-code 4
       --python render-sichuan-door.py -- path/to/sichuan-320-gold-door.png
"""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

output = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
scene = bpy.context.scene
meshes = [obj for obj in scene.objects if obj.type=='MESH']
assert len(meshes)==101
gold = [o for o in meshes if any(m and m.name=='Old gold building letters' for m in o.data.materials)]
assert gold
normal = Vector((-.998299,-.058299,0.0)).normalized()
along = Vector((-normal.y,normal.x,0.0))
target = Vector((-4.1236117593,10.3254711419,2.00))+.10*normal+.15*along
camera=bpy.data.cameras.new('Sichuan Road doorway detail')
obj=bpy.data.objects.new('Sichuan Road doorway detail',camera);scene.collection.objects.link(obj)
obj.location=target+normal*8.25-along*.42+Vector((0,0,.19))
obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
camera.type='ORTHO';camera.ortho_scale=5.04;scene.camera=obj
for lamp in [o for o in scene.objects if o.type=='LIGHT']:
    lamp.hide_render=True
def light(name,offset,energy,extent):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=extent
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=target+offset
    ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
light('Daylight over Sichuan Road',normal*4.7-along*3.6+Vector((0,0,4.8)),540,4.3)
light('Opposite street reflection',normal*3.8+along*4.8+Vector((0,0,1.2)),210,5.4)
world=bpy.data.worlds.new('Open street diffuse sky');world.use_nodes=True
world.node_tree.nodes.get('Background').inputs[0].default_value=(.60,.66,.74,1)
world.node_tree.nodes.get('Background').inputs[1].default_value=.42;scene.world=world
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=20
scene.cycles.use_denoising=False
scene.render.resolution_x=1040;scene.render.resolution_y=880;scene.render.resolution_percentage=100
scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB';scene.render.filepath=str(output)
bpy.ops.render.render(write_still=True)
print('Verified source mesh groups:',len(meshes),'and gold material objects:',len(gold),flush=True)
