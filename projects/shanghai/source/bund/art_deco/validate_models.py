"""Validate actual exported buffers, indices, world bounds, and upload limits."""
import json,struct,hashlib,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
report={'coordinate_system':'glTF east/up/south metres','models':[],'passed':True}
def matrix(node):
 if 'matrix' in node:return np.array(node['matrix']).reshape((4,4),order='F')
 x,y,z,w=node.get('rotation',[0,0,0,1]);q=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w,0],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w,0],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y,0],[0,0,0,1.]])
 q[:3,:3]=q[:3,:3]@np.diag(node.get('scale',[1,1,1]));q[:3,3]=node.get('translation',[0,0,0]);return q
for slug in ['peace_north','bank_china','peace_south']:
 path=ROOT/slug/(slug+'.glb');data=path.read_bytes();magic,version,length=struct.unpack_from('<4sII',data);assert magic==b'glTF' and version==2 and length==len(data)
 jl,jt=struct.unpack_from('<II',data,12);j=json.loads(data[20:20+jl]);offset=20+jl;bl,bt=struct.unpack_from('<II',data,offset);binary=data[offset+8:offset+8+bl]
 types={5121:np.uint8,5123:np.uint16,5125:np.uint32,5126:np.float32}
 def access(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt=np.dtype(types[a['componentType']]);off=v.get('byteOffset',0)+a.get('byteOffset',0)
  return np.ndarray((a['count'],n),dtype=dt,buffer=binary,offset=off,strides=(v.get('byteStride',dt.itemsize*n),dt.itemsize))
 triangles=0;positions={}
 for mi,m in enumerate(j['meshes']):
  positions[mi]=[]
  for primitive in m['primitives']:
   pos=access(primitive['attributes']['POSITION']);assert np.isfinite(pos).all();idx=access(primitive['indices']).reshape(-1);assert idx.size%3==0 and idx.max()<len(pos);triangles+=idx.size//3;positions[mi].append(pos)
 bounds=[]
 def visit(ni,parent):
  n=j['nodes'][ni];world=parent@matrix(n)
  if 'mesh' in n:
   for p in positions[n['mesh']]:
    transformed=p@world[:3,:3].T+world[:3,3];bounds.extend([transformed.min(axis=0),transformed.max(axis=0)])
  for child in n.get('children',[]):visit(child,world)
 for node in j['scenes'][j.get('scene',0)]['nodes']:visit(node,np.eye(4))
 lo=np.array(bounds).min(axis=0);hi=np.array(bounds).max(axis=0);meta=json.loads((ROOT/slug/'metadata.json').read_text())
 assert abs(lo[1])<.0001,(slug,lo)
 assert triangles==meta['triangles'] and triangles<300000
 assert len(data)<100_000_000 and (ROOT/slug/(slug+'.blend')).stat().st_size<100_000_000
 item={'id':slug,'triangles':triangles,'glb_bytes':len(data),'blend_bytes':(ROOT/slug/(slug+'.blend')).stat().st_size,'sha256':hashlib.sha256(data).hexdigest(),'primitives':sum(len(m['primitives']) for m in j['meshes']),'bounds_east_up_south':{'min':lo.tolist(),'max':hi.tolist()},'finite_positions':True,'indices_in_range':True,'ground_zero':True,'under_100_MB':True,'origin_longitude':meta['origin_longitude'],'origin_latitude':meta['origin_latitude'],'replacement':meta['replacement']}
 report['models'].append(item);print(slug,triangles,len(data),'ground',lo[1])
(ROOT/'geometry-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
