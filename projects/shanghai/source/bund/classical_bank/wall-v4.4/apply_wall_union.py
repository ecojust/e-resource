"""Apply captured source-wall replacement to frozen native; never overwrite inputs."""
import bpy,json,sys,argparse,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--capture',type=Path,default=P/'captured-wall-shells.json');ap.add_argument('--union',type=Path,default=P/'wall-union-mesh.json');ap.add_argument('--output-dir',type=Path,default=P);ap.add_argument('--credit-glb',type=Path);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);D=json.loads(args.capture.read_text());C=json.loads(args.union.read_text());ident=D['building'];args.output_dir.mkdir(exist_ok=True,parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(args.input)==D['input_native_sha256']==C['input_native_sha256'];assert sha(args.capture)==C['capture_sha256'];bpy.ops.wm.open_mainfile(filepath=str(args.input));obj=bpy.data.objects['HSBC Bund 12' if ident=='bund12' else 'Russo Chinese Bank Bund 15'];old=obj.data
verts=[tuple(v.co) for v in old.vertices];original_vertex_count=len(verts);removed=set(C['removed_native_face_ids']);assert len(removed)==D['matched_face_count'];keep=[p for p in old.polygons if p.index not in removed];faces=[tuple(p.vertices) for p in keep];materials=[p.material_index for p in keep];smooth=[p.use_smooth for p in keep];vbase=len(verts);verts+=C['vertices_blender_world'];new_faces=[tuple(vbase+i for i in f) for f in C['faces']];faces+=new_faces;materials+=[0]*len(new_faces);smooth+=[False]*len(new_faces)
mesh=bpy.data.meshes.new(ident+' conforming source wall boundary');mesh.from_pydata(verts,[],faces);mesh.update()
for m in old.materials:mesh.materials.append(m)
for p,mi,sm in zip(mesh.polygons,materials,smooth):p.material_index=mi;p.use_smooth=sm
assert all(tuple(mesh.vertices[i].co)==tuple(old.vertices[i].co) for i in range(len(old.vertices)))
assert all(tuple(mesh.polygons[i].vertices)==tuple(p.vertices) and mesh.polygons[i].material_index==p.material_index and mesh.polygons[i].use_smooth==p.use_smooth for i,p in enumerate(keep))
# Old and new wall-only first-hit rays at every original opening. Glass and frame
# geometry is deliberately absent from this check, so a filled hole is detected.
old_wall=BVHTree.FromPolygons([tuple(v.co) for v in old.vertices],[tuple(old.polygons[i].vertices) for i in sorted(removed)]);new_wall=BVHTree.FromPolygons(C['vertices_blender_world'],C['faces']);U=D['world_basis_u'];V=D['world_basis_v']
def world(p):x,y,z=p;return Vector((U[0]*x+V[0]*y,U[1]*x+V[1]*y,z))
raychecks=0;old_hits=0;new_hits=0
for sh in D['shells']:
 if sh['source_kind']!='bay':continue
 a=sh['bay_args'];x,y,lo,hi,w=a[0],a[2],a[5],a[6],a[7];u=sh['u'];v=sh['v'];origin=sh['origin'];direction=world((v[0],v[1],0))
 for delta in[-.2,0,.2]:
  xx=x+delta*w;z=(lo+hi)/2;start=world((origin[0]+u[0]*xx+v[0]*(y-.05),origin[1]+u[1]*xx+v[1]*(y-.05),z));before=old_wall.ray_cast(start,direction,.72);after=new_wall.ray_cast(start,direction,.72);old_hits+=before[0] is not None;new_hits+=after[0] is not None
  assert (before[0] is None)==(after[0] is None),(sh['source_bay'],'opening ray changed',before,after)
  if before[0] is not None:assert abs(before[3]-after[3])<2e-5
  raychecks+=1
obj.data=mesh;obj['wall_topology']='Only captured structural wall shells replaced by shared-node 2D union boundary; true opening reveals and facade plane/depth preserved.'
models=[obj]+([bpy.data.objects['Bund12 six observed main casement frames'],bpy.data.objects['Bund12 thirty independently mapped recessed glass panes']] if ident=='bund12' else[])
def object_digest(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<II',len(p.vertices),p.material_index));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 for uv in o.data.uv_layers:
  for p in uv.data:h.update(struct.pack('<2f',*p.uv))
 return h.hexdigest()
unchanged_extras=[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'geometry_material_uv_sha256':object_digest(o)} for o in models[1:]]
bpy.ops.object.select_all(action='DESELECT')
for o in models:o.select_set(True)
bpy.context.view_layer.objects.active=obj;raw=args.output_dir/(ident+'-clean-raw.glb');native=args.output_dir/(ident+'-clean.blend')
bpy.ops.export_scene.gltf(filepath=str(raw),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='AUTO',export_extras=True)
if args.credit_glb:
 def read(p):
  b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
 source,_=read(args.credit_glb);j,bin=read(raw)
 for k in('copyright','extras'):
  if k in source['asset']:j['asset'][k]=source['asset'][k]
 j['asset'].setdefault('extras',{})['structural_wall_cleanup']='Shared-node same-plane wall union, preserving original openings; v4.4'
 jb=json.dumps(j,ensure_ascii=False,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);bin+=b'\0'*((-len(bin))%4);raw.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(jb)+len(bin))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(bin),0x004e4942)+bin)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
mesh.calc_loop_triangles();triangles=sum(len(o.data.loop_triangles) if o==obj else(sum(len(p.vertices)-2 for p in o.data.polygons)) for o in models)
report={'schema_version':'classical-bank-clean-wall-v1','building':ident,'input_native_sha256':sha(args.input),'raw':{'file':raw.name,'bytes':raw.stat().st_size,'sha256':sha(raw),'triangles':triangles},'native':{'file':native.name,'bytes':native.stat().st_size,'sha256':sha(native)},'original_object_vertices_retained_exactly':original_vertex_count,'original_object_faces':len(old.polygons),'replaced_source_wall_faces':len(removed),'retained_nonwall_faces_exactly':len(keep),'new_shared_wall_vertices':len(C['vertices_blender_world']),'new_shared_wall_faces':len(new_faces),'original_wall_topology_preservation_claim_superseded':True,'preservation_scope':'All noncaptured native faces and every original vertex retained exactly; source structural wall topology intentionally replaced while preserving its projected region/depth. Photo panes/frames remain separate unchanged objects.','wall_only_opening_first_hit_checks':raychecks,'old_wall_hits_at_openings':old_hits,'new_wall_hits_at_openings':new_hits,'other_model_objects_unchanged':unchanged_extras,'wall_groups':C['groups'],'browser_validation_performed':False};assert raw.stat().st_size<100000000 and native.stat().st_size<100000000;(args.output_dir/'wall-clean-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('CANDIDATE_READY',json.dumps({k:v for k,v in report.items() if k!='wall_groups'}))
