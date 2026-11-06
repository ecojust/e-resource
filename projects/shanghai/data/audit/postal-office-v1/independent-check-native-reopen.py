"""Run inside a fresh Blender process after opening the delivered native file."""
import bpy,hashlib,json,struct,sys
from pathlib import Path
receipt_path=Path(sys.argv[sys.argv.index('--')+1]);out=Path(sys.argv[sys.argv.index('--')+2]);r=json.loads(receipt_path.read_text());scene=bpy.context.scene
objects=[bpy.data.objects[name] for name in scene['model_mesh_names']];d=hashlib.sha256()
for ob in sorted(objects,key=lambda ob:ob.name):
 d.update(ob.name.encode())
 for row in ob.matrix_world:d.update(struct.pack('<4f',*row))
 for v in ob.data.vertices:d.update(struct.pack('<3f',*v.co))
 for face in ob.data.polygons:
  assert len(face.vertices)==3
  d.update(struct.pack('<3I',*face.vertices))
path=Path(bpy.data.filepath);asset_hash=hashlib.sha256(path.read_bytes()).hexdigest();triangles=sum(len(ob.data.polygons) for ob in objects)
checks={'actual_delivered_native_file_hash_matches':asset_hash==r['sha256'],'actual_reopened_geometry_matches_saved_receipt':d.hexdigest()==r['geometry_hash_before_and_after_reopen'],'single_editable_building_mesh':len(objects)==1 and objects[0].type=='MESH','triangle_count_matches_raw':triangles==r['model_triangles']==251348,'model_source_raw_sha_matches':all(ob.get('source_raw_sha256')==r['source_raw_sha256'] for ob in objects),'candidate_identity_matches':scene.get('candidate_id')=='hongkou-general-post-office','preview_stage_excluded':bool(scene.get('preview_stage_excluded_from_model'))}
result={'schema':'postal-independent-native-reopen-v1','passed':all(checks.values()),'checks':checks,'blender_version':bpy.app.version_string,'native':{'file':str(path),'bytes':path.stat().st_size,'sha256':asset_hash},'actual_geometry_hash':d.hexdigest(),'model_triangles':triangles,'source_raw_sha256':r['source_raw_sha256'],'saved_receipt':{'file':str(receipt_path),'sha256':hashlib.sha256(receipt_path.read_bytes()).hexdigest()},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Fresh independent Blender process opened the production native file read-only. No author model/native modules imported, no re-save or render.'};out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result));assert result['passed']
