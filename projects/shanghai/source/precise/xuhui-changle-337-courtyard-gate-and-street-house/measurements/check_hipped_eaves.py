"""Trace registered exterior photographs onto the decoded triangular meshes."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
from register_street import Camera
HERE=Path(__file__).resolve().parent

def triangles(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];gl=json.loads(data[20:20+n]);buf=memoryview(data)[28+n:]
 def acc(idx):
  a=gl['accessors'][idx];v=gl['bufferViews'][a['bufferView']];dt={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]; comp={'SCALAR':1,'VEC3':3}[a['type']]
  return np.ndarray((a['count'],comp),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*comp),np.dtype(dt).itemsize))
 ts=[];ids=[]
 for mesh in gl['meshes']:
  for prim in mesh['primitives']:
   pos=acc(prim['attributes']['POSITION']);xyz=pos[:,[0,2,1]].astype(float);xyz[:,1]*=-1;idx=acc(prim['indices']).reshape(-1,3);ts.append(xyz[idx]);ids.extend([prim['material']]*len(idx))
 return np.vstack(ts),np.asarray(ids),[m['name']for m in gl['materials']]

def inspect(path,controls):
 tri,mat,names=triangles(path);e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];rows=[]
 for view,picks in controls.items():
  c=Camera(view);offset=c.c-tri[:,0];cross=np.cross(offset,e1)
  for feature,pixel,expected in picks:
   ray=c.ray(pixel);p=np.cross(ray,e2);det=(p*e1).sum(axis=1);inv=1/np.where(abs(det)>1e-10,det,1e-10)
   u=(p*offset).sum(axis=1)*inv;v=(cross@ray)*inv;d=(e2*cross).sum(axis=1)*inv;ok=(abs(det)>1e-10)&(u>=0)&(v>=0)&(u+v<=1)&(d>0)
   if ok.any():
    i=np.argmin(np.where(ok,d,np.inf));name=names[mat[i]];hit=(c.c+ray*d[i]).round(5).tolist()
   else:name=None;hit=None
   rows.append({'view':view,'pixel':pixel,'feature':feature,'observed_material':name,'world_hit':hit,'expected_fragments':expected,'passed':bool(name and any(e in name for e in expected))})
 return {'raw_file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'count':len(rows),'direct':sum(r['passed'] for r in rows),'rays':rows}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('glb',type=Path);parser.add_argument('out',type=Path);a=parser.parse_args();out=inspect(a.glb,json.loads((HERE/'hipped-roof-controls.json').read_bytes())['surface_points']);a.out.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(out['direct'],out['count'])
