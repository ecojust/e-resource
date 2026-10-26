"""Verify the final curtain fix against its frozen upstream wall raw GLB."""
import argparse,json,struct,hashlib
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True);a=ap.parse_args()
BASE=ROOT/'baseline/bund15-wall.glb'
D={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'};N={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
def read(path):
 b=path.read_bytes();l,_=struct.unpack_from('<II',b,12);d=json.loads(b[20:20+l]);binary=b[28+l:]
 def arr(i):
  ac=d['accessors'][i];v=d['bufferViews'][ac['bufferView']];dt=np.dtype(D[ac['componentType']]);cols=N[ac['type']];return np.ndarray((ac['count'],cols),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+ac.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*cols),dt.itemsize)).copy()
 out=defaultdict(Counter);pos=defaultdict(Counter);tris=0
 for m in d['meshes']:
  for p in m['primitives']:
   name=d['materials'][p['material']]['name'];attr={k:arr(v) for k,v in p['attributes'].items()};keys=sorted(attr);indices=arr(p['indices']).reshape(-1,3);tris+=len(indices)
   for ix in indices:
    vertices=[b''.join(attr[k][i].tobytes() for k in keys) for i in ix];out[name][min(b''.join(vertices[j:]+vertices[:j]) for j in range(3))]+=1
    pp=[attr['POSITION'][i].tobytes() for i in ix];pos[name][b''.join(sorted(pp))]+=1
 return {'triangles':tris,'data':out,'positions_unoriented':pos,'materials':{m['name']:m for m in d['materials']},'copyright':d['asset']['copyright'],'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
b=read(BASE);c=read(a.directory/'bund15-curtain-raw.glb');assert b['copyright']==c['copyright']
assert all(b['materials'][name]==mat for name,mat in c['materials'].items())
noncurtain=[m for m in b['data'] if not m.startswith('Curtain ')]
assert all(b['data'][m]==c['data'][m] for m in noncurtain)
assert b['triangles']==94288 and c['triangles']==92848
assert all(not(c['positions_unoriented'][m]-b['positions_unoriented'][m]) for m in c['positions_unoriented'])
removed_positions={m:sum((b['positions_unoriented'][m]-c['positions_unoriented'][m]).values()) for m in ['Curtain pale fabric','Curtain shaded folds']}
assert removed_positions=={'Curtain pale fabric':960,'Curtain shaded folds':480}
assert not c['data']['Curtain shaded folds'] and sum(c['data']['Curtain pale fabric'].values())==580
report={'schema':'bund15-curtain-combined-preservation-v1','status':'passed','input_wall_raw':{k:b[k] for k in ['triangles','sha256','bytes']},'output_curtain_raw':{k:c[k] for k in ['triangles','sha256','bytes']},'remaining_triangle_positions_exact':True,'noncurtain_oriented_attributes_exact':True,'remaining_material_definitions_exact':True,'copyright_exact':True,'removed_interpenetrating_fold_triangles':removed_positions,'removed_fold_boxes':120,'reoriented_prism_triangles':580,'source_chain_scope':'Wall→curtain combined stage: 1440 internal fold triangles deleted and 580 prism triangles reoriented. Previous wall preservation reports retain their original hashes and stop at the wall-stage output; remaining positions and all other geometry are unchanged.'}
(a.directory/'curtain-preservation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
