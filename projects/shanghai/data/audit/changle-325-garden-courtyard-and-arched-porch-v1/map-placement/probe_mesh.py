"""Read original meshopt-decoded city LODs. Vertical probe material and height at garden controls."""
import json,struct, hashlib, math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

def read(path, points):
 b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);d=memoryview(b)[28+n:]
 def arr(idx):
  a=j['accessors'][idx];v=j['bufferViews'][a['bufferView']]
  dtype={5120:'i1',5122:'<i2',5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
  width={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];size=np.dtype(dtype).itemsize
  return np.ndarray((a['count'],width),dtype,buffer=d,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*width),size))
 heights={k:[]for k in points};owners={};all_tri=0
 for node in j['nodes']:
  mesh=j['meshes'][node['mesh']];inst=node.get('extensions',{}).get('EXT_mesh_gpu_instancing');t=s=r=None
  if inst:
   ats=inst['attributes'];t=arr(ats['TRANSLATION']);s=arr(ats['SCALE']);r=Rotation.from_quat(arr(ats['ROTATION'])).as_matrix()
  for p in mesh['primitives']:
   att=p['attributes'];v=arr(att['POSITION']);ind=arr(p['indices']).reshape(-1,3);tri=v[ind];fid=arr(att['_FEATURE_ID_0'])[ind[:,0]].ravel() if '_FEATURE_ID_0' in att else None
   if fid is not None:
    u,c=np.unique(fid,return_counts=True);owners.update({int(k):int(n)+owners.get(int(k),0)for k,n in zip(u,c)})
   tris=tri[None] if inst is None else np.einsum('iab,itvb->itva',r,tri[None]*s[:,None,None,:])+t[:,None,None,:]
   tri=tris.reshape(-1,3,3);all_tri+=len(tri);v0=tri[:,0];u=tri[:,1]-v0;v=tri[:,2]-v0;den=u[:,0]*v[:,2]-u[:,2]*v[:,0]
   for k,(x,z) in points.items():
    ids=np.where((np.abs(den)>1e-8)&(tri[:,:,0].min(1)<=x)&(tri[:,:,0].max(1)>=x)&(tri[:,:,2].min(1)<=z)&(tri[:,:,2].max(1)>=z))[0]
    delta0=x-v0[ids,0];delta2=z-v0[ids,2];a=(delta0*v[ids,2]-delta2*v[ids,0])/den[ids];bb=(u[ids,0]*delta2-u[ids,2]*delta0)/den[ids]
    valid=(a>=-1e-6)&(bb>=-1e-6)&(a+bb<=1.000001)
    i=ids[valid]; y=v0[i,1]+a[valid]*u[i,1]+bb[valid]*v[i,1]
    for tri_i,zval in zip(i,y):heights[k].append((round(float(zval),4),int(fid[tri_i])if fid is not None else None))
 return {'decoded_sha256':hashlib.sha256(b).hexdigest(),'expanded_triangles':all_tri,'heights':{k:sorted(set(h),reverse=True) for k,h in heights.items()},'far_triangles_per_feature':{k:owners.get(k)for k in [1869,229,5009,5597]} if owners else None}
