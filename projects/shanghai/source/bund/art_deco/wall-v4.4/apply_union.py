"""Apply only source-identified wall-face replacements to published native models."""
import bpy,bmesh,json,sys,math,struct,hashlib,collections
from pathlib import Path
from mathutils import Vector
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from arguments import PACKAGE,workdir
P=workdir();OUT=P/'candidate';OUT.mkdir(exist_ok=True)

def digest(mesh,face_ids):
 h=hashlib.sha256()
 for index in face_ids:
  p=mesh.polygons[index];h.update(struct.pack('<I?',p.material_index,p.use_smooth));h.update(struct.pack('<I',len(p.vertices)))
  for vi in p.vertices:h.update(struct.pack('<3f',*mesh.vertices[vi].co))
  for uv in mesh.uv_layers:
   for li in p.loop_indices:h.update(struct.pack('<2f',*uv.data[li].uv))
 return h.hexdigest()
def bounds(objects):
 rows=[o.matrix_world@o.data.vertices[i].co for o in objects for p in o.data.polygons for i in p.vertices]
 return [[min(v[k]for v in rows)for k in range(3)],[max(v[k]for v in rows)for k in range(3)]]
def rays(rows,objects):
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();out=[]
 for r in rows:
  obj=objects[r['builder']];origin=obj.matrix_world@Vector(r['point']);normal=obj.matrix_world.to_3x3()@Vector(r['normal']);hit,loc,n,face,hitobj,matrix=bpy.context.scene.ray_cast(deps,origin,-normal,distance=4.0)
  if hit:
   original=hitobj.original;mi=hitobj.data.polygons[face].material_index;out.append({'distance':float((loc-origin).length),'material':hitobj.data.materials[mi].name,'point':list(loc)})
  else:out.append(None)
 return out

for bid in ['bund19','bund20','bund23']:
 cap=json.loads((P/f'{bid}-capture.json').read_text());union=json.loads((P/f'{bid}-wall-union.json').read_text());raydefs=json.loads((P/f'{bid}-aperture-rays.json').read_text())
 assert union['source_capture_sha256']==hashlib.sha256((P/f'{bid}-capture.json').read_bytes()).hexdigest()
 native=PACKAGE/'baseline'/f'{bid}.blend';assert hashlib.sha256(native.read_bytes()).hexdigest()==cap['native_source_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(native));models=[o for o in bpy.context.scene.objects if o.type=='MESH'and o.get('reference_reconstruction')];assert models
 objects={r['builder']:bpy.data.objects[r['object']]for r in cap['captured']}
 for row in cap['objects']:
  if row['builder'] not in objects:
   candidates=[o for o in models if o.name.startswith(row['builder'][:48])];assert len(candidates)==1
   objects[row['builder']]=candidates[0]
 for r in cap['objects']:assert not r.get('missing')and r['different_face_order_material_smooth']==0 and r['native_faces']==r['source_faces']and r['native_vertices']==r['source_vertices']and r['maximum_vertex_delta_m']<1e-5,r
 initialbounds=bounds(models);before_rays=rays(raydefs,objects)
 remove=collections.defaultdict(set)
 for r in cap['captured']:remove[r['object']].update(r['face_ids'])
 audits=[];original_matrices={o.name:[list(x)for x in o.matrix_world]for o in models}
 for obj in models:
  old=obj.data;excluded=remove.get(obj.name,set());keep=[p.index for p in old.polygons if p.index not in excluded];before=digest(old,keep)
  if excluded:
   verts=[tuple(v.co)for v in old.vertices];faces=[tuple(old.polygons[i].vertices)for i in keep];mats=[old.polygons[i].material_index for i in keep];smooth=[old.polygons[i].use_smooth for i in keep];uvs={layer.name:[[tuple(layer.data[li].uv)for li in old.polygons[i].loop_indices]for i in keep]for layer in old.uv_layers}
   new=bpy.data.meshes.new(old.name+' source-wall-union');new.from_pydata(verts,[],faces)
   for mat in old.materials:new.materials.append(mat)
   for face,mat,sm in zip(new.polygons,mats,smooth):face.material_index=mat;face.use_smooth=sm
   for name,values in uvs.items():
    layer=new.uv_layers.new(name=name)
    for face,vs in zip(new.polygons,values):
     for li,v in zip(face.loop_indices,vs):layer.data[li].uv=v
   new.update();obj.data=new
  after=digest(obj.data,range(len(obj.data.polygons)))
  assert before==after,(bid,obj.name,'protected faces changed')
  audits.append({'object':obj.name,'removed_source_wall_faces':len(excluded),'protected_faces':len(keep),'protected_coordinates_materials_smooth_uv_sha256':before,'same_after':True})
 combinedv=[];combinedf=[];combinedm=[];group_reports=[]
 for group in union['groups']:
  report=group['report'];mesh=bpy.data.meshes.new('temporary-wall-group');mesh.from_pydata(group['vertices'],[],group['faces']);mesh.update()
  for face,m in zip(mesh.polygons,group['materials']):face.material_index=m
  bm=bmesh.new();bm.from_mesh(mesh)
  # Collapse only coplanar edges within the new, already conformal wall shell.
  # Shared vertices keep face boundaries conformal; MATERIAL prevents merging
  # the real warm/cool stone and recessed spandrel surfaces.
  bmesh.ops.dissolve_limit(bm,angle_limit=.01,use_dissolve_boundaries=False,verts=list(bm.verts),edges=list(bm.edges),delimit={'MATERIAL'})
  bm.normal_update();nonmanifold=sum(not e.is_manifold for e in bm.edges);wrong=sum(not e.is_contiguous for e in bm.edges)
  assert not nonmanifold and not wrong,(bid,report['group'],nonmanifold,wrong)
  volume=bm.calc_volume(signed=True);assert abs(volume-report['rectangular_union_volume_m3'])<max(1e-4,report['rectangular_union_volume_m3']*2e-5),(bid,report['group'],volume,report['rectangular_union_volume_m3'])
  bm.to_mesh(mesh);bm.free();mesh.calc_loop_triangles();base=len(combinedv);combinedv.extend(tuple(v.co)for v in mesh.vertices);combinedf.extend(tuple(base+i for i in f.vertices)for f in mesh.polygons);combinedm.extend(f.material_index for f in mesh.polygons)
  group_reports.append({**report,'optimized_vertices':len(mesh.vertices),'optimized_faces':len(mesh.polygons),'optimized_triangles':len(mesh.loop_triangles),'optimized_signed_volume_m3':volume,'optimized_nonmanifold_edges':nonmanifold,'optimized_inconsistent_edges':wrong});bpy.data.meshes.remove(mesh)
 mesh=bpy.data.meshes.new(bid+' conformal wall union');mesh.from_pydata(combinedv,[],combinedf)
 material_source=next(iter(objects.values())).data.materials
 for mat in material_source:mesh.materials.append(mat)
 for face,m in zip(mesh.polygons,combinedm):face.material_index=m
 mesh.update();walls=bpy.data.objects.new('Conformal structural walls — source panel union',mesh);bpy.context.scene.collection.objects.link(walls);walls.matrix_world=next(iter(objects.values())).matrix_world.copy();walls['reference_reconstruction']='Topology-only union of source-identified structural wall volumes; geometry is not newly surveyed';models.append(walls)
 for obj in models[:-1]:assert original_matrices[obj.name]==[list(x)for x in obj.matrix_world]
 after_rays=rays(raydefs,objects);ray_errors=[];max_hit_delta=0
 for i,(a,b)in enumerate(zip(before_rays,after_rays)):
  if (a is None)!=(b is None):ray_errors.append({'index':i,'before':a,'after':b});continue
  if a is not None:
   delta=abs(a['distance']-b['distance']);max_hit_delta=max(max_hit_delta,delta)
   if delta>2e-4 or a['material']!=b['material']:ray_errors.append({'index':i,'before':a,'after':b})
 assert not ray_errors,(bid,'changed aperture ray',ray_errors[:5])
 finalbounds=bounds(models);boundsdelta=max(abs(a-b)for aa,bb in zip(initialbounds,finalbounds)for a,b in zip(aa,bb));assert boundsdelta<1e-4,(bid,boundsdelta)
 bpy.ops.object.select_all(action='DESELECT')
 for obj in models:obj.select_set(True)
 bpy.context.view_layer.objects.active=walls;bpy.context.view_layer.update()
 out=OUT/bid;out.mkdir(exist_ok=True);glb=out/f'{bid}.glb';blend=out/f'{bid}.blend'
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True)
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
 triangles=0
 for obj in models:obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
 result={'id':bid,'status':'pass','scope':'Source-identified Facade.panel five-face boxes and Bund20 source-defined12cm recessed spandrel boxes only. Curved arch/oculus fronts and all independent ornament stay original.','source_native_sha256':cap['native_source_sha256'],'source_raw_sha256':hashlib.sha256((PACKAGE/'baseline'/f'{bid}.glb').read_bytes()).hexdigest(),'source_generator_match':cap['objects'],'protected_original_objects':audits,'wall_groups':group_reports,'aperture_rays':{'tested':len(raydefs),'changed_first_hit_count':len(ray_errors),'maximum_distance_difference_m':max_hit_delta},'bounds_before':initialbounds,'bounds_after':finalbounds,'maximum_bounds_delta_m':boundsdelta,'all_original_object_transforms_identical':True,'triangles':triangles,'assets':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in [glb,blend]},'browser_verified':False,'geographic_anchor_unchanged':True}
 assert all(x['bytes']<100_000_000 for x in result['assets'].values());(out/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('WALL_CANDIDATE',bid,triangles,result['assets'],flush=True)
