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
sys.path.insert(0,str(HERE))
from run_root import verify_source

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def projected_perspective_envelope(points,position,target,azimuth_degrees,tan_half_x,tan_half_y):
 """Pure math ENU projection; values +/-1 are the perspective frame edges."""
 a=math.radians(azimuth_degrees);sa,ca=math.sin(a),math.cos(a)
 horizontal=math.hypot(target[0]-position[0],target[1]-position[1])
 rise=target[2]-position[2];length=math.hypot(horizontal,rise)
 if length<=0 or tan_half_x<=0 or tan_half_y<=0:raise ValueError('Invalid perspective camera')
 c,s=horizontal/length,rise/length
 right=(-ca,sa,0.);up=(sa*s,ca*s,c);forward=(-sa*c,-ca*c,s)
 xmin=ymin=minimum_depth=math.inf;xmax=ymax=-math.inf;count=0
 for point in points:
  q=tuple(float(point[i])-position[i] for i in range(3))
  depth=sum(q[i]*forward[i] for i in range(3));minimum_depth=min(minimum_depth,depth);count+=1
  if depth<=0:return {'all_in_front':False,'point_count':count,'minimum_depth_m':minimum_depth,'maximum_absolute_frame_coordinate':math.inf}
  x=sum(q[i]*right[i] for i in range(3))/(depth*tan_half_x)
  y=sum(q[i]*up[i] for i in range(3))/(depth*tan_half_y)
  xmin=min(xmin,x);xmax=max(xmax,x);ymin=min(ymin,y);ymax=max(ymax,y)
 if not count:raise ValueError('Perspective fit needs actual mesh points')
 return {'all_in_front':True,'point_count':count,'minimum_depth_m':minimum_depth,'frame_x':[xmin,xmax],'frame_y':[ymin,ymax],'maximum_absolute_frame_coordinate':max(abs(xmin),abs(xmax),abs(ymin),abs(ymax))}

def fit_eye_level_perspective(low,high,azimuth_degrees,resolution):
 """Fit eight corners of the actual ENU mesh AABB; no source-photo calibration.

 The fixed eye is 1.7 m above model ground z=0. Target height is an explicitly
 estimated 45% of the actual vertical envelope. A conservative AABB fit is
 subsequently checked against every imported model vertex by the caller.
 """
 low=tuple(float(v) for v in low);high=tuple(float(v) for v in high)
 if len(low)!=3 or len(high)!=3 or any(not math.isfinite(v) for v in (*low,*high)) or any(high[i]<=low[i] for i in range(3)):raise ValueError('Finite nondegenerate actual bounds required')
 if len(resolution)!=2 or min(resolution)<=0 or not math.isfinite(azimuth_degrees):raise ValueError('Invalid perspective view inputs')
 eye_height=1.7;lens=45.;sensor_width=36.;margin=1.11
 target=((low[0]+high[0])/2,(low[1]+high[1])/2,low[2]+.45*(high[2]-low[2]))
 tanx=sensor_width/(2*lens);tany=tanx*resolution[1]/resolution[0]
 angle=math.radians(azimuth_degrees);sa,ca=math.sin(angle),math.cos(angle)
 corners=[(x,y,z) for x in (low[0],high[0]) for y in (low[1],high[1]) for z in (low[2],high[2])]
 limit=1/margin
 def at(distance):
  position=(target[0]+sa*distance,target[1]+ca*distance,eye_height)
  envelope=projected_perspective_envelope(corners,position,target,azimuth_degrees,tanx,tany)
  return position,envelope
 def fits(envelope):return envelope['all_in_front'] and envelope['minimum_depth_m']>.2 and envelope['maximum_absolute_frame_coordinate']<=limit
 lower=0.;upper=max(high[i]-low[i] for i in range(3))
 for _ in range(32):
  if fits(at(upper)[1]):break
  lower=upper;upper*=2
 else:raise ValueError('Could not fit actual model envelope with bounded camera backoff')
 for _ in range(48):
  middle=(lower+upper)/2
  if fits(at(middle)[1]):upper=middle
  else:lower=middle
 distance=upper*1.000001;position,envelope=at(distance)
 if not fits(envelope):raise ValueError('Final perspective envelope failed fit')
 return {'position_enu':list(position),'target_enu':list(target),'azimuth_degrees':azimuth_degrees,'elevation_degrees':math.degrees(math.atan2(target[2]-eye_height,distance)),'eye_height_above_ground_m':eye_height,'ground_z_m':0.,'lens_mm':lens,'sensor_width_mm':sensor_width,'sensor_fit':'HORIZONTAL','tan_half_x':tanx,'tan_half_y':tany,'horizontal_target_distance_m':distance,'target_vertical_envelope_fraction_estimate':.45,'frame_margin_factor':margin,'conservative_actual_aabb_projection':envelope,'fit_policy':'Eight corners of imported model ENU bounds, bounded backoff and binary refinement; then all actual mesh vertices checked. No photo-derived camera calibration.'}

def main():
 verify_source()
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
  magic,version,size=struct.unpack('<4sII',stream.read(12));length,kind=struct.unpack('<II',stream.read(8));doc=json.loads(stream.read(length))
 if magic!=b'glTF' or version!=2 or kind!=0x4e4f534a:raise ValueError('Actual glTF2 binary required')
 if doc.get('extras',{}).get('id')!='jiading-shanghai-auto-museum':raise ValueError('Wrong model identity')
 if doc['extras'].get('calibration_sha256')!=sha(HERE/'calibration.json'):raise ValueError('Raw does not bind current frozen calibration')
 if doc['extras'].get('source_geometry_sha256')!=sha(HERE/'geometry-input.json'):raise ValueError('Raw source owner mismatch')
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
 model=list(bpy.context.scene.objects)
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 collection=bpy.data.collections.new('Shanghai_Auto_Museum_model');scene.collection.children.link(collection)
 for obj in model:
  for old in list(obj.users_collection):old.objects.unlink(obj)
  collection.objects.link(obj)
 meshes=[o for o in model if o.type=='MESH']
 if not meshes:raise ValueError('Raw contains no mesh')
 points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 low=Vector([min(p[i] for p in points) for i in range(3)]);high=Vector([max(p[i] for p in points) for i in range(3)])
 center=(low+high)/2;extent=max(high-low)
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=args.samples
 scene.cycles.use_denoising=bool(getattr(bpy.app.build_options, 'openimagedenoise', False));scene.cycles.max_bounces=8;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=4;scene.cycles.transmission_bounces=8
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
 full_info=fit_eye_level_perspective(low,high,view['full_azimuth_deg'],view['full_resolution'])
 bpy.ops.object.camera_add(location=full_info['position_enu']);full=bpy.context.object;full.name='West_forecourt_eye_level_whole_museum';preview(full)
 full.rotation_euler=(Vector(full_info['target_enu'])-full.location).to_track_quat('-Z','Y').to_euler()
 full.data.type='PERSP';full.data.lens=full_info['lens_mm'];full.data.sensor_width=full_info['sensor_width_mm'];full.data.sensor_fit='HORIZONTAL'
 full.data.clip_start=.1;full.data.clip_end=max(500.,full_info['horizontal_target_distance_m']+extent*4)
 scene.camera=full;scene.render.resolution_x,scene.render.resolution_y=view['full_resolution'];bpy.context.view_layer.update()
 # Query Blender's actual lens frame to verify the pure-math aspect convention.
 frame=full.data.view_frame(scene=scene)
 actual_tanx=max(abs(v.x/v.z) for v in frame);actual_tany=max(abs(v.y/v.z) for v in frame)
 if not math.isclose(actual_tanx,full_info['tan_half_x'],rel_tol=1e-6) or not math.isclose(actual_tany,full_info['tan_half_y'],rel_tol=1e-6):raise ValueError('Blender perspective sensor/aspect differs from fitted frame')
 inverse=full.matrix_world.inverted();xmin=ymin=minimum_depth=math.inf;xmax=ymax=-math.inf
 for point in points:
  local=inverse@point;depth=-local.z;minimum_depth=min(minimum_depth,depth)
  if depth<=full.data.clip_start or depth>=full.data.clip_end:raise ValueError('Actual mesh vertex lies outside full camera clipping range')
  px=local.x/(depth*actual_tanx);py=local.y/(depth*actual_tany)
  xmin=min(xmin,px);xmax=max(xmax,px);ymin=min(ymin,py);ymax=max(ymax,py)
 actual_envelope={'point_count':len(points),'minimum_depth_m':minimum_depth,'frame_x':[xmin,xmax],'frame_y':[ymin,ymax],'maximum_absolute_frame_coordinate':max(abs(xmin),abs(xmax),abs(ymin),abs(ymax))}
 if actual_envelope['maximum_absolute_frame_coordinate']>1/full_info['frame_margin_factor']+1e-6:raise ValueError('Actual Blender mesh projection violates conservative full-camera fit')
 full_info.update({'name':full.name,'projection':'perspective','resolution':view['full_resolution'],'actual_blender_vertex_projection':actual_envelope,'photo_calibrated':False,'scope':'West forecourt at fixed 1.7 m eye height with 45 mm lens. Target at estimated 45% vertical-envelope height. Camera retreats to fit actual model; no measured source-photo camera or photographic match is claimed.'})
 detail,detail_info=camera('North_wrapped_shell_and_deep_entry_soffit',Vector(view['detail_target_enu']),view['detail_azimuth_deg'],view['detail_elevation_deg'],view['detail_resolution'],vertical_height=view['detail_ortho_height_m'])
 rear,rear_info=camera('Waterside_curved_end_and_external_stair',center,view['rear_azimuth_deg'],view['rear_elevation_deg'],view['rear_resolution'],fit=True)
 for role,info in [('full',full_info),('detail',detail_info),('rear',rear_info)]:info['camera_role']=role
 rear_info['scope']='2016 waterside photograph supports this facade and external stair; view is illustrative, not calibrated. Unseen roof and exact detail positions remain estimates.'
 scene.camera=full;scene.render.resolution_x,scene.render.resolution_y=view['full_resolution']
 args.output.mkdir(parents=True)
 native=args.output/'jiading-shanghai-auto-museum.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(native.resolve()),compress=True)
 if native.stat().st_size>=30_000_000:raise ValueError('Native exceeds30MB authorbudget; review packaging before further renders')
 images=[]
 for name,obj,info in [('full',full,full_info),('detail',detail,detail_info),('rear',rear,rear_info)]:
  if args.only!='all' and args.only!=name:continue
  scene.camera=obj;scene.render.resolution_x,scene.render.resolution_y=info['resolution']
  png=args.output/f'jiading-shanghai-auto-museum-{name}.png';scene.render.filepath=str(png.resolve());bpy.ops.render.render(write_still=True)
  images.append({'file':png.name,'bytes':png.stat().st_size,'sha256':sha(png),'camera':info})
 report={'schema':'auto-museum-native-render-v11','protected_roles':['north_curved_glazed_slots','silver_C_wrapper','deep_soffit','stepped_curtain_layers','yellow_ramp_bands','open_louvres','ground_entry','exterior_stair','fourth_level_terrace'],'source_glb':str(args.glb.resolve()),'source_glb_sha256':sha(args.glb),'builder_sha256':sha(HERE/'build_model.py'),'calibration_sha256':sha(HERE/'calibration.json'),'renderer_sha256':sha(Path(__file__)),'blender_version':bpy.app.version_string,'engine':'CYCLES CPU','samples':args.samples,'threads':args.threads,'denoising_enabled':scene.cycles.use_denoising,'denoising_policy':'Use only when the actual Blender build provides OpenImageDenoise','native':{'file':native.name,'bytes':native.stat().st_size,'sha256':sha(native)},'bounds_enu_m':[list(low),list(high)],'model_meshes':len(meshes),'model_images':sum(1 for image in bpy.data.images if image.source=='FILE' and bool(image.filepath)),'preview_collection_excluded_from_raw':True,'preview_ground_z':-.025,'ground_base_m':0,'renders':images,'human_visual_review_passed':False,'browser_passed':False,'notes':'Generated five-floor modern museum geometry previews; no photo textures. Cameras are illustrative, not calibrated. Exact source image bytes are not embedded. All three cameras are retained in the compressed editable blend.'}
 (args.output/'native-render-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'native':report['native'],'renders':images},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
