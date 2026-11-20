"""Confirm that the current roof study adds two materials while preserving every prior oriented surface."""
from pathlib import Path
import argparse, hashlib, json, struct, sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'source'))
from verify_serialized import load
ap=argparse.ArgumentParser()
ap.add_argument('--old',type=Path,required=True);ap.add_argument('--revised',type=Path,required=True)
ap.add_argument('--old-packed',type=Path);ap.add_argument('--new-packed',type=Path);ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
def record(p):
 return {'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
before,tags0,old=load(args.old,args.old_packed);after,tags1,new=load(args.revised,args.new_packed)
def material_info(path):
 data=path.read_bytes()
 n=struct.unpack_from('<I',data,12)[0]
 doc=json.loads(data[20:20+n])
 return {m['name']:m for m in doc['materials']}
old_materials=material_info(args.old_packed or args.old)
new_materials=material_info(args.new_packed or args.revised)
assert set(new_materials)-set(old_materials)=={'cover panel','cover frame'}
assert all(new_materials[name]==value for name,value in old_materials.items()),'Existing glTF material properties changed'

assert set(new)-set(old)=={'cover panel','cover frame'}
assert not (set(old)-set(new))
for material,old_hash in old.items():
 assert old_hash==new[material], f'Existing oriented triangles changed for {material}'
new_triangles=after[np.isin(tags1,['cover panel','cover frame'])]
low=new_triangles.reshape(-1,3).min(0);high=new_triangles.reshape(-1,3).max(0)
assert np.allclose(low,[-2.4,-3.75,10.10],atol=3e-5)
assert np.allclose(high,[8.4,1.55,10.42],atol=3e-5)
assert len(after)-len(before)==len(new_triangles)==144
r={'old':record(args.old_packed or args.old),'revised':record(args.new_packed or args.revised),'old_triangles':len(before),'revised_triangles':len(after),'added_triangles':len(new_triangles),'old_oriented_float32_digest_by_material':old,'revised_oriented_float32_digest_by_material':new,'added_bounds_enu_m':[low.tolist(),high.tolist()],'all_existing_geometry_and_material_assignments_match':True,'all_existing_gltf_material_properties_unchanged':True}
args.out.write_text(json.dumps(r,indent=2)+'\n')
print(str(args.out),len(before),len(after))
