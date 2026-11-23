"""First-hit material using ordinary decoded GLB vertices and the two photo matrices."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np

def triangles(p):
    b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);body=memoryview(b)[28+n:]
    def a(i):
        c=j['accessors'][i];v=j['bufferViews'][c['bufferView']]
        dtype={5123:'<u2',5125:'<u4',5126:'<f4',5121:'u1'}[c['componentType']]
        nc={'VEC3':3,'SCALAR':1}[c['type']]
        begin=v.get('byteOffset',0)+c.get('byteOffset',0)
        vals=np.ndarray((c['count'],nc),dtype=dtype,buffer=body,offset=begin,
                        strides=(v.get('byteStride',nc*np.dtype(dtype).itemsize),np.dtype(dtype).itemsize))
        return np.array(vals)
    alltri=[];names=[]; mats=[m.get('name','') for m in j['materials']]
    for mesh in j['meshes']:
        for c in mesh['primitives']:
            v=a(c['attributes']['POSITION']).astype(float)
            enu=v[:,[0,2,1]]*[1,-1,1]
            ix=a(c['indices']).ravel(); alltri.append(enu[ix].reshape(-1,3,3))
            names.extend([mats[c['material']]]*(len(ix)//3))
    return np.concatenate(alltri),np.array(names)

def probe(path,cameras,controls):
    tri,names=triangles(path);a=tri[:,0];e1=tri[:,1]-a;e2=tri[:,2]-a
    rows=[]; frame=np.array(cameras['ENU_from_uzd']);origin=np.array(cameras['origin_enu'])
    for k,points in controls['native_pixels_by_station'].items():
        c=cameras['cameras'][k];p=np.array(c['P_uzd']);eye=np.array(c['C_uzd']);source=origin+frame@eye
        for point in points:
            uv=point['pixel']; dr=frame@np.linalg.solve(p[:,:3],[*uv,1.]); dr/=np.linalg.norm(dr)
            t=source-a;h=np.cross(dr,e2);det=np.einsum('ij,ij->i',e1,h); on=np.abs(det)>1e-11
            inv=np.divide(1.,det,out=np.zeros_like(det),where=on);u=np.einsum('ij,ij->i',t,h)*inv
            q=np.cross(t,e1);v=q@dr*inv;distance=np.einsum('ij,ij->i',e2,q)*inv
            distance[~(on&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1.0000001)&(distance>.0001))]=np.inf
            i=int(np.argmin(distance));hit=names[i] if np.isfinite(distance[i]) else None
            rows.append({'station':k,'feature':point['feature'],'native_pixel':uv,'wanted':point['material'],'actual':hit,'hit':hit==point['material']})
    return {'source':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'direct':sum(r['hit'] for r in rows),'total':len(rows),'rows':rows}

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mesh',type=Path);cli.add_argument('cameras',type=Path);cli.add_argument('controls',type=Path);cli.add_argument('out',type=Path)
    ar=cli.parse_args();report=probe(ar.mesh,json.loads(ar.cameras.read_bytes()),json.loads(ar.controls.read_bytes()));ar.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report['source'],report['direct'],report['total'])
