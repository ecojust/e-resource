"""Compare all non-limestone oriented triangle attributes in two raw GLBs.
Requires NumPy; does not alter models. Exact float values, not rounded hashes.
"""
import argparse, hashlib, json, struct
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def extract(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);blob=b[28+n:]
 def acc(i):
  d=g['accessors'][i];v=g['bufferViews'][d['bufferView']];c={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[d['type']];t=np.dtype({5123:'<u2',5125:'<u4',5126:'<f4'}[d['componentType']])
  return np.ndarray((d['count'],c),t,blob,v.get('byteOffset',0)+d.get('byteOffset',0),(v.get('byteStride',c*t.itemsize),t.itemsize))
 out={}
 for m in g['meshes']:
  for pr in m['primitives']:
   name=g['materials'][pr['material']]['name']
   if name=='limestone':continue
   index=acc(pr['indices']).ravel().reshape(-1,3);names=sorted(pr['attributes']);attrs=np.concatenate([acc(pr['attributes'][n]) for n in names],axis=1);rows=[]
   for tri in attrs[index]:
    v=[tuple(float(x) for x in q) for q in tri];rows.append(min(tuple(v[j:]+v[:j]) for j in range(3)))
   out[name]={'triangles':len(rows),'attributes':names,'oriented_attributes_sha256':hashlib.sha256(repr(sorted(rows)).encode()).hexdigest()}
 return out
before=extract(a.before);after=extract(a.after)
report={'before_sha256':hashlib.sha256(a.before.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(a.after.read_bytes()).hexdigest(),'non_limestone_all_attributes_exact':before==after,'materials':after}
a.output.write_text(json.dumps(report,indent=2)+'\n');assert before==after,'Non-wall geometry changed';print('PASS',sum(q['triangles'] for q in after.values()),'non-limestone oriented triangles preserve every attribute exactly')
