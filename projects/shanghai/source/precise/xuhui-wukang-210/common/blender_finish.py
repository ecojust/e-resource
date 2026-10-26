"""Import the self-contained raw GLB, save editable .blend, optionally render.

blender -b --python blender_finish.py -- --glb model.glb --output folder
Blender 4.3+; the geometry construction step separately requires Shapely/numpy.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser();ap.add_argument('--glb',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
ap.add_argument('--render',action='store_true');ap.add_argument('--view-azimuth',type=float,default=80)
ap.add_argument('--view-elevation',type=float,default=12)
ap.add_argument('--width',type=int,default=1200);ap.add_argument('--height',type=int,default=1100)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
args.output.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
model=list(bpy.context.scene.objects)
collection=bpy.data.collections.new('Photo_reconstructed_architecture');bpy.context.scene.collection.children.link(collection)
for obj in model:
 for c in list(obj.users_collection):c.objects.unlink(obj)
 collection.objects.link(obj)
points=[obj.matrix_world@Vector(v) for obj in model if obj.type=='MESH' for v in obj.bound_box]
low=Vector([min(p[i] for p in points) for i in range(3)]);high=Vector([max(p[i] for p in points) for i in range(3)])
center=(low+high)/2;extent=max(high-low)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=args.width;scene.render.resolution_y=args.height;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.world.color=(.45,.45,.45)
scene.view_settings.view_transform='AgX'
qa=bpy.data.collections.new('Preview_only');scene.collection.children.link(qa)
def preview(obj):
 for c in list(obj.users_collection):c.objects.unlink(obj)
 qa.objects.link(obj)
bpy.ops.object.light_add(type='SUN',rotation=(math.radians(32),math.radians(-28),math.radians(-25)))
sun=bpy.context.object;sun.data.energy=3.;sun.data.angle=.12;preview(sun)
bpy.ops.object.light_add(type='AREA',location=(center.x+extent*.5,center.y-extent*.7,extent*1.4))
fill=bpy.context.object;fill.data.energy=1800;fill.data.shape='DISK';fill.data.size=extent;fill.rotation_euler=(Vector(center)-fill.location).to_track_quat('-Z','Y').to_euler();preview(fill)
angle=math.radians(args.view_azimuth);elevation=math.radians(args.view_elevation)
sun.rotation_euler=Vector((-math.sin(angle)*.65,-math.cos(angle)*.65,-.8)).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(center.x+math.sin(angle)*extent*2,center.y+math.cos(angle)*extent*2,center.z+extent*2*math.tan(elevation)))
camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';scene.camera=camera;preview(camera)
# Frame the actual projected mesh, so a deep, narrow building does not become
# tiny merely because its north/south footprint dimension is large.
bpy.context.view_layer.update();inverse=camera.matrix_world.inverted()
projected=[inverse@(obj.matrix_world@v.co) for obj in model if obj.type=='MESH' for v in obj.data.vertices]
minx,maxx=min(p.x for p in projected),max(p.x for p in projected)
miny,maxy=min(p.y for p in projected),max(p.y for p in projected)
camera.location+=camera.matrix_world.to_3x3()@Vector(((minx+maxx)/2,(miny+maxy)/2,0))
camera.data.ortho_scale=1
frame=camera.data.view_frame(scene=scene)
frame_width=max(v.x for v in frame)-min(v.x for v in frame)
frame_height=max(v.y for v in frame)-min(v.y for v in frame)
camera.data.ortho_scale=max((maxx-minx)/frame_width,(maxy-miny)/frame_height)*1.12
bpy.ops.mesh.primitive_plane_add(size=extent*8,location=(center.x,center.y,-.01));plane=bpy.context.object;preview(plane)
ground=bpy.data.materials.new('Preview ground');ground.diffuse_color=(.38,.39,.37,1);plane.data.materials.append(ground)
out=args.output/(args.glb.stem+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
assert out.stat().st_size<100_000_000
if args.render:
 scene.render.filepath=str((args.output/(args.glb.stem+'-preview.png')).resolve());bpy.ops.render.render(write_still=True)
report={'blender_version':bpy.app.version_string,'native_file':out.name,'native_bytes':out.stat().st_size,
        'imported_meshes':sum(o.type=='MESH' for o in model),'bounds_blender':{'min':list(low),'max':list(high)},
        'preview_ground_plane_z_m':-.01,'model_ground_z_m':0,'qa_collection_excluded_from_source_glb':True,'rendered':args.render,
        'source_glb_sha256':hashlib.sha256(args.glb.read_bytes()).hexdigest(),
        'native_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
        'preview_camera':{'azimuth_degrees':args.view_azimuth,'elevation_degrees':args.view_elevation,'resolution':[args.width,args.height]},
        'images':[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file),
                   'packed_bytes':len(im.packed_file.data) if im.packed_file else 0,
                   'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None}
                  for im in bpy.data.images if im.name not in ('Render Result','Viewer Node')]}
(args.output/(args.glb.stem+'-blender.json')).write_text(json.dumps(report,indent=2)+'\n')
