"""Bounded actual appearance review. Pack material PNGs in an editable native."""
from pathlib import Path
import hashlib,json
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'source/model-input.json').read_text())
OUT=ROOT/'final-review'
RAW=OUT/'hudec-C-full.glb'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.ops.import_scene.gltf(filepath=str(RAW))
model=[o for o in scene.objects if o.type=='MESH']
col=bpy.data.collections.new('HUDEC_C_ESTIMATED_CURRENT_EXTERIOR');scene.collection.children.link(col)
for o in model:
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o)
    o['door_height_prior_m']=2.30;o['architectural_measurement']=False
points=[o.matrix_world@v.co for o in model for v in o.data.vertices]
preview=bpy.data.collections.new('PREVIEW_ONLY_NOT_EXPORTED');scene.collection.children.link(preview)
def move(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    preview.objects.link(o)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.max_bounces=4
scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False))
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=85
scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.74,.78,.84,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
bpy.ops.object.light_add(type='SUN',location=(20,-25,30));sun=bpy.context.object;move(sun)
sun.rotation_euler=Vector((-.55,.35,-.85)).to_track_quat('-Z','Y').to_euler();sun.data.energy=2.8;sun.data.angle=.20
bpy.ops.mesh.primitive_plane_add(size=120,location=(0,0,-.035));ground=bpy.context.object;move(ground)
mat=bpy.data.materials.new('Neutral review surface');mat.diffuse_color=(.36,.38,.36,1);ground.data.materials.append(mat)
t=Vector((*D['provisional_architecture_east_axis_enu'],0));n=Vector((*D['provisional_architecture_north_axis_enu'],0))
target=-t*2.5-n*2.0+Vector((0,0,6.0))
west=t*((-3.5-1.175)*2.3)+n*((-1.2-1.325)*2.3)+Vector((0,0,7.3))
views=[('southwest-full',target-n*35-t*31+Vector((0,0,14)),target,(880,700),None),
       ('north-entry-full',target+n*40+t*8+Vector((0,0,3.0)),target,(880,700),None),
       ('west-facade-close',west-t*24-n*14+Vector((0,0,7)),west,(840,780),16.0)]
cameras=[]
for name,loc,aim,res,scale in views:
    bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;move(cam);cam.name=name
    cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.clip_end=200
    scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;bpy.context.view_layer.update()
    if scale is None:
        cam.data.ortho_scale=1;frame=cam.data.view_frame(scene=scene)
        fw=max(v.x for v in frame)-min(v.x for v in frame);fh=max(v.y for v in frame)-min(v.y for v in frame)
        pp=[cam.matrix_world.inverted()@v for v in points]
        x0,x1=min(v.x for v in pp),max(v.x for v in pp);y0,y1=min(v.y for v in pp),max(v.y for v in pp)
        cam.location+=cam.matrix_world.to_3x3()@Vector(((x0+x1)/2,(y0+y1)/2,0))
        cam.data.ortho_scale=max((x1-x0)/fw,(y1-y0)/fh)*1.10
    else:cam.data.ortho_scale=scale
    cameras.append((name,cam,res))
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file:image.pack()
scene.camera=cameras[0][1]
native=ROOT/'native-final/changning-hudec-residence.blend'
rawdoc=json.loads(RAW.read_bytes()[20:20+int.from_bytes(RAW.read_bytes()[12:16],'little')])
copyright=rawdoc['asset']['copyright']
for data in [scene,col,*model]:
    data['author']='agent';data['copyright']=copyright;data['license']='MIT'
scene['building_id']='changning-hudec-residence';scene['door_height_prior_m']=2.30
scene['height_measured']=False;scene['reference_era']='Current restoration exterior in2017/2018 sources, not a1930 measured reconstruction'
for name,content in [('LICENSE_MIT',(ROOT/'LICENSE').read_text()),('MODEL_PROVENANCE.json',json.dumps({'author':'agent','license':'MIT','raw_sha256':hashlib.sha256(RAW.read_bytes()).hexdigest(),'scale':'2.30m estimated door prior; ±0.15m are pressure cases, not measurement or confidence intervals.','scope':'Current restoration main residence and estimated service exterior; unobserved service windows omitted.','materials':'Original procedural MIT atlases by agent; no reference photograph pixels.'},ensure_ascii=False,indent=2))]:
    textblock=bpy.data.texts.new(name);textblock.write(content)
native.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
def info(p):return {'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
images=[]
for name,cam,res in cameras:
    if name!='north-entry-full':continue
    scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res
    path=OUT/'previews'/(name+'.png');path.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    images.append({**info(path),'cameraENU':list(cam.location),'projection':'orthographic','photo_calibrated':False})
    print('ACTUAL_REVIEW_PREVIEW_READY',path,flush=True)
report={'schema':'hudec-detailed-appearance-review-v1','raw':info(RAW),'native':info(native),
        'images':images,'blender_version':bpy.app.version_string,'engine':'Cycles CPU','samples':32,
        'threads':4,'raw_geometry_used_in_native':True,'preview_collection_not_in_glb':True,
        'root_visual_acceptance_pending':True,'only_new_view':'north-entry-full; prior southwest/west images remain bound to preservedreview-v2, with exact north-only geometry delta declared separately','main_modified':False,'remote_modified':False}
(OUT/'NATIVE_APPEARANCE_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
