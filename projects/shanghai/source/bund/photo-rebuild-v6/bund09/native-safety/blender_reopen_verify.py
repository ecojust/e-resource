"""Parent-only Blender reopen: model triangles/bounds and packed source JPEG.

blender -b --python blender_reopen_verify.py -- --native file.blend \
  --raw ../output/bund09-raw.glb --report native-reopen.json
"""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser();ap.add_argument('--native',type=Path,required=True);ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--report',type=Path,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);raw=a.raw.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=raw[28+jl:]
assert len(raw)<100_000_000 and a.native.stat().st_size<100_000_000
native_sha=hashlib.sha256(a.native.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(a.native.resolve()))
collection=bpy.data.collections.get('Photo_reconstructed_architecture');assert collection
objects=[o for o in collection.all_objects if o.type=='MESH'];assert objects
triangles=0;points=[]
for o in objects:
    o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
    points.extend(o.matrix_world@Vector(v) for v in o.bound_box)
primitives=[p for mesh in doc['meshes'] for p in mesh['primitives']]
expected_triangles=sum(doc['accessors'][p['indices']]['count']//3 for p in primitives)
assert triangles==expected_triangles,(triangles,expected_triangles)
rawmin=[min(doc['accessors'][p['attributes']['POSITION']]['min'][k] for p in primitives) for k in range(3)]
rawmax=[max(doc['accessors'][p['attributes']['POSITION']]['max'][k] for p in primitives) for k in range(3)]
expected_min=[rawmin[0],-rawmax[2],rawmin[1]];expected_max=[rawmax[0],-rawmin[2],rawmax[1]]
actual_min=[min(p[k] for p in points) for k in range(3)];actual_max=[max(p[k] for p in points) for k in range(3)]
delta=max(abs(x-y) for x,y in zip(actual_min+actual_max,expected_min+expected_max));assert delta<.00002,delta
expected_images=[]
for im in doc.get('images',[]):
    view=doc['bufferViews'][im['bufferView']];start=view.get('byteOffset',0);data=binary[start:start+view['byteLength']]
    expected_images.append({'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
actual_images=[]
for im in bpy.data.images:
    if im.name in ('Render Result','Viewer Node'):continue
    assert im.packed_file,im.name
    data=im.packed_file.data;actual_images.append({'name':im.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
assert sorted((x['bytes'],x['sha256']) for x in actual_images)==sorted((x['bytes'],x['sha256']) for x in expected_images)
assert hashlib.sha256(a.native.read_bytes()).hexdigest()==native_sha
report={'schema':'compressed-native-reopen-v1','passed':True,'blender_version':bpy.app.version_string,'native_sha256':native_sha,'native_bytes':a.native.stat().st_size,'source_raw_sha256':hashlib.sha256(raw).hexdigest(),'architecture_collection_only':True,'model_meshes':len(objects),'triangles':triangles,'expected_triangles':expected_triangles,'bounds_blender':{'min':actual_min,'max':actual_max},'max_bound_delta_m':delta,'source_jpeg_packed_byte_identical':True,'packed_images':actual_images,'native_file_unmodified_by_reopen':True,'visual_acceptance':'Separate parent render/browser review; not performed by this checker.'}
a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
