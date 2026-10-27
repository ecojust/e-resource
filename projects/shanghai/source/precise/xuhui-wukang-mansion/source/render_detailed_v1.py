#!/usr/bin/env python3
"""Blender -b -t 2 --python render_previews.py -- --glb RAW --out NEW.
Three non-photocalibrated exterior views and an editable compressed .blend.
"""
import argparse,sys,math,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--samples',type=int,default=12);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
 if a.out.exists():raise ValueError('Use new directory')
 a.out.mkdir(parents=True)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(a.glb.resolve()))
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 coll=bpy.data.collections.new('Wukang_Main_Detailed_Exterior');scene.collection.children.link(coll)
 objects=list(scene.objects)
 for o in objects:
  for c in list(o.users_collection):c.objects.unlink(o)
  coll.objects.link(o)
 meshes=[o for o in objects if o.type=='MESH'];points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 low=Vector([min(v[i] for v in points) for i in range(3)]);high=Vector([max(v[i] for v in points) for i in range(3)]);center=(low+high)/2
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.max_bounces=4
 scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False));scene.render.threads_mode='FIXED';scene.render.threads=2
 scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=80;scene.render.resolution_percentage=100
 scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.69,.73,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
 preview=bpy.data.collections.new('Preview_Only_Excluded_From_Model_Exports');scene.collection.children.link(preview)
 def move(o):
  for c in list(o.users_collection):c.objects.unlink(o)
  preview.objects.link(o)
 bpy.ops.object.light_add(type='SUN',location=(80,-60,70));sun=bpy.context.object;move(sun);sun.rotation_euler=Vector((-.7,.4,-.7)).to_track_quat('-Z','Y').to_euler();sun.data.energy=2.8;sun.data.angle=.10
 bpy.ops.mesh.primitive_plane_add(size=450,location=(0,0,-.015));ground=bpy.context.object;move(ground);mat=bpy.data.materials.new('Neutral preview ground');mat.diffuse_color=(.39,.40,.37,1);mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.39,.40,.37,1);ground.data.materials.append(mat)
 theta=0.0
 def enu(p):
  x,y,z=p;return(x*math.cos(theta)-y*math.sin(theta),x*math.sin(theta)+y*math.cos(theta),z)
 views=[('south-east-full',(85,-100,58),(0,0,14),(1200,950),True,None),('north-west-full',(-85,100,58),(0,0,14),(1200,950),True,None),('southwest-nose-detail',(-58,-67,16),(-22,-26,14),(1200,1000),False,27),('roof-and-recesses',(58,-65,105),(0,0,23),(1200,950),True,None)]
 cams=[]
 for name,loc,target,res,fit,height in views:
  bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;move(cam);cam.name=name;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.clip_end=1000;scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;bpy.context.view_layer.update()
  cam.data.ortho_scale=1;frame=cam.data.view_frame(scene=scene);fw=max(v.x for v in frame)-min(v.x for v in frame);fh=max(v.y for v in frame)-min(v.y for v in frame)
  if fit:
   inv=cam.matrix_world.inverted();pp=[inv@v for v in points];x0,x1=min(v.x for v in pp),max(v.x for v in pp);y0,y1=min(v.y for v in pp),max(v.y for v in pp)
   cam.location+=cam.matrix_world.to_3x3()@Vector(((x0+x1)/2,(y0+y1)/2,0));cam.data.ortho_scale=max((x1-x0)/fw,(y1-y0)/fh)*1.10
  elif height:cam.data.ortho_scale=height/fh
  else:cam.data.type='PERSP';cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36;cam.data.lens=764*36/1080
  cams.append((name,cam,res))
 scene.camera=cams[0][1];scene.render.resolution_x,scene.render.resolution_y=cams[0][2]
 
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file:
   try:im.pack()
   except RuntimeError:pass
 native=a.out/'wukang-mansion.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native.resolve()),compress=True)
 if native.stat().st_size>=100000000:raise ValueError('Native file exceeds user limit')
 images=[]
 for name,cam,res in cams:
  scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;path=a.out/(name+'.png');scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True)
  images.append({'file':path.name,'bytes':path.stat().st_size,'sha256':sha(path),'camera_enu':list(cam.location),'ortho_scale':cam.data.ortho_scale,'photo_calibrated':False,'view_kind':'inferred perspective compatibility' if 'calibration' in name else 'illustrative model view','camera_type':cam.data.type,'focal_mm':cam.data.lens if cam.data.type=='PERSP' else None});print('PREVIEW_READY',str(path),flush=True)
 for mesh in meshes:mesh.data.calc_loop_triangles()
 texture_images=[{'name':im.name,'packed':bool(im.packed_file),'bytes':len(im.packed_file.data) if im.packed_file else None,'sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None} for im in bpy.data.images if im.packed_file]
 report={'raw':{'path':str(a.glb.resolve()),'bytes':a.glb.stat().st_size,'sha256':sha(a.glb)},'native':{'path':str(native.resolve()),'bytes':native.stat().st_size,'sha256':sha(native)},'bounds_enu':[list(low),list(high)],'triangles':sum(len(o.data.loop_triangles) for o in meshes),'model_meshes':len(meshes),'blender_version':bpy.app.version_string,'engine':'CYCLES CPU','samples':a.samples,'preview_ground_is_not_exported':True,'textures_embedded':bool(texture_images),'packed_source_images':texture_images,'images':images,'browser_passed':False,'human_appearance_review_passed':False,'stage':'detailed exterior review candidate; human visual acceptance pending'}
 (a.out/'native-render-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
