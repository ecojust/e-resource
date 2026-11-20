"""Save editable former Shanghai city museum geometry; render and reopen the actual .blend."""
import argparse,hashlib,json,struct,sys,subprocess,tempfile
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ID='yangpu-former-shanghai-city-museum'
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

p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--previews',type=Path,required=True);p.add_argument('--samples',type=int,default=16);p.add_argument('--suffix',default='');p.add_argument('--views',default='front,oblique,rear,roof')
p.add_argument('--oidn',default='oidnDenoise')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
data=a.raw.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);meta=doc['extras'];assert meta['id']==ID
bpy.ops.import_scene.gltf(filepath=str(a.raw.resolve()))
model=[ob for ob in bpy.context.scene.objects if ob.type=='MESH'];assert len(model)==1
# Keep the original building mesh intact and the two new roof components individually editable.
body=model[0]
for material, label in [('cover frame','Eastern roof / gridded frame'),('cover panel','Eastern roof / base and fields')]:
 bpy.ops.object.select_all(action='DESELECT')
 body.select_set(True);bpy.context.view_layer.objects.active=body
 indices={s.material_index for s in body.data.polygons if body.data.materials[s.material_index].name==material}
 assert len(indices)==1
 for v in body.data.vertices:v.select=False
 for e in body.data.edges:e.select=False
 for face in body.data.polygons:face.select=face.material_index in indices
 before_split=set(bpy.data.objects);bpy.context.tool_settings.mesh_select_mode=(False,False,True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
 [section]=set(bpy.data.objects)-before_split;section.name=label
model=[ob for ob in bpy.context.scene.objects if ob.type=='MESH'];assert len(model)==3
source_sha=hashlib.sha256(data).hexdigest()
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
scene.render.resolution_x=1008;scene.render.resolution_y=672;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Preview world');scene.world.color=(.27,.27,.27)
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.unit_settings.system='METRIC'
available={'eastcover':(15,-23,40),'eastcourt':(66,-85,96),'front':(-135,-8,48),'oblique':(-110,-110,75),'rear':(125,95,65),'roof':(5,-18,170),'entrance':(-75,-1,17),'gallery':(-50,-22,29),'roofdetail':(-40,-34,47),'wing':(30,-90,32)}
views={'native-'+name:available[name] for name in a.views.split(',')}
a.previews.mkdir(parents=True,exist_ok=True);a.out.parent.mkdir(parents=True,exist_ok=True)
bpy.context.view_layer.update();corners=[ob.matrix_world@Vector(c) for ob in model for c in ob.bound_box];records=[]
for name,position in views.items():
 target=Vector((3,-1.1,10.27)) if name=='native-eastcover' else Vector((3,-1,7)) if name=='native-eastcourt' else Vector((-20,-.8,6)) if name=='native-entrance' else Vector((-13.8,-.8,14.2)) if name=='native-gallery' else Vector((-13.8,-.8,20)) if name=='native-roofdetail' else Vector((0,-27,5)) if name=='native-wing' else Vector((0,0,9))
 scope={'native-eastcover':[(-4,-6,10),(10,4.5,10.5)],'native-entrance':[(-21,-11,0),(-18,9,12.2)],'native-gallery':[(-20.4,-10,11.8),(-7.0,8.5,16.5)],'native-roofdetail':[(-22,-12,15.4),(-5,11,24.2)],'native-wing':[(-35,-35,0),(41,-22,10.7)]}.get(name)
 view_corners=[Vector((x,y,z)) for x in [scope[0][0],scope[1][0]] for y in [scope[0][1],scope[1][1]] for z in [scope[0][2],scope[1][2]]] if scope else corners
 camera.location=position;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 for k in range(30):
  bpy.context.view_layer.update();q=[world_to_camera_view(scene,camera,c) for c in view_corners]
  lo=[min(v[i] for v in q) for i in range(3)];hi=[max(v[i] for v in q) for i in range(3)]
  if lo[0]>=.04 and lo[1]>=.04 and hi[0]<=.96 and hi[1]<=.96 and lo[2]>0:break
  camera.location=target+(camera.location-target)*1.06
 else:raise AssertionError('Unable to frame actual model')
 path=a.previews/(name+a.suffix+'.png')
 records.append({'file':path.name,'camera_position':list(camera.location),'target':list(target),'bbox_ndc_min':lo,'bbox_ndc_max':hi,'framing_steps':k,'framing_scope':'specified architectural detail' if scope else 'complete model'})
selected=records[min(1,len(records)-1)];camera.location=selected['camera_position'];target=Vector(selected['target']);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
scene['candidate_id']=ID;scene['model_mesh_names']=[ob.name for ob in model];scene['candidate_metadata_json']=json.dumps(meta,ensure_ascii=False);scene['preview_stage_excluded_from_model']=True
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
assert 0<a.out.stat().st_size<100000000
bpy.ops.wm.open_mainfile(filepath=str(a.out.resolve()));reopened=[bpy.data.objects[n] for n in bpy.context.scene['model_mesh_names']]
assert geometry_hash(reopened)==before and sum(len(o.data.polygons) for o in reopened)==count
assert json.loads(bpy.context.scene['candidate_metadata_json'])==meta
scene=bpy.context.scene
for view in records:
 camera=scene.camera;camera.location=view['camera_position'];target=Vector(view['target'])
 camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
 path=a.previews/view['file'];scene.render.filepath=str(path.resolve())
 bpy.ops.render.render(write_still=True)
 view['unfiltered_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 with tempfile.TemporaryDirectory() as work:
  work=Path(work)
  subprocess.run(['magick',str(path),'-colorspace','sRGB','-endian','LSB',str(work/'render.pfm')],check=True)
  subprocess.run([a.oidn,'-d','cpu','--threads','2','--ldr',str(work/'render.pfm'),'--srgb','-o',str(work/'clean.pfm')],check=True)
  subprocess.run(['magick',str(work/'clean.pfm'),'-set','colorspace','sRGB','-depth','8',str(path)],check=True)
 view['denoiser']='Open Image Denoise CPU, LDR sRGB'
 view['rendered_after_reopen']=True;view['bytes']=path.stat().st_size
 view['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

report={'id':ID,'blender':bpy.app.version_string,'source_raw_sha256':source_sha,'model_triangles':count,'model_meshes':len(reopened),'geometry_hash_before_and_after_reopen':before,'bytes':a.out.stat().st_size,'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'actual_reopen_passed':True,'stage_excluded_from_geometry_hash':True,'previews':records}
(a.previews/'native.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
