"""Check the uncluttered garden, retained roof limits, and first surfaces at measured camera landmarks."""
from pathlib import Path
import hashlib,json,math,struct,sys
import numpy as np

names=('raw','decoded-full','decoded-lod')
script=Path(__file__).resolve()
project=Path(sys.argv[3]).resolve() if len(sys.argv)>3 else next(p for p in script.parents if (p/'source/precise').is_dir())
src=project/'source/precise/changning-zhu-xueren-residence-yuyuan-garden-veranda/measurements'
reg=json.loads((src/'south-garden-two-view-registration.json').read_bytes());east=json.loads((src/'east-porch-five-view-world.json').read_bytes())
def mesh_data(path):
 raw=path.read_bytes();l,k=struct.unpack_from('<II',raw,12);gl=json.loads(raw[20:20+l]);blob=memoryview(raw)[28+l:];types={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}
 def arr(i):
  a=gl['accessors'][i];b=gl['bufferViews'][a['bufferView']];ct=np.dtype(types[a['componentType']]);count={'VEC3':3,'SCALAR':1}[a['type']];stride=b.get('byteStride',count*ct.itemsize)
  return np.ndarray((a['count'],count),dtype=ct,buffer=blob,offset=b.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,ct.itemsize))
 tris=[];mats=[]
 for m in gl['meshes']:
  for p in m['primitives']:
   v=arr(p['attributes']['POSITION']);tri=v[arr(p['indices']).reshape(-1,3)];tri=tri[:,:,[0,2,1]];tri[:,:,1]*=-1
   tris.append(tri);mats.extend([gl['materials'][p['material']]['name']]*len(tri))
 return np.concatenate(tris),mats,hashlib.sha256(raw).hexdigest()
def roof_cross(tri,x):
 seg=[]
 for i in range(3):
  v=tri[:,i,:2];u=tri[:,(i+1)%3,:2];dx=u[:,0]-v[:,0];mask=(np.minimum(v[:,0],u[:,0])<=x)&(np.maximum(v[:,0],u[:,0])>=x)&(abs(dx)>1e-7)
  vals=np.full(len(tri),np.nan);vals[mask]=v[mask,1]+(x-v[mask,0])/dx[mask]*(u[mask,1]-v[mask,1]);seg.append(vals)
 seg=np.array(seg);idx=np.isfinite(seg).sum(axis=0)>=2;seg=seg[:,idx]
 if not seg.shape[1]:return []
 spans=sorted(zip(np.nanmin(seg,axis=0),np.nanmax(seg,axis=0)));out=[]
 for lo,hi in spans:
  if not out or lo>out[-1][1]+.06:out.append([float(lo),float(hi)])
  else:out[-1][1]=max(out[-1][1],float(hi))
 return [[round(a,3),round(b,3)]for a,b in out if b-a>.04]
def scan(file):
 tri,mat,sha=mesh_data(file);full=tri.reshape(-1,3);mats=sorted(set(mat));mid=np.array([mats.index(s)for s in mat],dtype=np.int16)
 material_roof=[i for i,m in enumerate(mats) if any(s in m.lower() for s in ('weathered red flat tiles','earthen ridge caps','red tile edge'))]
 tiles=tri[np.isin(mid,material_roof)]
 profiles=[dict(x_m=x,red_roof_footprint_y_m=roof_cross(tiles,x)) for x in (-.5,1.25,5,9.4,12.2,15.5,17.75,19.5,21.5,24)]
 def query(xyz,d):
  # The ray is conditioned in float64. The mesh attributes are float32.
  here=None
  for i in range(0,len(tri),8192):
   t=tri[i:i+8192].astype('d');e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0];p=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,p)
   m=abs(det)>1e-9;inv=np.divide(1.,det,out=np.zeros_like(det),where=m);s=xyz-t[:,0];u=np.einsum('ij,ij->i',s,p)*inv;q=np.cross(s,e1);v=q@d*inv;dist=np.einsum('ij,ij->i',e2,q)*inv
   good=m&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(dist>.001)
   if not np.any(good):continue
   best=int(np.argmin(np.where(good,dist,np.inf)))
   if here is None or dist[best]<here[0]:here=(float(dist[best]),i+best)
  if here is None:return None
  distance,i=here;return dict(xyz_m=np.round(xyz+d*distance,3).tolist(),material=mat[i],distance_m=round(distance,3))
 def cast(P,uv):
  matx=np.array(P);eye=-np.linalg.solve(matx[:,:3],matx[:,3]);dir=np.linalg.solve(matx[:,:3],[*uv,1.]);dir/=np.linalg.norm(dir);return query(eye,dir)
 optical=[]
 for r in reg['rows']:
  cam=next(x for x in reg['cameras'] if x['file']==r['photo']);pt=r['observed_px'];hit=cast(cam['projection'],pt)
  optical.append(dict(photo=Path(r['photo']).name,feature=r['point'],px=pt,held_out=r['held_out'],first=hit))
 for r in east['observations']:
  if r['role'] not in ('held out','porch','garden-return'):continue
  optical.append(dict(photo=r['camera'],feature=r['feature'],px=r['observed_px'],held_out=r['role']=='held out',first=cast(east['garden_cameras'][r['camera']],r['observed_px'])))
 outside=[]
 for x,y in [(-1,3),(-1,10),(0,-4),(4,-4),(9,-4),(17,-4),(22.5,3),(25,6),(28,6),(9,22),(15,22),(20,22)]:
  outside.append(dict(site_local_xy_m=[x,y],first_from_above=query(np.array([x,y,30.]),np.array([0.,0.,-1.]))))
 assert not any(q['first_from_above'] for q in outside)
 return dict(sha256=sha,triangles=len(tri),bounds_xyz_m=[np.round(full.min(axis=0),3).tolist(),np.round(full.max(axis=0),3).tolist()],tile_bounds_xyz_m=[np.round(tiles.min(axis=(0,1)),3).tolist(),np.round(tiles.max(axis=(0,1)),3).tolist()],roof_profiles=profiles,garden_and_unattributed_buildings=outside,photo_rays=optical)
if __name__=='__main__':
 f=Path(sys.argv[1]);out=Path(sys.argv[2]);result=scan(f);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['sha256'],result['triangles'],result['roof_profiles'],sum(i['first'] is not None for i in result['photo_rays']),len(result['photo_rays']))
