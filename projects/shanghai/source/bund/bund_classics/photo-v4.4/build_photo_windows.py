"""Selective real-photo appearance on the existing Bund17 3-D glazing.
Run with Blender4.3: blender -b -t2 --python build_photo_windows.py -- --project /path/to/shanghai --output /path/to/output [--render]
Original photograph pixels/bytes are retained. Only selected glazing fronts and
internal frame bars are calibrated after conforming wall topology and roof corrections.
The default cleaned baseline is generated from the separately retained original baseline.
"""
import bpy,json,math,hashlib,argparse,sys,struct
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from glb_provenance import COPYRIGHT,retain_provenance
ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--output',type=Path,default=HERE/'output');ap.add_argument('--render',action='store_true');ap.add_argument('--base-model',type=Path,default=HERE/'bund17-clean-base.blend');ap.add_argument('--views',default='front,oblique,window-detail');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
P=args.project;OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
config=json.loads((HERE/'window-controls.json').read_text());windows=config['windows']
for w in windows:
 w['active']=w['id']!='row1-centre'
 if not w['active']:w['skipReason']='Carved stone relief occludes the lower reference glazing; retain complete original window instead of stretching visible upper image.'
bpy.ops.wm.open_mainfile(filepath=str(args.base_model))
source=json.loads((HERE/'news-footprint.json').read_text());poly=source['polygon_local_east_north'];A=Vector((*poly[2],0));B=Vector((*poly[3],0));T=(B-A).normalized();N=Vector((T.y,-T.x,0));C=(A+B)*.5;UP=Vector((0,0,1))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('bund17'));old=obj.data;old.update();materials=list(old.materials)
glass_index=next(i for i,m in enumerate(materials) if m.name.startswith('recessed blue grey glazing'));frame_index=next(i for i,m in enumerate(materials) if m.name.startswith('painted window frames'));trim_index=next(i for i,m in enumerate(materials) if m.name.startswith('carved pale stone'))
photo=P/'assets/references/bund/bund17.jpg';source_sha=hashlib.sha256(photo.read_bytes()).hexdigest();image=bpy.data.images.load(str(photo),check_existing=True);image.pack()
photo_mat=bpy.data.materials.new('PhotoFacade_Bund17_Glazing');photo_mat.use_nodes=True;bs=photo_mat.node_tree.nodes.get('Principled BSDF');tex=photo_mat.node_tree.nodes.new('ShaderNodeTexImage');tex.name='Unmodified Suicasmo CC0 original';tex.image=image;tex.interpolation='Linear';tex.extension='EXTEND';photo_mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.82
photo_meta={'exifOrientation':6,'rawSize':[5184,3456],'orientedSize':[3456,5184],'uvConvention':'stored-pixels','sourceSha256':source_sha}
photo_mat['photographicSource']=photo_meta;photo_mat['photographer']='Suicasmo';photo_mat['photoLicense']='CC0-1.0'
new_frame=materials[frame_index].copy();new_frame.name='PhotoMatched_window_frames';new_frame.diffuse_color=(.045,.052,.05,1);nbs=new_frame.node_tree.nodes.get('Principled BSDF');nbs.inputs['Base Color'].default_value=(.045,.052,.05,1);nbs.inputs['Roughness'].default_value=.62;nbs.inputs['Metallic'].default_value=.10
photo_index=len(materials);materials.append(photo_mat);new_frame_index=len(materials);materials.append(new_frame)
stone_index=next(i for i,m in enumerate(materials) if m.name=='limestone')
recess_mat=materials[glass_index].copy();recess_mat.name='Roof_tower_and_attic_interior_shade';recess_mat.diffuse_color=(.018,.021,.020,1);rbs=recess_mat.node_tree.nodes.get('Principled BSDF');rbs.inputs['Base Color'].default_value=(.018,.021,.020,1);rbs.inputs['Roughness'].default_value=.9;rbs.inputs['Metallic'].default_value=0;recess_index=len(materials);materials.append(recess_mat)
verts=[tuple(v.co) for v in old.vertices];faces=[];face_mats=[];smooth=[];face_uv=[];removed={'glass_front':0,'old_frame_polygons':0,'overlapping_triplet_trim':0,'open_roof_tower_polygons':0};unchanged=[]
def local(p):
 v=Vector(p)-C;return v.dot(T),v.dot(N),p[2]
def belongs(coords,w,tolerance=.0005):
 lo,hi=w['model_z'];u=w['model_centre_u'];width=w['model_width'];return all(u-width/2-tolerance<=x<=u+width/2+tolerance and lo-tolerance<=z<=hi+tolerance for x,d,z in coords)
# Primitive components remain disconnected in the original batched mesh.
# Select complete roof components rather than cutting individual high faces of
# the pediments, which cross the tower-plinth height.
parents=list(range(len(old.vertices)))
def find(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
def union(a,b):
 a=find(a);b=find(b)
 if a!=b:parents[b]=a
for f in old.polygons:
 for v in f.vertices[1:]:union(f.vertices[0],v)
groups={}
for f in old.polygons:
 g=groups.setdefault(find(f.vertices[0]),{'vertices':set(),'materials':set()});g['vertices'].update(f.vertices);g['materials'].add(f.material_index)
roof_vertices=set();pediment_vertices=set();wing_axis=(B-A).length/2-3.55/2
for g in groups.values():
 coords=[local(old.vertices[i].co) for i in g['vertices']];us,ds,zs=zip(*coords)
 if min(zs)>=34.065 and g['materials'].issubset({stone_index,trim_index}):roof_vertices.update(g['vertices'])
 elif min(zs)>=33.30 and max(zs)<=34.80 and min(ds)>=-.621 and max(ds)<=-.179 and g['materials']=={trim_index}:
  if any(all(abs(u-side*wing_axis)<2.05 for u in us) for side in [-1,1]):pediment_vertices.update(g['vertices'])
assert roof_vertices and len(pediment_vertices)==48,(len(roof_vertices),len(pediment_vertices))
for index in pediment_vertices:verts[index]=tuple(Vector(verts[index])+N*.98)
attic_shaded_faces=0
fronts={w['id']:[] for w in windows if w['active']}
for face in old.polygons:
 if face.vertices[0] in roof_vertices:removed['open_roof_tower_polygons']+=1;continue
 coords=[local(old.vertices[i].co) for i in face.vertices];matched=None
 # Existing triplet side trims overlap: +/-0.84 and +/-0.85m centres,
 # both0.18m wide at the exact same depth. Replace the pair by one jamb.
 duplicate=False
 if face.material_index==trim_index:
  for row in range(5):
   lo=9.4+row*3.51+.68;hi=9.4+row*3.51+3.51-.62
   if all(.744<abs(u)<.946 and -.051<d<.131 and lo-.051<z<hi+.051 for u,d,z in coords):duplicate=True;break
 if duplicate:removed['overlapping_triplet_trim']+=1;continue
 for w in windows:
  if w['active'] and belongs(coords,w):matched=w;break
 if matched and face.material_index==glass_index and face.normal.dot(N)>.99 and all(-.229<d<-.226 for x,d,z in coords):
  fronts[matched['id']].append(face.index);removed['glass_front']+=1;continue
 if matched and face.material_index==frame_index and all(-.211<d<-.129 for x,d,z in coords):
  removed['old_frame_polygons']+=1;continue
 mapped_mat=face.material_index
 if face.material_index==glass_index and all(28.9<z<33.71 and -2.10<d<-1.90 for u,d,z in coords):mapped_mat=recess_index;attic_shaded_faces+=1
 faces.append(tuple(face.vertices));face_mats.append(mapped_mat);smooth.append(face.use_smooth);face_uv.append([(0,0)]*len(face.vertices));unchanged.append(face.index)
assert len(fronts)==24 and all(fronts.values()),fronts
assert removed['overlapping_triplet_trim']==240,removed

closed_primitive_volumes=[]
def add_geom(points,polys,mat,uvs=None):
 edges={}
 for f in polys:
  for a,b in zip(f,f[1:]+f[:1]):
   key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
 if edges and all(v==2 for v in edges.values()):
  volume=0.0
  for f in polys:
   a=Vector(points[f[0]])
   for i in range(1,len(f)-1):volume+=a.dot(Vector(points[f[i]]).cross(Vector(points[f[i+1]])))/6
  assert volume>1e-8,('new closed primitive winding',mat,volume)
  closed_primitive_volumes.append(volume)
 base=len(verts);verts.extend([tuple(p) for p in points])
 for f in polys:
  faces.append(tuple(base+i for i in f));face_mats.append(mat);smooth.append(False);face_uv.append([uvs[i] for i in f] if uvs else [(0,0)]*len(f))
def box(u,z,w,h,depth=.036,d=-.193,mat=None):
 axes=[T,N,UP];center=C+T*u+N*d+UP*z
 ps=[center+T*a*w/2+N*b*depth/2+UP*c*h/2 for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 # T/outward/up is left handed; preserve outward winding.
 fs=[f[:1]+tuple(reversed(f[1:])) for f in fs];add_geom(ps,fs,new_frame_index if mat is None else mat)
for row in range(5):
 lo=9.4+row*3.51+.68;hi=9.4+row*3.51+3.51-.62
 for side in [-1,1]:box(side*.845,(lo+hi)/2,.18,hi-lo+.10,depth=.18,d=.04,mat=trim_index)
def front_prism(centre_u,outline,d_front,d_back,material):
 points=[C+T*(centre_u+u)+N*d+UP*z for d in [d_front,d_back] for u,z in outline];n=len(outline)
 # Outline CCW in u/z has its front normal along N.
 fs=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
 fs.extend(((i+1)%n,i,i+n,(i+1)%n+n) for i in range(n));add_geom(points,fs,material)
def engaged_column(u,d,z0,z1,r=.13):
 profile=[(z0,r*1.35),(z0+.12,r*1.35),(z0+.22,r),(z1-.23,r*.88),(z1-.12,r*1.25),(z1,r*1.25)];segments=32;points=[]
 for z,rad in profile:
  for j in range(segments):
   a=j*math.tau/segments;flute=1-.035*(1+math.cos(a*12));points.append(C+T*(u+rad*math.cos(a)*flute)+N*(d+rad*math.sin(a)*flute)+UP*z)
 fs=[]
 for k in range(len(profile)-1):
  for j in range(segments):a=k*segments+j;b=k*segments+(j+1)%segments;fs.append((a,b,b+segments,a+segments))
 fs.extend([tuple(range(segments-1,-1,-1)),tuple((len(profile)-1)*segments+j for j in range(segments))]);fs=[f[:1]+tuple(reversed(f[1:])) for f in fs];add_geom(points,fs,trim_index)
for side in [-1,1]:
 u=side*wing_axis
 # Pediment is in front of the tower plinth, as visible in both references;
 # the original overlapping slab had hidden its upper half.
 front_prism(u,[(-1.73,33.58),(1.73,33.58),(0,34.38)],.54,.41,stone_index)
 for z,w,h,d in [(34.20,3.35,.25,2.65),(34.40,3.07,.18,2.42)]:box(u,z,w,h,depth=d,d=-1.15,mat=trim_index)
 # An opaque rectangular tower encloses the dark front opening. The side and
 # rear are deliberately plain because there is no complete survey reference.
 z0,z1=34.49,37.24;W,D=2.80,2.20;opening=1.04;lo,hi=34.76,36.98
 for sign in [-1,1]:box(u+sign*(W/2-.14),(z0+z1)/2,.28,z1-z0,depth=D,d=-1.15,mat=stone_index)
 box(u,(z0+z1)/2,W,z1-z0,depth=.28,d=-2.11,mat=stone_index)
 # Front wall is built around a real opening, not covered by a dark decal.
 jamb=(W-opening)/2
 for sign in [-1,1]:box(u+sign*(opening/2+jamb/2),(z0+z1)/2,jamb,z1-z0,depth=.25,d=-.175,mat=stone_index)
 box(u,(z0+lo)/2,opening,lo-z0,depth=.25,d=-.175,mat=stone_index)
 box(u,(hi+z1)/2,opening,z1-hi,depth=.25,d=-.175,mat=stone_index)
 box(u,(lo+hi)/2,opening,hi-lo,depth=.06,d=-.56,mat=recess_index)
 # Two close columns per side (four on the front) are visible in the photos.
 for offset in [-1.23,-.91,.91,1.23]:engaged_column(u+offset,.075,34.58,37.18,.125)
 for z,w,h,d in [(37.28,3.05,.16,2.48),(37.43,3.24,.14,2.65),(37.61,3.48,.21,2.86),(37.79,3.12,.14,2.57)]:box(u,z,w,h,depth=d,d=-1.15,mat=trim_index)
 box(u,37.94,2.86,.18,depth=2.30,d=-1.15,mat=stone_index)
 # A low segmental crown, not an exposed spherical dome. Its shallow curved
 # silhouette is visible in the current and1994 reference photographs.
 radius,rise,base=1.35,.48,38.03
 outline=[(-radius,base),(radius,base)]+[(radius*math.cos(j*math.pi/20),base+rise*math.sin(j*math.pi/20)) for j in range(1,20)]
 front_prism(u,outline,-.075,-2.225,trim_index)
 for su in [-1,1]:
  for sd in [-1,1]:box(u+su*1.34,38.10,.18,.42,depth=.18,d=-1.15+sd*1.08,mat=trim_index)
 # Bridge the existing pole's base to the crown without changing its40m tip.
 box(u,38.67,.19,.36,depth=.19,d=-1.15,mat=trim_index)

bar_count=0;photo_triangles=0
for w in windows:
 if not w['active']:continue
 H=Matrix(w['uv_homography_display']);lo,hi=w['model_z'];cx=w['model_centre_u'];width=w['model_width'];nx,ny=config['glazing_subdivision'];points=[];uvs=[]
 for j in range(ny+1):
  z=lo+(hi-lo)*j/ny;t=1-j/ny
  for i in range(nx+1):
   s=i/nx;u=cx-width/2+width*s;points.append(C+T*u+N*(-.2275)+UP*z)
   q=H@Vector((s,t,1));px=q.x/q.z;py=q.y/q.z
   # EXIF6: raw x=oriented y; raw y=rawH-oriented x. Blender v grows up.
   uvs.append((py/1920,px/1280))
 quads=[]
 for j in range(ny):
  for i in range(nx):a=j*(nx+1)+i;quads.append((a,a+1,a+nx+2,a+nx+1))
 add_geom(points,quads,photo_index,uvs);photo_triangles+=len(quads)*2
 # Only strong, interior frame lines are geometric; fine captured lines remain
 # part of the photo. This removes the old unobserved equal-third grid.
 vbars=[b for b in w['detected_vertical_bars'] if .23<b['fraction']<.81 and b['width_fraction']>=.018]
 if not vbars and 'wing' in w['axis']:vbars=[{'fraction':.53,'width_fraction':.022,'manual':'Visible central sash joint, below automatic dark threshold.'}]
 hbars=[b for b in w['detected_horizontal_bars'] if .16<b['fraction']<.56 and b['width_fraction']>=.018]
 for bar in vbars:
  thickness=min(.048,max(.018,bar['width_fraction']*width*.45));box(cx-width/2+bar['fraction']*width,(lo+hi)/2,thickness,hi-lo-.025);bar_count+=1
 for bar in hbars:
  thickness=min(.052,max(.019,bar['width_fraction']*(hi-lo)*.42));box(cx,hi-bar['fraction']*(hi-lo),width-.025,thickness);bar_count+=1
 w['applied_vertical_bars']=vbars;w['applied_horizontal_bars']=hbars
mesh=bpy.data.meshes.new('Bund17 preserved architecture with photo-calibrated glazing');mesh.from_pydata(verts,[],faces);mesh.update();
for mat in materials:mesh.materials.append(mat)
uv=mesh.uv_layers.new(name='StoredPhotoPixelsUV')
for face,mat,sm,coords in zip(mesh.polygons,face_mats,smooth,face_uv):
 face.material_index=mat;face.use_smooth=sm
 for index,co in zip(face.loop_indices,coords):uv.data[index].uv=co
obj.data=mesh
obj['photographic_glazing']='24 clean large windows among25 examined; lowest central window excluded by relief occlusion; source image pixels unchanged.'
obj['source_photo_license']='CC0-1.0, Suicasmo';obj['source_photo_sha256']=source_sha
for o in bpy.context.scene.objects:o.select_set(False)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
mesh.calc_loop_triangles();triangles=len(mesh.loop_triangles)
# Real-geometry rays prove the photographed panes remain behind the wall, and
# the new tower apertures end in opaque dark recesses rather than open sky.
ray_checks=[]
for w in windows:
 if not w['active']:continue
 z=sum(w['model_z'])/2;origin=C+T*w['model_centre_u']+N*2+UP*z
 hit,point,normal,index=obj.ray_cast(origin,-N);depth=local(point)[1] if hit else None
 assert hit and depth<-.14 and mesh.polygons[index].material_index in [photo_index,new_frame_index],(w['id'],hit,depth,index)
 ray_checks.append({'id':w['id'],'first_surface_d_m':depth})
roof_rays=[]
for side in [-1,1]:
 for kind,z,expected_d in [('dark_front_opening',35.8,-.53),('visible_pediment',34.0,.54)]:
  hit,point,normal,index=obj.ray_cast(C+T*(side*wing_axis)+N*2+UP*z,-N);d=local(point)[1] if hit else None
  assert hit and abs(d-expected_d)<.002,(kind,side,hit,d)
  roof_rays.append({'side':side,'kind':kind,'front_d':d,'material':materials[mesh.polygons[index].material_index].name})
def export(path):
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_extras=True,export_copyright=COPYRIGHT)
 retain_provenance(path)
export(OUT/'bund17-photo.glb');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bund17-photo.blend'))
# Texture-free variant uses the very same updated geometry and the original
# blue-grey glass material, not white texture factors with a missing map.
mesh.materials[photo_index]=materials[glass_index];export(OUT/'bund17-untextured.glb');mesh.materials[photo_index]=photo_mat
# Freeze independently reproducible checks before adding preview-only scene.
checks={'baseline_file':args.base_model.name,'baseline_sha256':hashlib.sha256(args.base_model.read_bytes()).hexdigest(),'baseline_scope':'Cleaned conforming structural wall baseline; body unchanged checks compare this cleaned input, not legacy closed wall boxes.','photo_sha256':source_sha,'photo_bytes':photo.stat().st_size,'original_vertices':len(old.vertices),'original_polygons':len(old.polygons),'preserved_original_polygons':len(unchanged),'removed':removed,'unchanged_original_vertices':sum(tuple(v.co)==verts[i] for i,v in enumerate(old.vertices)),'moved_pediment_vertices':len(pediment_vertices),'roof_primitive_vertices_replaced':len(roof_vertices),'attic_recess_faces_shaded':attic_shaded_faces,'mapped_windows':24,'reviewed_windows':25,'skipped_windows':[w['id'] for w in windows if not w['active']],'photo_triangles':photo_triangles,'new_frame_bars':bar_count,'triangles':triangles,'raw_bytes':(OUT/'bund17-photo.glb').stat().st_size,'native_bytes':(OUT/'bund17-photo.blend').stat().st_size,'untextured_bytes':(OUT/'bund17-untextured.glb').stat().st_size,'footprint_anchor_unchanged':True,'window_recess_m':.2525,'front_wall_plane_d_m':.025,'glass_front_d_m':-.2275,'photo_gpu_rgba_mip_bytes_estimate':int(5184*3456*4*4/3),'image_edited':False,'surveyed_accuracy':False,'bounds_blender':[[min(verts[i][k] for f in faces for i in f) for k in range(3)],[max(verts[i][k] for f in faces for i in f) for k in range(3)]],'closed_primitive_winding':{'count':len(closed_primitive_volumes),'minimum_positive_volume_m3':min(closed_primitive_volumes)},'glazing_rays':ray_checks,'roof_rays':roof_rays,'cleaned_baseline_body_vertices_unchanged':all(tuple(v.co)==verts[i] for i,v in enumerate(old.vertices) if v.co.z<33.3),'roof_reconstruction':{'front_columns_per_tower':4,'opaque_towers':2,'recess_depth_m':.48,'crown_rise_m':.48,'pediment_frontward_shift_m':.98,'source':'See roof-reference.json; dimensions photo-proportioned, side/rear simplified.'}}
(OUT/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');(OUT/'applied-window-controls.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
print('PHOTO_WINDOW_CHECKS',json.dumps(checks))
if args.render:
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.12;scene.render.resolution_x=1100;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
 scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.52,.59,.65,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
 bpy.ops.object.light_add(type='AREA',location=(80,30,70));bpy.context.object.data.energy=40000;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=45
 target=C+UP*20;bpy.ops.object.camera_add(location=target+N*75+T*3);cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=43;scene.camera=cam;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
 for name,point,scale in [('front',target+N*75,43),('oblique',target+N*65+T*25+UP*7,45),('window-detail',C+UP*18+N*40,21)]:
  if name not in args.views.split(','):continue
  target_now=C+UP*(18 if name=='window-detail' else 20);cam.location=point;cam.rotation_euler=(target_now-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
