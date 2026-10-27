"""Import actual raw GLB without material rewrites; native package and previews."""
import json,hashlib,math
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent.parent
ASSET_METADATA=json.loads((ROOT/'source/asset-metadata.json').read_text())
D=json.loads((ROOT/'source/design-input.json').read_text());f=D['frame'];xx=f['architecture_X_EN'];yy=f['architecture_Y_EN']
R=Matrix(((xx[0],yy[0],0),(xx[1],yy[1],0),(0,0,1)))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports/bajin-main-detailed.glb'))
items=list(scene.objects);col=bpy.data.collections.new('MODEL_BAJIN_MAIN_HOUSE_ENU');scene.collection.children.link(col)
for o in items:
    for cc in list(o.users_collection):cc.objects.unlink(o)
    col.objects.link(o);o['author']='agent';o['copyright']=ASSET_METADATA['copyright'];o['coordinate_frame']='Anchor local ENU, rotation baked';o['scope']='Main house exterior, estimated heights and hidden roof'
preview=bpy.data.collections.new('PREVIEW_ONLY_NOT_BUILDING_OR_GARDEN');scene.collection.children.link(preview)
def move(o):
    for cc in list(o.users_collection):cc.objects.unlink(o)
    preview.objects.link(o)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.max_bounces=5
scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False));scene.render.threads_mode='FIXED';scene.render.threads=2
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=80
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.78,.82,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
bpy.ops.object.light_add(type='SUN',location=R@Vector((-15,-20,28)));sun=bpy.context.object;move(sun)
sun.rotation_euler=(R@Vector((.4,.45,-.8))).to_track_quat('-Z','Y').to_euler();sun.data.energy=2.0;sun.data.angle=.20
bpy.ops.mesh.primitive_plane_add(size=90,location=(0,0,-.04));ground=bpy.context.object;move(ground);ground.name='Preview ground, not modeled garden'
mat=bpy.data.materials.new('Neutral preview floor');mat.diffuse_color=(.32,.35,.32,1);ground.data.materials.append(mat)
views=[('garden',(0,-40,7),(0,0,6),(1040,900)),('north-entry',(0,40,7),(0,0,6),(1040,900)),('north-entry-oblique',(8,23,9),(0,6.7,2.0),(1050,1000))]
cams=[]
points=[o.matrix_world@v.co for o in items if o.type=='MESH' for v in o.data.vertices]
for name,loc,aim,res in views:
    bpy.ops.object.camera_add(location=R@Vector(loc));cam=bpy.context.object;move(cam);cam.name='Preview '+name
    cam.rotation_euler=(R@Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.clip_end=200
    scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100;bpy.context.view_layer.update()
    if name=='north-entry-oblique':cam.data.ortho_scale=7.9
    else:
        cam.data.ortho_scale=1;cf=cam.data.view_frame(scene=scene);fw=max(v.x for v in cf)-min(v.x for v in cf);fh=max(v.y for v in cf)-min(v.y for v in cf)
        pp=[cam.matrix_world.inverted()@p for p in points];x0,x1=min(p.x for p in pp),max(p.x for p in pp);y0,y1=min(p.y for p in pp),max(p.y for p in pp)
        cam.location+=cam.matrix_world.to_3x3()@Vector(((x0+x1)/2,(y0+y1)/2,0));cam.data.ortho_scale=max((x1-x0)/fw,(y1-y0)/fh)*1.13
    cams.append((name,cam,res))
scene.camera=cams[2][1];scene['author']='agent';scene['copyright']=ASSET_METADATA['copyright'];col['copyright']=ASSET_METADATA['copyright']
scene['anchor_lonlat']=f['anchor'];scene['coordinate_frame']='Anchor-local East/North/Up, GLB rotation baked, heading zero';scene['scope']='Exterior main house only. Dimensions and hidden roof estimates; unobserved flank openings omitted.'
scene['native_AO']='glTF Material Output Occlusion export-preservation route retained; not native Principled AO shading equivalence.'
scene['acceptance']='Pending root and independent QA review; not installed'
for img in bpy.data.images:
    if img.source=='FILE' and not img.packed_file:img.pack()
(ROOT/'review/native').mkdir(parents=True,exist_ok=True);native=ROOT/'review/native/bajin-main-house.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
def desc(p):return {'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
images=[]
for name,cam,res in cams:
    scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;p=ROOT/'review/previews'/f'{name}.png';scene.render.filepath=str(p)
    bpy.ops.render.render(write_still=True);images.append({**desc(p),'camera_ENU':list(cam.location),'orthographic':True,'photo_calibrated':False});print('PREVIEW_READY',name,flush=True)
report={'native':desc(native),'raw_input':desc(ROOT/'exports/bajin-main-detailed.glb'),'images':images,'blender':bpy.app.version_string,'samples':24,'render_engine':'Cycles CPU','model_collection':col.name,'preview_collection':preview.name,'no_native_material_rewrite':True,'copyright':ASSET_METADATA['copyright'],'packed_images':len([i for i in bpy.data.images if i.packed_file]),'normal_and_AO_require_independent_QA':True}
(ROOT/'review/native-render-report.json').write_text(json.dumps(report,indent=2)+'\n');print('NATIVE_READY',native,flush=True)
