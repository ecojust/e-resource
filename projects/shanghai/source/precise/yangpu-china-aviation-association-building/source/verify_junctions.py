"""Focused serialized-ray checks for roof junction closure and coplanar seams."""
import argparse,json,struct,hashlib
from pathlib import Path
import numpy as np

def load(path):
 data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);binary=data[28+size:]
 def acc(k):
  ac=doc['accessors'][k];bv=doc['bufferViews'][ac['bufferView']];dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']];n={'SCALAR':1,'VEC3':3}[ac['type']];offset=bv.get('byteOffset',0)+ac.get('byteOffset',0);stride=bv.get('byteStride',np.dtype(dtype).itemsize*n)
  return np.ndarray((ac['count'],n),dtype=dtype,buffer=binary,offset=offset,strides=(stride,np.dtype(dtype).itemsize))
 triangles=[];materials=[]
 for mesh in doc['meshes']:
  for pr in mesh['primitives']:
   v=acc(pr['attributes']['POSITION']).astype(float);v=v[:,[0,2,1]]*np.array([1,-1,1]);f=acc(pr['indices']).reshape(-1,3).astype(int);triangles.append(v[f]);materials.extend([doc['materials'][pr['material']]['name']]*len(f))
 return np.concatenate(triangles),np.asarray(materials)
def ray(tri,materials,origin,direction):
 o=np.asarray(origin,float);d=np.asarray(direction,float);a,b,c=tri[:,0],tri[:,1],tri[:,2];e1=b-a;e2=c-a;h=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);good=np.abs(det)>1e-10;inv=np.zeros(len(det));inv[good]=1/det[good];s=o-a;u=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1);v=q@d*inv;t=np.einsum('ij,ij->i',e2,q)*inv;valid=good&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>1e-6);idx=np.where(valid)[0]
 if not len(idx):return None
 best=idx[np.argmin(t[idx])];same=idx[np.abs(t[idx]-t[best])<1e-5]
 return {'distance_m':float(t[best]),'point_enu':(o+d*t[best]).tolist(),'materials_at_nearest_hit':sorted(set(materials[same]))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();tri,mats=load(a.raw)
 tests=[('front high-low junction',[-2.4,1.13,9.5],[-1,0,0],-4.4),('rear junction above low roof edge',[16.2,-2.8,7.95],[1,0,0],17.2),('front roof seam below cap',[-16,10,10.5],[1,0,0],-14.8),('front roof seam just above roof',[-16,10,10.61],[1,0,0],-14.8),('rear portal raised face',[27,1.15,8.4],[-1,0,0],25.25),('front foot seam',[-16,10,.06],[1,0,0],-14.8)]
 records=[]
 for name,o,d,x in tests:
  hit=ray(tri,mats,o,d);passed=bool(hit and abs(hit['point_enu'][0]-x)<.002 and hit['materials_at_nearest_hit']==['pale grey stone']);records.append({'name':name,'origin_enu':o,'direction_enu':d,'expected_first_wall_x':x,'hit':hit,'passed':passed})
 out={'id':'yangpu-china-aviation-association-building','raw_sha256':hashlib.sha256(a.raw.read_bytes()).hexdigest(),'scope':'Six focused rays at observed roof-height gaps/coplanar seams, not a proof of every possible exterior ray.','records':records,'passed':all(r['passed']for r in records)};a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed']else 1)
