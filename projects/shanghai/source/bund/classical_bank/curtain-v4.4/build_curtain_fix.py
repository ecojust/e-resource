"""Correct ten inward curtain prisms and remove 120 interpenetrating internal folds."""
import argparse,bpy,json,struct,hashlib,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);a.output.mkdir(parents=True,exist_ok=True)
spec=json.loads((ROOT/'curtain-input.json').read_text());native=ROOT/'baseline/bund15-wall.blend';raw=ROOT/'baseline/bund15-wall.glb'
assert hashlib.sha256(native.read_bytes()).hexdigest()==spec['baseline_native_sha256'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==spec['baseline_raw_sha256']
bpy.ops.wm.open_mainfile(filepath=str(native));ob=bpy.data.objects[spec['object_name']];mesh=ob.data;target={i for p in spec['curtain_prisms'] for i in p['faces']};assert len(target)==425
before_vertices=[tuple(v.co) for v in mesh.vertices];before_faces={p.index:(tuple(p.vertices),p.material_index,p.use_smooth) for p in mesh.polygons};before_materials=[m.name for m in mesh.materials]
def other_sig():
 out={}
 for o in bpy.data.objects:
  if o.type!='MESH' or o==ob:continue
  m=o.data;data={'vertices':[list(v.co) for v in m.vertices],'faces':[(list(f.vertices),f.material_index,f.use_smooth) for f in m.polygons],'uv':{u.name:[list(v.uv) for v in u.data] for u in m.uv_layers},'materials':[x.name for x in m.materials]};out[o.name]=hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()
 return out
other_before=other_sig();outward=Vector((-spec['world_basis_v'][0],-spec['world_basis_v'][1],0));front_center=spec['front_center'];v=Vector(spec['world_basis_v'])
def measure(component):
 faces=set(component['faces']);ids={j for i in faces for j in mesh.polygons[i].vertices};origin=sum((mesh.vertices[j].co for j in ids),Vector())/len(ids);volume=0;count=0
 for t in mesh.loop_triangles:
  if t.polygon_index in faces:
   x,y,z=[mesh.vertices[j].co-origin for j in t.vertices];volume+=x.dot(y.cross(z))/6;count+=1
 miny=min(Vector(mesh.vertices[j].co[:2]).dot(v)-front_center[1] for j in ids);dots=[]
 for i in faces:
  f=mesh.polygons[i]
  if all(abs(Vector(mesh.vertices[j].co[:2]).dot(v)-front_center[1]-miny)<1e-5 for j in f.vertices):dots.append(f.normal.dot(outward))
 return {'signed_volume_m3':volume,'triangles':count,'front_normal_dot_outward':dots}
mesh.calc_loop_triangles();before=[measure(c) for c in spec['curtain_prisms']];assert sum(x['triangles'] for x in before)==580
assert all(x['signed_volume_m3']<0 and all(d<-.999 for d in x['front_normal_dot_outward']) for x in before)
for i in sorted(target):mesh.polygons[i].flip()
mesh.update();mesh.calc_loop_triangles();after=[measure(c) for c in spec['curtain_prisms']]
assert all(x['signed_volume_m3']>0 and all(d>.999 for d in x['front_normal_dot_outward']) for x in after)
assert before_vertices==[tuple(v.co) for v in mesh.vertices]
assert before_materials==[m.name for m in mesh.materials];assert other_sig()==other_before
for p in mesh.polygons:
 verts,mat,smooth=before_faces[p.index];assert p.material_index==mat and p.use_smooth==smooth
 if p.index not in target:assert tuple(p.vertices)==verts
 else:
  reverse=verts[::-1];actual=tuple(p.vertices);assert actual in [reverse[i:]+reverse[:i] for i in range(len(reverse))]
# Remove only the independently identified fold boxes. Their vertices are not
# shared by any retained face; other original orphan vertices remain untouched.
fold_faces={i for c in spec['fold_components'] for i in c['faces']};assert len(fold_faces)==720
fold_vertices={j for i in fold_faces for j in mesh.polygons[i].vertices};assert len(fold_vertices)==960
kept=[f for f in mesh.polygons if f.index not in fold_faces]
assert not any(j in fold_vertices for f in kept for j in f.vertices)
vertex_ids=[i for i in range(len(mesh.vertices)) if i not in fold_vertices];remap={old:new for new,old in enumerate(vertex_ids)}
new=bpy.data.meshes.new(mesh.name+'_without_internal_curtain_folds');new.from_pydata([tuple(mesh.vertices[i].co) for i in vertex_ids],[],[tuple(remap[j] for j in f.vertices) for f in kept])
for m in mesh.materials:new.materials.append(m)
for dst,src in zip(new.polygons,kept):dst.material_index=src.material_index;dst.use_smooth=src.use_smooth
for uv in mesh.uv_layers:
 target_uv=new.uv_layers.new(name=uv.name)
 for dst,src in zip(new.polygons,kept):
  for dl,sl in zip(dst.loop_indices,src.loop_indices):target_uv.data[dl].uv=uv.data[sl].uv
assert all(tuple(new.vertices[remap[i]].co)==before_vertices[i] for i in vertex_ids)
for dst,src in zip(new.polygons,kept):assert tuple(tuple(new.vertices[j].co) for j in dst.vertices)==tuple(tuple(mesh.vertices[j].co) for j in src.vertices)
old_mesh=mesh;ob.data=new;mesh=new;mesh.update();bpy.data.meshes.remove(old_mesh)
assert other_sig()==other_before
ob['curtain_repair']='Reverse ten inward curtain prisms (425 native faces / 580 triangles), remove 120 interpenetrating internal fold boxes (720 faces / 1440 triangles); all remaining coordinates and other geometry unchanged.'
blob=raw.read_bytes();n,_=struct.unpack_from('<II',blob,12);original_doc=json.loads(blob[20:20+n]);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
out=a.output/'bund15-curtain-raw.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_materials='EXPORT',export_copyright=original_doc['asset']['copyright'])
b=out.read_bytes();n,_=struct.unpack_from('<II',b,12);doc=json.loads(b[20:20+n]);doc['asset']['extras']=dict(original_doc['asset'].get('extras',{}),curtain_repair={'version':'bund15-curtain-v4.4','input_wall_raw_sha256':spec['baseline_raw_sha256'],'inward_prisms_corrected':10,'reoriented_triangles':580,'remaining_positions_unchanged':True,'fold_boxes_removed':120,'fold_triangles_removed':1440})
j=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);tail=b[20+n:];out.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail)
bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'bund15-curtain.blend'),compress=True)
report={'version':'bund15-curtain-winding-native-v1','input_wall_stage':{'raw_sha256':spec['baseline_raw_sha256'],'native_sha256':spec['baseline_native_sha256']},'baseline_wall_report_scope':'Upstream preservation applies to pre-wall→wall output. This later stage reverses 425 curtain native faces and deletes 720 internal fold faces. It does not rewrite wall-stage hashes or extend the upstream preservation claim across these explicit later changes.','prisms_corrected':10,'native_faces_reoriented':425,'triangles_reoriented':580,'remaining_native_vertex_positions_exact':True,'all_remaining_nontarget_native_face_geometry_exact':True,'removed_interpenetrating_fold_boxes':120,'removed_fold_triangles':1440,'removed_native_fold_faces':720,'removed_native_fold_vertices':960,'other_meshes_unchanged':other_before,'before':before,'after':after,'output':{'raw_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'native_sha256':hashlib.sha256((a.output/'bund15-curtain.blend').read_bytes()).hexdigest()}}
(a.output/'curtain-native-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['before','after']},indent=2))
