"""Read an already saved native file; no scene or material edits, no re-save."""
from pathlib import Path
import json,hashlib
import bpy
ROOT=Path(__file__).resolve().parent.parent
metadata=json.loads((ROOT/'source/asset-metadata.json').read_text());expected=metadata['copyright']
scene=bpy.context.scene;col=bpy.data.collections['MODEL_BAJIN_MAIN_HOUSE_ENU']
assert scene['copyright']==col['copyright']==expected
items=[]
for o in col.objects:
 assert o.get('copyright')==expected
 items.append({'name':o.name,'type':o.type,'copyright':o['copyright']})
native=ROOT/'review/native/bajin-main-house.blend'
report={'schema':'bajin-native-metadata-readback-v2','actual_saved_native_read':True,'independent_QA':False,'native_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'scene_copyright':scene['copyright'],'model_collection_copyright':col['copyright'],'model_objects':items,'canonical_metadata_sha256':hashlib.sha256((ROOT/'source/asset-metadata.json').read_bytes()).hexdigest(),'copyright_all_exactly_match':True,'scene_or_material_mutated':False,'native_resaved':False}
(ROOT/'review/native-metadata-check.json').write_text(json.dumps(report,indent=2)+'\n');print('NATIVE_METADATA_MATCH')
