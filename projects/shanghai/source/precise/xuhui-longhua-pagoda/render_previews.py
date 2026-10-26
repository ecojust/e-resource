#!/usr/bin/env python3
"""Root-only Blender import/save + three honest geometry previews; no texture baking.

Blender -b -t 2 --python render_previews.py -- --glb ... --output NEW_DIRECTORY
Camera views are illustrative, not calibrated to any source photograph.
"""
import argparse,hashlib,json,math,sys
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
 parser.add_argument('--only',choices=('all','both','full','detail','low'),default='all')
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 if args.output.exists():raise ValueError('Output must be a new directory; prior native/preview evidence is immutable.')
 if args.glb.is_symlink() or not args.glb.is_file():raise ValueError('Use the actual frozen raw GLB file.')
 if not 1<=args.samples<=128 or not 1<=args.threads<=8:raise ValueError('Samples/threads outside this bounded preview scope.')
 calibration=json.loads((HERE/'calibration.json').read_text());view=calibration['preview']
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
 model=list(bpy.context.scene.objects)
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 collection=bpy.data.collections.new('Longhua_model');scene.collection.children.link(collection)
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
 scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.72
 preview_collection=bpy.data.collections.new('Preview_only_not_source_geometry');scene.collection.children.link(preview_collection)
 def preview(obj):
  for old in list(obj.users_collection):old.objects.unlink(obj)
  preview_collection.objects.link(obj)
 bpy.ops.object.light_add(type='SUN',location=(20,-30,50));sun=bpy.context.object;preview(sun)
 sun.rotation_euler=Vector((.5,-.7,-.85)).to_track_quat('-Z','Y').to_euler();sun.data.energy=2.3;sun.data.angle=math.radians(8)
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
 full,full_info=camera('Full_tower_three_quarter',center,view['azimuth_deg'],view['elevation_deg'],view['full_resolution'],fit=True)
 detail,detail_info=camera('Middle_storeys_detail',Vector((0,0,view['detail_target_z'])),view['azimuth_deg']+15,0,view['detail_resolution'],vertical_height=view['detail_ortho_height'])
 low_azimuth=math.radians(view['azimuth_deg']);low_target=Vector((0,0,view['low_target_z']))
 bpy.ops.object.camera_add(location=(math.sin(low_azimuth)*view['low_position_radius_m'],math.cos(low_azimuth)*view['low_position_radius_m'],view['low_camera_height_m']))
 low_camera=bpy.context.object;low_camera.name='Low_human_height_perspective';preview(low_camera)
 low_camera.rotation_euler=(low_target-low_camera.location).to_track_quat('-Z','Y').to_euler();low_camera.data.type='PERSP'
 low_camera.data.lens=view['low_focal_length_mm'];low_camera.data.sensor_width=36;low_camera.data.clip_start=.1;low_camera.data.clip_end=500
 low_info={'name':low_camera.name,'projection':'perspective','resolution':view['low_resolution'],'position_enu':list(low_camera.location),'target_enu':list(low_target),'focal_length_mm':low_camera.data.lens,'sensor_width_mm':36,'photo_calibrated':False,'purpose':'Human-height upward view of real roof underside/supports; no photo camera solution claimed'}
 scene.camera=full;scene.render.resolution_x,scene.render.resolution_y=view['full_resolution']
 args.output.mkdir(parents=True)
 native=args.output/'xuhui-longhua-pagoda.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(native.resolve()),compress=True)
 if native.stat().st_size>=100_000_000:raise ValueError('Native exceeds the strict single-file limit')
 images=[]
 for name,obj,info in [('full',full,full_info),('detail',detail,detail_info),('low',low_camera,low_info)]:
  if args.only!='all' and not (args.only=='both' and name in ('full','detail')) and args.only!=name:continue
  scene.camera=obj;scene.render.resolution_x,scene.render.resolution_y=info['resolution']
  png=args.output/f'xuhui-longhua-pagoda-{name}.png';scene.render.filepath=str(png.resolve());bpy.ops.render.render(write_still=True)
  images.append({'file':png.name,'bytes':png.stat().st_size,'sha256':sha(png),'camera':info})
 report={'schema':'longhua-native-render-v9','source_glb':str(args.glb.resolve()),'source_glb_sha256':sha(args.glb),'builder_sha256':sha(HERE/'build_model.py'),'calibration_sha256':sha(HERE/'calibration.json'),'renderer_sha256':sha(Path(__file__)),'blender_version':bpy.app.version_string,'engine':'CYCLES CPU','samples':args.samples,'threads':args.threads,'denoising_enabled':scene.cycles.use_denoising,'denoising_policy':'Use only when the actual Blender build provides OpenImageDenoise','native':{'file':native.name,'bytes':native.stat().st_size,'sha256':sha(native)},'bounds_enu_m':[list(low),list(high)],'model_meshes':len(meshes),'model_images':0,'preview_collection_excluded_from_raw':True,'preview_ground_z':-.025,'ground_base_m':0,'renders':images,'human_visual_review_passed':False,'browser_passed':False,'notes':'These are generated geometry previews, not human acceptance or calibrated photo matches. All three cameras are retained in the editable compressed blend.'}
 (args.output/'native-render-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'native':report['native'],'renders':images},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
