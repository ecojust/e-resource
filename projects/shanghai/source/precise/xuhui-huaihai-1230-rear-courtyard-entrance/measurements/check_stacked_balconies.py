"""Check the 2013 and 2016 courtyard rail and sash pixels against original or independently decoded meshes."""
from pathlib import Path
import argparse,hashlib,json,struct
import numpy as np
from register_court import Camera
HERE=Path(__file__).absolute().parent
def proof(mesh,station,rows=None):
    blob=mesh.read_bytes();size=struct.unpack_from('<I',blob,12)[0]
    doc=json.loads(blob[20:20+size]);data=memoryview(blob)[28+size:]
    def arr(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];k={'SCALAR':1,'VEC3':3}[a['type']]
        dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        return np.ndarray((a['count'],k),dt,buffer=data,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',k*dt.itemsize),dt.itemsize))
    tri=[];mat=[];names=[m['name'] for m in doc['materials']]
    for m in doc['meshes']:
        for q in m['primitives']:
            v=arr(q['attributes']['POSITION'])[:,[0,2,1]].copy();v[:,1]*=-1
            f=arr(q['indices']).reshape(-1,3);tri.append(v[f]);mat.append(np.full(len(f),q['material']))
    t=np.concatenate(tri);materials=np.concatenate(mat);a=t[:,0];e1=t[:,1]-a;e2=t[:,2]-a
    cam=Camera(station);eye=cam.c;records=[]
    if rows is None:
        rows=json.loads((HERE/'stacked-balcony-controls.json').read_bytes())['native_pixel_controls'][station]
    for sample in rows:
        d=cam.ray(sample['uv']);d=d/np.linalg.norm(d)
        h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);inv=np.divide(1.,det,out=np.zeros_like(det),where=np.abs(det)>1e-9)
        s=eye-a;u=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1);v=(q@d)*inv;dr=np.einsum('ij,ij->i',q,e2)*inv
        dr[~((np.abs(det)>1e-9)&(u>=0)&(v>=0)&(u+v<=1)&(dr>0))]=np.inf
        j=int(dr.argmin());hit=bool(np.isfinite(dr[j]));actual=names[materials[j]] if hit else None
        xyz=eye+dr[j]*d if hit else None
        through=(not hit or xyz[1]>-.05)
        passed=through if sample['wanted']=='through' else actual==sample['wanted']
        records.append({**sample,'actual':actual,'hit_xyz':np.round(xyz,4).tolist() if hit else None,'passed':bool(passed)})
    return dict(station=station,sha256=hashlib.sha256(blob).hexdigest(),passed=sum(x['passed']for x in records),count=len(records),rays=records)
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mesh',type=Path);cli.add_argument('station',choices=['04','25']);cli.add_argument('out',type=Path);args=cli.parse_args()
    r=proof(args.mesh,args.station);args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(r['passed'],r['count'])
