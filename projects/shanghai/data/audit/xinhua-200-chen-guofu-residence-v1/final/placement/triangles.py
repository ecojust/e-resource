import numpy as np,struct,json,math
from probe_mesh import rotations
def configure(ready_doc, origin, azimuth, feature):
 global ready,lon,lat,A,R,merc,owner_id
 ready=ready_doc;lon,lat=origin;A=math.radians(azimuth);R=6378137*math.cos(math.radians(ready['origin_latitude']));merc=math.asinh(math.tan(math.radians(ready['origin_latitude'])));owner_id=feature
def local(a):
 a=a.astype(np.float64,copy=False)
 e=(ready['origin_longitude']+np.degrees(a[:,:,0]/R)-lon)*111320*math.cos(math.radians(lat))
 n=(np.degrees(np.arctan(np.sinh(merc-a[:,:,2]/R)))-lat)*110860
 return np.stack([e*math.sin(A)+n*math.cos(A),-e*math.cos(A)+n*math.sin(A),a[:,:,1]],axis=-1)
def city_tri(path):
 raw=path.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+jl]);b=memoryview(raw)[28+jl:]
 def get(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];typ={5120:'i1',5122:'<i2',5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']];n={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
  return np.ndarray((a['count'],n),typ,buffer=b,offset=a.get('byteOffset',0)+v.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(typ).itemsize*n),np.dtype(typ).itemsize))
 for node in j['nodes']:
  parts=j['meshes'][node['mesh']]['primitives'];inst=node.get('extensions',{}).get('EXT_mesh_gpu_instancing');transform=None
  if inst:
   at=inst['attributes'];transform=(get(at['TRANSLATION']),get(at['SCALE']),rotations(get(at['ROTATION'])))
  for p in parts:
   mat=j['materials'][p['material']]['name'];ind=get(p['indices']).reshape(-1,3);tri=get(p['attributes']['POSITION'])[ind]
   if inst:
    t,s,r=transform
    groups=np.einsum('iab,itvb->itva',r,tri[None]*s[:,None,None,:])+t[:,None,None,:]
    tri=groups.reshape(-1,3,3)
   if '_FEATURE_ID_0'in p['attributes']:
    F=get(p['attributes']['_FEATURE_ID_0'])[ind[:,0]].reshape(-1)
    for fid in (owner_id,):
     pick=F==fid
     if pick.any():yield mat+' owner '+str(fid),local(tri[pick])
   else:yield mat,local(tri)
def sat(one,many):
 # Separating axes for two triangles, including the in-plane edge normals for coplanar contacts.
 a=np.roll(one,-1,axis=0)-one;b=np.roll(many,-1,axis=1)-many
 na=np.cross(a[0],a[1]);nb=np.cross(b[:,0],b[:,1]);ok=np.ones(len(many),dtype=bool)
 axes=[na,nb]+[np.cross(x,b[:,j]) for x in a for j in range(3)]+[np.cross(na,x)for x in a]+[np.cross(nb,b[:,j])for j in range(3)]
 for ax in axes:
  if ax.ndim==1:ax=np.broadcast_to(ax,(len(many),3))
  norm=np.linalg.norm(ax,axis=1);tol=2e-6*norm
  v=one@ax.T;u=np.einsum('ij,ikj->ik',ax,many)
  ok&=(v.max(0)>=u.min(1)-tol)&(u.max(1)>=v.min(0)-tol)
 return ok
