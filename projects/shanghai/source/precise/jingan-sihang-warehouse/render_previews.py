#!/usr/bin/env python3
"""Root-only Blender import/save + three honest geometry previews; no texture baking.

Blender -b -t 2 --python render_previews.py -- --glb ... --output NEW_DIRECTORY
Camera views are illustrative, not calibrated to any source photograph.
"""
import argparse,hashlib,json,math,sys,struct
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--glb',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--samples',type=int,default=24);parser.add_argument('--threads',type=int,default=2)
 parser.add_argument('--only',choices=('all','full','detail','rear'),default='all')
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 if args.output.exists():raise ValueError('Output must be a new directory; prior native/preview evidence is immutable.')
 if args.glb.is_symlink() or not args.glb.is_file():raise ValueError('Use the actual frozen raw GLB file.')
 if not 1<=args.samples<=128 or not 1<=args.threads<=8:raise ValueError('Samples/threads outside this bounded preview scope.')
 calibration=json.loads((HERE/'calibration.json').read_text());view=calibration['preview']
 with args.glb.open('rb') as stream:
  header=stream.read(20)
  if header[:4]!=b'glTF':raise ValueError('Not a binary glTF')
  json_bytes=struct.unpack_from('<I',header,12)[0];doc=json.loads(stream.read(json_bytes).decode('utf8').rstrip(' \0'))
 extras=doc.get('extras',{})
 if extras.get('id')!='jingan-sihang-warehouse' or extras.get('calibration_sha256')!=sha(HERE/'calibration.json') or extras.get('source_freeze_sha256')!=sha(HERE/'source-freeze.json'):raise ValueError('Raw does not bind this frozen warehouse authoring source')
 if doc.get('images'):raise ValueError('No private/source photo textures belong in this warehouse raw')
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
 model=list(bpy.context.scene.objects)
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 collection=bpy.data.collections.new('Sihang_Continental_Warehouse_Model');scene.collection.children.link(collection)
 for obj in model:
  for old in list(obj.users_collection):old.objects.unlink(obj)
  collection.objects.link(obj)
 meshes=[o for o in model if o.type=='MESH']
 if not meshes:raise ValueError('Raw contains no mesh')
 points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 low=Vector([min(p[i] for p in points) for i in range(3)]);high=Vector([max(p[i] for p in points) for i in range(3)])
 center=(low+high)/2;extent=max(high-low)
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=args.samples
 scene.cycles.use_denoising=bool(getattr(bpy.app.build_options, 'openimagedenoise', False));scene.cycles.max_bounces=5;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3
 scene.render.threads_mode='FIXED';scene.render.threads=args.threads
 scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 scene.render.film_transparent=False;scene.view_settings.view_transform='AgX'
 scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.52,.55,.58,1)
 scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.95
 preview_collection=bpy.data.collections.new('Preview_only_not_source_geometry');scene.collection.children.link(preview_collection)
 def preview(obj):
  for old in list(obj.users_collection):old.objects.unlink(obj)
  preview_collection.objects.link(obj)
 bpy.ops.object.light_add(type='SUN',location=(20,-30,50));sun=bpy.context.object;preview(sun)
 sun.rotation_euler=Vector((.5,-.7,-.85)).to_track_quat('-Z','Y').to_euler();sun.data.energy=2.8;sun.data.angle=math.radians(8)
 bpy.ops.object.light_add(type='AREA',location=(-25,-20,35));fill=bpy.context.object;preview(fill)
 fill.data.energy=1200;fill.data.shape='DISK';fill.data.size=30;fill.rotation_euler=(center-fill.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.mesh.primitive_plane_add(size=extent*5,location=(center.x,center.y,-.025));ground=bpy.context.object;preview(ground)
 material=bpy.data.materials.new('Neutral_preview_ground');material.diffuse_color=(.39,.40,.375,1);material.use_nodes=True
 material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.39,.40,.375,1)
 material.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9;ground.data.materials.append(material)
 def camera(name,target,azimuth,elevation,resolution,fit=False,vertical_height=None):
  angle=math.radians(azimuth);elev=math.radians(elevation);distance=extent*2
  bpy.ops.object.camera_add(location=(target.x+math.sin(angle)*distance,target.y+math.cos(angle)*distance,target.z+math.tan(elev)*distance))
  obj=bpy.context.object;obj.name=name;preview(obj);obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
  obj.data.type='ORTHO';obj.data.clip_start=.1;obj.data.clip_end=500;scene.camera=obj
  scene.render.resolution_x,scene.render.resolution_y=resolution;bpy.context.view_layer.update()
  obj.data.ortho_scale=1;frame=obj.data.view_frame(scene=scene)
  fw=max(v.x for v in frame)-min(v.x for v in frame);fh=max(v.y for v in frame)-min(v.y for v in frame)
  if fit:
   inverse=obj.matrix_world.inverted();p=[inverse@v for v in points]
   minx,maxx=min(v.x for v in p),max(v.x for v in p);miny,maxy=min(v.y for v in p),max(v.y for v in p)
   obj.location+=obj.matrix_world.to_3x3()@Vector(((minx+maxx)/2,(miny+maxy)/2,0))
   obj.data.ortho_scale=max((maxx-minx)/fw,(maxy-miny)/fh)*1.11
  else:obj.data.ortho_scale=vertical_height/fh
  return obj,{'name':name,'projection':'orthographic','azimuth_degrees':azimuth,'elevation_degrees':elevation,'resolution':resolution,'ortho_scale':obj.data.ortho_scale,'position_enu':list(obj.location),'target_enu':list(target),'photo_calibrated':False}
 full,full_info=camera('South_east_full_compound',center,view['full_azimuth_deg'],view['full_elevation_deg'],view['full_resolution'],fit=True)
 detail,detail_info=camera('West_memorial_wall_damage',Vector(view['detail_target_enu']),view['detail_azimuth_deg'],view['detail_elevation_deg'],view['detail_resolution'],vertical_height=view['detail_ortho_height'])
 rear,rear_info=camera('North_curve_setback_sixth_floor_and_skylights',center,view['rear_azimuth_deg'],view['rear_elevation_deg'],view['rear_resolution'],fit=True)
 rear_info['scope']='Curved north boundary and two glazed atrium openings follow interpreted designer plans; northern pane counts and plant dimensions remain estimates. No calibrated aerial-photo match claimed.'
 scene.camera=full;scene.render.resolution_x,scene.render.resolution_y=view['full_resolution']
 args.output.mkdir(parents=True)
 native=args.output/'jingan-sihang-warehouse.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(native.resolve()),compress=True)
 if native.stat().st_size>=30_000_000:raise ValueError('Native exceeds30MB engineering budget; strict user limit remains100MB')
 images=[]
 for name,obj,info in [('full',full,full_info),('detail',detail,detail_info),('rear',rear,rear_info)]:
  if args.only!='all' and args.only!=name:continue
  scene.camera=obj;scene.render.resolution_x,scene.render.resolution_y=info['resolution']
  png=args.output/f'jingan-sihang-warehouse-{name}.png';scene.render.filepath=str(png.resolve());bpy.ops.render.render(write_still=True)
  images.append({'role':name,'file':png.name,'bytes':png.stat().st_size,'sha256':sha(png),'camera':info})
 report={'schema':'sihang-warehouse-native-render-v12','source_glb':str(args.glb.resolve()),'source_glb_sha256':sha(args.glb),'source_glb_bytes':args.glb.stat().st_size,'source_freeze_sha256':sha(HERE/'source-freeze.json'),'builder_sha256':sha(HERE/'build_model.py'),'calibration_sha256':sha(HERE/'calibration.json'),'renderer_sha256':sha(Path(__file__)),'blender_version':bpy.app.version_string,'engine':'CYCLES CPU','samples':args.samples,'threads':args.threads,'denoising_enabled':scene.cycles.use_denoising,'denoising_policy':'Use only when the actual Blender build provides OpenImageDenoise','native':{'file':native.name,'bytes':native.stat().st_size,'sha256':sha(native)},'bounds_enu_m':[list(low),list(high)],'model_meshes':len(meshes),'model_images':sum(1 for image in bpy.data.images if image.source=='FILE' and bool(image.filepath)),'preview_collection_excluded_from_raw':True,'preview_ground_z':-.025,'ground_base_m':0,'images':images,'human_visual_review_passed':False,'browser_passed':False,'notes':'These are generated geometry previews, not human acceptance or calibrated photo matches. All three cameras are retained in the editable compressed blend.'}
 (args.output/'native-render-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'native':report['native'],'images':images},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
