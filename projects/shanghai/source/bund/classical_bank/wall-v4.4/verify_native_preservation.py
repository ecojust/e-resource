"""Independent comparison of saved pre/post-cleanup .blend files; no saves."""
import bpy,argparse,sys,json,hashlib,struct
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);D=json.loads(args.capture.read_text());removed={i for sh in D['shells'] for i in sh['old_face_ids']};name='HSBC Bund 12' if D['building']=='bund12' else'Russo Chinese Bank Bund 15'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for f in o.data.polygons:h.update(struct.pack('<II?',len(f.vertices),f.material_index,f.use_smooth));h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 for uv in o.data.uv_layers:
  for v in uv.data:h.update(struct.pack('<2f',*v.uv))
 for m in o.data.materials:h.update(m.name.encode())
 return h.hexdigest()
assert sha(args.before)==D['input_native_sha256'];bpy.ops.wm.open_mainfile(filepath=str(args.before));o=bpy.data.objects[name];vs=[tuple(v.co) for v in o.data.vertices];kept=[(tuple(p.vertices),p.material_index,p.use_smooth) for p in o.data.polygons if p.index not in removed];extra={ob.name:digest(ob) for ob in bpy.data.objects if ob.type=='MESH' and ob.name!=name};mats=[m.name for m in o.data.materials];images={im.name:hashlib.sha256(bytes(im.packed_file.data)).hexdigest() for im in bpy.data.images if im.packed_file}
bpy.ops.wm.open_mainfile(filepath=str(args.after));o=bpy.data.objects[name];assert len(o.data.vertices)>=len(vs);assert all(tuple(o.data.vertices[i].co)==v for i,v in enumerate(vs));assert [m.name for m in o.data.materials]==mats
assert all((tuple(o.data.polygons[i].vertices),o.data.polygons[i].material_index,o.data.polygons[i].use_smooth)==r for i,r in enumerate(kept));after_extra={ob.name:digest(ob) for ob in bpy.data.objects if ob.type=='MESH' and ob.name!=name};assert extra==after_extra;after_images={im.name:hashlib.sha256(bytes(im.packed_file.data)).hexdigest() for im in bpy.data.images if im.packed_file};assert images==after_images
report={'schema_version':'saved-native-wall-preservation-v1','status':'passed','building':D['building'],'before_native_sha256':D['input_native_sha256'],'after_native_sha256':sha(args.after),'original_vertices_exact':len(vs),'retained_nonshell_faces_exact':len(kept),'intentionally_replaced_structural_faces':len(removed),'material_slots_preserved':True,'other_mesh_objects_geometry_material_uv_unchanged':extra,'packed_image_bytes_unchanged':images,'source_capture_sha256':sha(args.capture),'comparison':'Saved native files reopened independently; vertex floats, face indices/materials/smoothing, other mesh UVs and packed image bytes compared.','browser_test_performed':False};args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
