"""Read the genuinely delivered floating-point positions and material assignments."""
from pathlib import Path
import sys,struct,hashlib,json,ctypes as ct
import numpy as np
from PIL import Image
W=Path(__file__).parent; M=W/'mesh'
def decode(f):
 data=f.read_bytes();length,=struct.unpack_from('<I',data,12);j=json.loads(data[20:20+length]);buf=memoryview(data)[28+length:];parts=[];names=[];palette=[]
 assert all(set(node)<=set(('name','mesh'))for node in j['nodes'])
 def acc(index):
  a=j['accessors'][index];v=j['bufferViews'][a['bufferView']];dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);n={'VEC3':3,'SCALAR':1}[a['type']];return np.ndarray((a['count'],n),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*n),dt.itemsize))
 for node in j['nodes']:
  for g in j['meshes'][node['mesh']]['primitives']:
   vertices=acc(g['attributes']['POSITION']);ii=acc(g['indices']).ravel();v=vertices[ii].reshape(-1,3,3).astype(float);v=v[:,:,[0,2,1]];v[:,:,1]*=-1;parts.append(v);m=j['materials'][g['material']];palette.append(m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1.,1.,1.,1.])[:3]);names.extend([m['name']]*len(v))
 return np.concatenate(parts),np.array(names),{m['name']:m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1.,1.,1.,1.])[:3] for m in j['materials']}
def norm(v):return v/np.linalg.norm(v)
def hit(t,m,o,d):
 v1=t[:,1]-t[:,0];v2=t[:,2]-t[:,0];p=np.cross(np.broadcast_to(d,v2.shape),v2);det=(v1*p).sum(1);ok=np.abs(det)>1e-9;iv=np.zeros_like(det);iv[ok]=1/det[ok];s=o-t[:,0];u=iv*(s*p).sum(1);q=np.cross(s,v1);v=iv*(q*d).sum(1);r=iv*(v2*q).sum(1);ok&=(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(r>1e-6);ix=np.flatnonzero(ok)
 if len(ix)==0:return None
 i=ix[np.argmin(r[ix])];return str(m[i]),(o+d*r[i]).tolist()
