"""Blender native export and actual Cycles previews (original model only)."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import bpy
from mathutils import Vector

parser=argparse.ArgumentParser();parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--previews',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.import_scene.gltf(filepath=str(args.raw.resolve()))
model=[o for o in bpy.context.scene.objects if o.type=='MESH']
for obj in model:
    obj['source_raw_sha256']=hashlib.sha256(args.raw.read_bytes()).hexdigest()
    obj['scope']='Physical east paifang from official text; shared photographic structure not independently bound to plaque faces. Two stone posts, open passage, one high and two low canopies,12 corners. Blank plaques;9.6m including ornaments is estimated; no geographic registration. Shared west-candidate geometry assumptions do not verify identical real details on the physical east portal.'
collection=bpy.data.collections.new('Preview stage — not part of the building');bpy.context.scene.collection.children.link(collection)
def stage(obj):
    for current in list(obj.users_collection): current.objects.unlink(obj)
    collection.objects.link(obj)
def geometry_hash(objects):
    h=hashlib.sha256()
    for obj in sorted(objects,key=lambda o:o.name):
        h.update(obj.name.encode())
        for v in obj.data.vertices:h.update(struct.pack('<3f',*v.co))
        for p in obj.data.polygons:h.update(struct.pack('<3I',*p.vertices))
    return h.hexdigest()
count=sum(len(o.data.polygons) for o in model)
raw_bytes=args.raw.read_bytes();json_size=struct.unpack_from('<I',raw_bytes,12)[0];raw_doc=json.loads(raw_bytes[20:20+json_size])
expected=sum(raw_doc['accessors'][p['indices']]['count']//3 for m in raw_doc['meshes'] for p in m['primitives'])
assert count==expected, f'Blender import changed face count: {count} vs {expected}'
before_hash=geometry_hash(model)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.1));ground=bpy.context.object;ground.name='Preview only — not surveyed ground';stage(ground)
mat=bpy.data.materials.new('Preview neutral ground');mat.diffuse_color=(.22,.25,.22,1);ground.data.materials.append(mat)
bpy.ops.object.light_add(type='AREA',location=(-12,-16,24));key=bpy.context.object;key.data.energy=2200;key.data.shape='DISK';key.data.size=12;key.rotation_euler=(Vector((0,0,2))-key.location).to_track_quat('-Z','Y').to_euler();stage(key)
bpy.ops.object.light_add(type='SUN',location=(0,0,20));sun=bpy.context.object;sun.data.energy=2.2;sun.rotation_euler=(.45,-.45,-.5);stage(sun)
bpy.ops.object.light_add(type='AREA',location=(0,-10,7));fill=bpy.context.object;fill.data.energy=700;fill.data.size=8;fill.rotation_euler=(Vector((0,0,6))-fill.location).to_track_quat('-Z','Y').to_euler();stage(fill)
bpy.ops.object.light_add(type='AREA',location=(4,9,8));backfill=bpy.context.object;backfill.data.energy=450;backfill.data.size=8;backfill.rotation_euler=(Vector((0,0,5.5))-backfill.location).to_track_quat('-Z','Y').to_euler();stage(backfill)
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='Preview camera';stage(camera);camera.data.lens=48;bpy.context.scene.camera=camera
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Preview world');scene.world.color=(.25,.25,.25);scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.unit_settings.system='METRIC'
args.previews.mkdir(parents=True,exist_ok=True);args.out.parent.mkdir(parents=True,exist_ok=True)
views={'native-front':(0,-23,7),'native-oblique':(12,-20,10),'native-rear':(-12,20,10)}
for name,position in views.items():
    camera.location=position;camera.rotation_euler=(Vector((0,0,4.7))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str((args.previews/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
camera.location=(12,-20,10);camera.rotation_euler=(Vector((0,0,4.7))-camera.location).to_track_quat('-Z','Y').to_euler()
scene['model_mesh_names']=[o.name for o in model];scene['status']='Candidate awaiting geographic registration; not approved as full historic reconstruction.'
bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()),compress=True)
assert args.out.stat().st_size<100000000
bpy.ops.wm.open_mainfile(filepath=str(args.out.resolve()))
reopened=[bpy.data.objects[name] for name in bpy.context.scene['model_mesh_names']]
assert geometry_hash(reopened)==before_hash
assert sum(len(o.data.polygons) for o in reopened)==count
report={'source_raw_sha256':hashlib.sha256(args.raw.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'model_triangles':count,'model_meshes':len(model),'geometry_hash_before_and_after_reopen':before_hash,'bytes':args.out.stat().st_size,'sha256':hashlib.sha256(args.out.read_bytes()).hexdigest(),'stage_excluded_from_geometry_hash':True,'previews':list(views)}
(args.previews/'native.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
