"""Save editable China Aviation Association building geometry; render and reopen the actual .blend."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ID='yangpu-china-aviation-association-building'
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

p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--previews',type=Path,required=True);p.add_argument('--samples',type=int,default=16);p.add_argument('--suffix',default='');p.add_argument('--views',default='front,oblique,rear,roof,entrance,crown,eastportal,connector')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
data=a.raw.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);meta=doc['extras'];assert meta['id']==ID
bpy.ops.import_scene.gltf(filepath=str(a.raw.resolve()))
model=[ob for ob in bpy.context.scene.objects if ob.type=='MESH'];assert len(model)==1
source_sha=hashlib.sha256(data).hexdigest()
params=json.loads(Path(__file__).with_name('model-parameters.json').read_text());cx,cy=params['tower_center_enu_m'];tr=params['tower_radius_m']
for ob in model:
 ob['source_raw_sha256']=source_sha;ob['scope']=meta['scope']
count=sum(len(ob.data.polygons) for ob in model)
assert count==sum(doc['accessors'][pr['indices']]['count']//3 for m in doc['meshes'] for pr in m['primitives'])
before=geometry_hash(model);scene=bpy.context.scene
coll=bpy.data.collections.new('Preview only — not part of building');scene.collection.children.link(coll)
def stage(ob):
 for c in list(ob.users_collection):c.objects.unlink(ob)
 coll.objects.link(ob)
target=Vector((0,0,8))
bpy.ops.mesh.primitive_plane_add(size=230,location=(0,0,-.02));ground=bpy.context.object;ground.name='Preview ground, not surveyed';stage(ground)
mat=bpy.data.materials.new('Preview ground');mat.diffuse_color=(.24,.26,.24,1);ground.data.materials.append(mat)
bpy.ops.object.light_add(type='AREA',location=(-70,95,130));ob=bpy.context.object;ob.data.energy=20000;ob.data.shape='DISK';ob.data.size=9;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();stage(ob)
bpy.ops.object.light_add(type='SUN',location=(0,0,130));ob=bpy.context.object;ob.data.energy=2.;ob.rotation_euler=(.4,-.4,-.6);stage(ob)
bpy.ops.object.camera_add();camera=bpy.context.object;stage(camera);scene.camera=camera;camera.data.lens=50
scene.render.engine='CYCLES';scene.cycles.samples=a.samples;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Preview world');scene.world.color=(.27,.27,.27)
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.unit_settings.system='METRIC'
available={'front':(-96,.4,31),'oblique':(-80,-67,60),'rear':(83,62,46),'roof':(5,-16,120),'entrance':(cx-31,cy,7),'crown':(cx-26,cy-24,39),'eastportal':(48,1.15,8),'connector':(36,-35,27)}
views={'native-'+name:available[name] for name in a.views.split(',')}
a.previews.mkdir(parents=True,exist_ok=True);a.out.parent.mkdir(parents=True,exist_ok=True)
bpy.context.view_layer.update();corners=[ob.matrix_world@Vector(c) for ob in model for c in ob.bound_box];records=[]
for name,position in views.items():
 target=Vector((cx-tr,cy,3.5)) if name=='native-entrance' else Vector((cx,cy,14.5)) if name=='native-crown' else Vector((25.25,1.15,4.2)) if name=='native-eastportal' else Vector((6.3,1.1,6.9)) if name=='native-connector' else Vector((1,0,7))
 scope={'native-entrance':[(cx-tr-1.8,cy-5.1,0),(cx-tr+1.7,cy+5.1,8.2)],'native-crown':[(cx-tr-1.4,cy-7.4,10.5),(cx+tr+1.4,cy+7.6,17)],'native-eastportal':[(24,-3.5,0),(27,5.9,8.8)],'native-connector':[(-6,-4,0),(25,6.3,9)]}.get(name)
 view_corners=[Vector((x,y,z)) for x in [scope[0][0],scope[1][0]] for y in [scope[0][1],scope[1][1]] for z in [scope[0][2],scope[1][2]]] if scope else corners
 camera.location=position;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 for k in range(30):
  bpy.context.view_layer.update();q=[world_to_camera_view(scene,camera,c) for c in view_corners]
  lo=[min(v[i] for v in q) for i in range(3)];hi=[max(v[i] for v in q) for i in range(3)]
  if lo[0]>=.04 and lo[1]>=.04 and hi[0]<=.96 and hi[1]<=.96 and lo[2]>0:break
  camera.location=target+(camera.location-target)*1.06
 else:raise AssertionError('Unable to frame actual model')
 path=a.previews/(name+a.suffix+'.png');scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True)
 records.append({'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera_position':list(camera.location),'target':list(target),'bbox_ndc_min':lo,'bbox_ndc_max':hi,'framing_steps':k,'framing_scope':'specified architectural detail' if scope else 'complete model'})
selected=records[min(1,len(records)-1)];camera.location=selected['camera_position'];target=Vector(selected['target']);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
scene['candidate_id']=ID;scene['model_mesh_names']=[ob.name for ob in model];scene['candidate_metadata_json']=json.dumps(meta,ensure_ascii=False);scene['preview_stage_excluded_from_model']=True
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
assert 0<a.out.stat().st_size<100000000
bpy.ops.wm.open_mainfile(filepath=str(a.out.resolve()));reopened=[bpy.data.objects[n] for n in bpy.context.scene['model_mesh_names']]
assert geometry_hash(reopened)==before and sum(len(o.data.polygons) for o in reopened)==count
assert json.loads(bpy.context.scene['candidate_metadata_json'])==meta
report={'id':ID,'blender':bpy.app.version_string,'source_raw_sha256':source_sha,'model_triangles':count,'model_meshes':len(reopened),'geometry_hash_before_and_after_reopen':before,'bytes':a.out.stat().st_size,'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'actual_reopen_passed':True,'stage_excluded_from_geometry_hash':True,'render_engine':'CYCLES','render_samples':a.samples,'denoising':False,'render_sequence':'8 views from the same pre-save building geometry; actual saved file reopened and geometry hash verified identical','previews':records}
(a.previews/'native.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
