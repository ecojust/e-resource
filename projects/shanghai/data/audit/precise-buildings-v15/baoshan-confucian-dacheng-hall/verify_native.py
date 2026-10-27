"""Blender background: reopen the delivered native and check its model collection."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--expected-triangles',type=int,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.output.exists()
bpy.ops.wm.open_mainfile(filepath=str(a.native))
c=bpy.data.collections.get('Baoshan_Dacheng_Hall_Complete_Exterior');assert c
meshes=[o for o in c.all_objects if o.type=='MESH'];assert meshes
low=[math.inf]*3;high=[-math.inf]*3;triangles=0;vertices=0
for o in meshes:
    o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
    for v in o.data.vertices:
        pt=o.matrix_world@v.co;vertices+=1
        for i in range(3):
            assert math.isfinite(pt[i]);low[i]=min(low[i],pt[i]);high[i]=max(high[i],pt[i])
print(json.dumps({'actual_triangles':triangles,'expected_triangles':a.expected_triangles,'meshes':len(meshes)}),flush=True)
assert triangles==a.expected_triangles, f'Native triangle count {triangles} != raw {a.expected_triangles}'
assert a.native.stat().st_size<100_000_000
r={'passed':True,'file':str(a.native),'bytes':a.native.stat().st_size,'sha256':hashlib.sha256(a.native.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'meshes':len(meshes),'triangles':triangles,'vertices':vertices,'bounds_enu':[low,high],'model_collection':c.name,'scope':'Actually reopened compressed Blender file; finite model vertices and expected triangle count; preview stage/cameras excluded from model counts.'}
a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
