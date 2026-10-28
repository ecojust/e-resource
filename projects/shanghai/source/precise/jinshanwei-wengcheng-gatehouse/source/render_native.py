"""Import actual GLB, save editable native and three neutral previews. agent, MIT."""
from pathlib import Path
import hashlib
import json
import os
import sys
import struct
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'source/design-input.json').read_text())
f=D['frame'];xx=f['architecture_X_EN'];yy=f['architecture_Y_EN']
R=Matrix(((xx[0],yy[0],0),(xx[1],yy[1],0),(0,0,1)))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
raw=ROOT/'exports/jinshanwei-gatehouse-raw.glb'
raw_bytes=raw.read_bytes();raw_doc=json.loads(raw_bytes[20:20+struct.unpack_from('<I',raw_bytes,12)[0]])
raw_copyright=raw_doc['asset']['copyright']
bpy.ops.import_scene.gltf(filepath=str(raw))
items=list(scene.objects)
model=bpy.data.collections.new('MODEL_JINSHANWEI_GATEHOUSE_ENU');scene.collection.children.link(model)
for ob in items:
    for collection in list(ob.users_collection):collection.objects.unlink(ob)
    model.objects.link(ob);ob['author']='agent';ob['scope']=D['scope'];ob['dimensions_estimated']=True
    ob['copyright']=raw_copyright;ob['license']='Original geometry and materials: MIT; plaque glyphs: SIL OFL1.1'
preview=bpy.data.collections.new('PREVIEW_ONLY_NOT_PARK_MODEL');scene.collection.children.link(preview)
def move(ob):
    for collection in list(ob.users_collection):collection.objects.unlink(ob)
    preview.objects.link(ob)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.max_bounces=5
scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False))
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=85
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.74,.78,.82,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
bpy.ops.object.light_add(type='SUN',location=R@Vector((-30,-35,55)));sun=bpy.context.object;move(sun)
sun.rotation_euler=(R@Vector((.35,.45,-.82))).to_track_quat('-Z','Y').to_euler();sun.data.energy=2.2;sun.data.angle=.18
bpy.ops.mesh.primitive_plane_add(size=160,location=(0,0,-.05));ground=bpy.context.object;move(ground);ground.name='Neutral preview floor, not a modeled park'
mat=bpy.data.materials.new('Neutral preview floor');mat.diffuse_color=(.29,.31,.29,1);ground.data.materials.append(mat)
views=[('ground-front-perspective',(0,-80,3.5),(0,-16,9),(1000,706)),
       ('north-east-oblique',(-70,-70,48),(0,0,8.5),(1000,850)),
       ('rear-high',(60,70,60),(0,0,8.5),(1000,850))]
points=[ob.matrix_world@v.co for ob in items if ob.type=='MESH' for v in ob.data.vertices]
cameras=[]
for name,location,aim,resolution in views:
    bpy.ops.object.camera_add(location=R@Vector(location));cam=bpy.context.object;move(cam);cam.name='Preview '+name
    cam.rotation_euler=(R@Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP' if name=='ground-front-perspective' else 'ORTHO';cam.data.clip_end=400
    if name=='ground-front-perspective':cam.data.lens=50;cam.data.sensor_width=36
    scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=resolution;scene.render.resolution_percentage=100;bpy.context.view_layer.update()
    if name!='ground-front-perspective':
        cam.data.ortho_scale=1;frame=cam.data.view_frame(scene=scene)
        fw=max(v.x for v in frame)-min(v.x for v in frame);fh=max(v.y for v in frame)-min(v.y for v in frame)
        q=[cam.matrix_world.inverted()@p for p in points];x0,x1=min(p.x for p in q),max(p.x for p in q);y0,y1=min(p.y for p in q),max(p.y for p in q)
        cam.location+=cam.matrix_world.to_3x3()@Vector(((x0+x1)/2,(y0+y1)/2,0));cam.data.ortho_scale=max((x1-x0)/fw,(y1-y0)/fh)*1.12
    cameras.append((name,cam,resolution))
scene.camera=cameras[1][1];scene['author']='agent';scene['anchor_lonlat']=f['anchor'];scene['scope']=D['scope'];scene['coordinate_frame']='Anchor-local ENU; baked architecture rotation; metres'
scene['dimensions']='Imagery-derived estimates, not surveyed geometry';scene['acceptance']='Draft for independent review; not installed or published'
scene['copyright']=raw_copyright;scene['license']='Original geometry and materials: MIT; plaque glyphs: SIL OFL1.1'
scene['raw_glb_sha256']=hashlib.sha256(raw_bytes).hexdigest()
model['author']='agent';model['copyright']=raw_copyright;model['license']=scene['license']
model['anchor_lonlat']=f['anchor'];model['coordinate_frame']=scene['coordinate_frame'];model['units']='metres'
scene['native_AO']='glTF exporter occlusion preservation route retained; not Principled AO shading equivalence.'
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file:image.pack()
(ROOT/'review/native').mkdir(parents=True,exist_ok=True);(ROOT/'review/previews').mkdir(parents=True,exist_ok=True)
native=ROOT/'review/native/jinshanwei-gatehouse.blend'
replace_draft='--replace-unaccepted-draft' in sys.argv
if native.exists() and (not replace_draft or native.stat().st_nlink!=1):raise FileExistsError('Use a fresh native output or explicit independent-draft replacement')
native_temp=ROOT/'review/native/.jinshanwei-gatehouse.pending.blend'
if native_temp.exists():raise FileExistsError(native_temp)
bpy.ops.wm.save_as_mainfile(filepath=str(native_temp),compress=True);os.replace(native_temp,native)
def desc(p):return {'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
images=[]
for name,cam,res in cameras:
    scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res
    p=ROOT/'review/previews'/f'{name}.png';scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    images.append({**desc(p),'camera_ENU':list(cam.location),'orthographic':cam.data.type=='ORTHO','lens_mm':cam.data.lens if cam.data.type=='PERSP' else None,'photo_calibrated':False,'dimensions_px':list(res)})
    print('PREVIEW_READY',name,flush=True)
report={'native':desc(native),'raw_input':desc(raw),'images':images,'blender':bpy.app.version_string,'render_engine':'Cycles CPU','samples':24,'model_collection':model.name,'preview_collection':preview.name,'native_material_rewrite':False,'packed_images':len([im for im in bpy.data.images if im.packed_file]),'no_park_or_interior_model':True,'review_pending':True}
(ROOT/'review/native-render-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())<35_000_000
print('NATIVE_READY',native,flush=True)
