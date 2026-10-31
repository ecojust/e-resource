"""Save editable Daxin historic main block geometry; render and reopen the actual .blend."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ID='huangpu-daxin-company'
def geometry_hash(objects):
 d=hashlib.sha256()
 for ob in sorted(objects,key=lambda o:o.name):
  d.update(ob.name.encode())
  for row in ob.matrix_world:d.update(struct.pack('<4f',*row))
  for v in ob.data.vertices:d.update(struct.pack('<3f',*v.co))
  for p in ob.data.polygons:
   assert len(p.vertices)==3
   d.update(struct.pack('<3I',*p.vertices))
 return d.hexdigest()

p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--previews',type=Path,required=True);p.add_argument('--samples',type=int,default=16);p.add_argument('--suffix',default='')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
data=a.raw.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);meta=doc['extras'];assert meta['id']==ID
bpy.ops.import_scene.gltf(filepath=str(a.raw.resolve()))
model=[ob for ob in bpy.context.scene.objects if ob.type=='MESH'];assert len(model)==1
source_sha=hashlib.sha256(data).hexdigest()
for ob in model:
 ob['source_raw_sha256']=source_sha;ob['scope']='Daxin historic main block exterior. South and west are photo guided; north/east and unseen roof, all dimensions and height endpoints are author estimates. Modern B/C buildings, advertising and interiors are excluded.'
count=sum(len(ob.data.polygons) for ob in model)
assert count==sum(doc['accessors'][pr['indices']]['count']//3 for m in doc['meshes'] for pr in m['primitives'])
before=geometry_hash(model);scene=bpy.context.scene
coll=bpy.data.collections.new('Preview only — not part of building');scene.collection.children.link(coll)
def stage(ob):
 for c in list(ob.users_collection):c.objects.unlink(ob)
 coll.objects.link(ob)
target=Vector((0,0,20.0))
bpy.ops.mesh.primitive_plane_add(size=300,location=(0,0,-.12));ground=bpy.context.object;ground.name='Preview ground, not surveyed';stage(ground)
mat=bpy.data.materials.new('Preview ground');mat.diffuse_color=(.24,.26,.24,1);ground.data.materials.append(mat)
bpy.ops.object.light_add(type='AREA',location=(-70,120,150));ob=bpy.context.object;ob.data.energy=15000;ob.data.shape='DISK';ob.data.size=9;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();stage(ob)
bpy.ops.object.light_add(type='SUN',location=(0,0,130));ob=bpy.context.object;ob.data.energy=2.;ob.rotation_euler=(.4,-.4,-.6);stage(ob)
bpy.ops.object.camera_add();camera=bpy.context.object;stage(camera);scene.camera=camera;camera.data.lens=50
scene.render.engine='CYCLES';scene.cycles.samples=a.samples;scene.cycles.use_denoising=False
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Preview world');scene.world.color=(.27,.27,.27)
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.unit_settings.system='METRIC'
views={'native-front':(0,-145,57),'native-oblique':(-110,-115,76),'native-rear':(100,110,73)}
a.previews.mkdir(parents=True,exist_ok=True);a.out.parent.mkdir(parents=True,exist_ok=True)
bpy.context.view_layer.update();corners=[ob.matrix_world@Vector(c) for ob in model for c in ob.bound_box];records=[]
for name,position in views.items():
 camera.location=position;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 for k in range(30):
  bpy.context.view_layer.update();q=[world_to_camera_view(scene,camera,c) for c in corners]
  lo=[min(v[i] for v in q) for i in range(3)];hi=[max(v[i] for v in q) for i in range(3)]
  if lo[0]>=.04 and lo[1]>=.04 and hi[0]<=.96 and hi[1]<=.96 and lo[2]>0:break
  camera.location=target+(camera.location-target)*1.06
 else:raise AssertionError('Unable to frame actual model')
 path=a.previews/(name+a.suffix+'.png');scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True)
 records.append({'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera_position':list(camera.location),'target':list(target),'bbox_ndc_min':lo,'bbox_ndc_max':hi,'framing_steps':k})
camera.location=records[1]['camera_position'];camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
scene['candidate_id']=ID;scene['model_mesh_names']=[ob.name for ob in model];scene['candidate_metadata_json']=json.dumps(meta,ensure_ascii=False);scene['preview_stage_excluded_from_model']=True
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
assert 0<a.out.stat().st_size<100000000
bpy.ops.wm.open_mainfile(filepath=str(a.out.resolve()));reopened=[bpy.data.objects[n] for n in bpy.context.scene['model_mesh_names']]
assert geometry_hash(reopened)==before and sum(len(o.data.polygons) for o in reopened)==count
assert json.loads(bpy.context.scene['candidate_metadata_json'])==meta
report={'id':ID,'blender':bpy.app.version_string,'source_raw_sha256':source_sha,'model_triangles':count,'model_meshes':len(reopened),'geometry_hash_before_and_after_reopen':before,'bytes':a.out.stat().st_size,'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'actual_reopen_passed':True,'stage_excluded_from_geometry_hash':True,'previews':records}
(a.previews/'native.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
