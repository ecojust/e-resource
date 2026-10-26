"""Verify the final native file contains its photograph and repair geometry."""
import argparse,bpy,hashlib,json,sys
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.open_mainfile(filepath=str(a.input));model=bpy.data.collections['MODEL_Bund18_Chartered_Bank'];images=[];triangles=0
for im in bpy.data.images:
 if im.packed_file:
  blob=im.packed_file.data;images.append({'name':im.name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
assert len(images)==1 and images[0]['bytes']==798956 and images[0]['sha256']=='26a1219fe534659ae78bae9dfc498aef30b50b957172046a5c401906758315ba'
meshes=[ob for ob in model.objects if ob.type=='MESH'];assert len(meshes)==16
for ob in meshes:ob.data.calc_loop_triangles();triangles+=len(ob.data.loop_triangles)
assert triangles==130374
report={'packed_images':images,'model_meshes':len(meshes),'triangles':triangles,'core_meshes':[ob.name for ob in meshes if ob.name.startswith('Bund18_WallCore_')],'portable':True};a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report))
