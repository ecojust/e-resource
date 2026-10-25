"""Build Shanghai GLB landmarks in true meters and a georeferenced Blender scene.

Run: blender --background --python export_landmarks.py
All exports have their footprint center at local origin and local ground y=0
in glTF (z=0 in Blender). Coordinates in metadata.json anchor them to the map.
"""
import bpy
import json
import math
import os
import sys
from pathlib import Path
from mathutils import Vector,Matrix

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
OUT=Path(os.environ.get('SHANGHAI_OUTPUT_DIR',str(HERE.parent/'output'/'shanghai')))
ASSETS=OUT/'landmarks';ASSETS.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)

def mat(name,color,metal=.2,rough=.35):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
 p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
mats={
 'glass_blue':mat('Blue curtain glass',(.075,.20,.29),.48,.25),
 'glass_teal':mat('Teal curtain glass',(.14,.35,.40),.42,.27),
 'metal':mat('Graphite metal',(.15,.18,.20),.7,.3),
 'silver':mat('Brushed silver',(.58,.64,.68),.66,.31),
 'stone':mat('Pale architectural stone',(.55,.57,.54),.05,.65),
 'warm':mat('Warm stone',(.67,.51,.33),.08,.56),
 'red':mat('Antenna warning red',(.62,.12,.12),.18,.40),
}
from landmarks import build_landmark_groups,LANDMARKS
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['Coordinate system']='Blender east / north / up. Native placement uses local tangent-plane approximation centered at 121.503,31.236; GLBs are local-origin meters.'
groups=build_landmark_groups(mats)
metadata={'schemaVersion':1,'units':'meters','coordinateSystem':'glTF right-handed Y-up, local origin at footprint center','mapCrs':'EPSG:4326','modeling':'Procedural visual approximations of recognizable landmarks; geographic anchors and original heights are explicit. Not survey-grade geometry.','landmarks':[]}
origin=(121.503,31.236)
for slug,objects in groups.items():
 meta=LANDMARKS[slug];cx,cy=meta['center']
 original={obj:obj.matrix_world.copy() for obj in objects}
 local=Matrix.Diagonal(Vector((4,4,4,1)))@Matrix.Translation((-cx,-cy,0))
 for obj in objects:obj.matrix_world=local@original[obj]
 bpy.context.view_layer.update()
 # Native model details extend by tiny mullion radii: normalize actual height.
 corners=[obj.matrix_world@Vector(corner) for obj in objects for corner in obj.bound_box]
 minz=min(v.z for v in corners);maxz=max(v.z for v in corners)
 zfactor=meta['height']/(maxz-minz)
 adjust=Matrix.Diagonal(Vector((1,1,zfactor,1)))@Matrix.Translation((0,0,-minz))
 for obj in objects:obj.matrix_world=adjust@obj.matrix_world
 bpy.context.view_layer.update()
 corners=[obj.matrix_world@Vector(corner) for obj in objects for corner in obj.bound_box]
 bbox={'min':[min(v[i] for v in corners) for i in range(3)],'max':[max(v[i] for v in corners) for i in range(3)]}
 bpy.ops.object.select_all(action='DESELECT')
 for obj in objects:obj.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 path=ASSETS/(slug+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True)
 assert 0<path.stat().st_size<100_000_000
 entry={'id':slug,'name':meta['name'],'file':'landmarks/'+slug+'.glb','longitude':meta['longitude'],'latitude':meta['latitude'],'osmWay':meta['osmWay'],'coordinateSource':'https://www.openstreetmap.org/way/'+str(meta['osmWay']),'heightMeters':meta['height'],'footprintMeters':{'width':bbox['max'][0]-bbox['min'][0],'depth':bbox['max'][1]-bbox['min'][1]},'bytes':path.stat().st_size,'glTFUpAxis':'Y','blenderBounds':bbox}
 metadata['landmarks'].append(entry)
 # Arrange native edit scene at the correct relative geographic locations.
 x=(meta['longitude']-origin[0])*111320*math.cos(math.radians(origin[1]))
 y=(meta['latitude']-origin[1])*111320
 group=bpy.data.collections.new(meta['name']+' / '+slug);scene.collection.children.link(group)
 for obj in objects:
  obj.matrix_world=Matrix.Translation((x,y,0))@obj.matrix_world
  for c in list(obj.users_collection):c.objects.unlink(obj)
  group.objects.link(obj)
 group['longitude']=meta['longitude'];group['latitude']=meta['latitude'];group['height_m']=meta['height']
 print('LANDMARK_EXPORTED',slug,path.stat().st_size,'bytes',entry['footprintMeters'])
(OUT/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
# A camera and neutral lighting make the native file convenient to inspect.
bpy.ops.object.camera_add(location=(-2200,-2300,1500))
cam=bpy.context.object;cam.name='Shanghai skyline overview';cam.rotation_euler=(Vector((-250,200,300))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=48;cam.data.clip_end=10000;scene.camera=cam
sun_data=bpy.data.lights.new('Afternoon sun','SUN');sun_data.energy=3
sun=bpy.data.objects.new('Afternoon sun',sun_data);scene.collection.objects.link(sun);sun.rotation_euler=(math.radians(30),math.radians(-20),math.radians(-35))
scene.world.color=(.34,.40,.47)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.clip_end=20000
   area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'shanghai-landmarks.blend'))
assert (OUT/'shanghai-landmarks.blend').stat().st_size<100_000_000
print('LANDMARKS_COMPLETE',str(OUT))
