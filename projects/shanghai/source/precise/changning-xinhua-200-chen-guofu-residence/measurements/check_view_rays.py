"""Intersect each marked photo pixel with the decoded near and far meshes."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import struct
import numpy as np

def triangles(path):
    with path.open('rb') as src, mmap.mmap(src.fileno(),0,access=mmap.ACCESS_READ) as blob:
        n=struct.unpack_from('<I',blob,12)[0]
        doc=json.loads(blob[20:20+n])
        def array(index):
            a=doc['accessors'][index]
            v=doc['bufferViews'][a['bufferView']]
            kind=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
            width={'SCALAR':1,'VEC3':3}[a['type']]
            start=28+n+v.get('byteOffset',0)+a.get('byteOffset',0)
            return np.ndarray((a['count'],width),kind,buffer=blob,offset=start,strides=(v.get('byteStride',kind.itemsize*width),kind.itemsize))
        for idx in doc['scenes'][doc.get('scene',0)]['nodes']:
            node=doc['nodes'][idx]
            assert set(node) <= {'name','mesh'}
            for p in doc['meshes'][node['mesh']]['primitives']:
                assert p.get('mode',4)==4
                mat=doc['materials'][p['material']]['name']
                pos=array(p['attributes']['POSITION'])
                ix=array(p['indices']).reshape(-1,3)
                for start in range(0,len(ix),1024):
                    coords=pos[ix[start:start+1024]][:,:,[0,2,1]].astype(float)
                    coords[:,:,1]*=-1
                    yield mat,coords
                del pos,ix

def survey(path, stations):
    records={};rays=[]
    for key,cam in stations.items():
        C,R,K=map(np.asarray,(cam['C'],cam['R'],cam['K']))
        for name,v in cam['controls'].items():
            d=R.T@np.linalg.solve(K,[*v['observed'],1])
            result=dict(observed_px=v['observed'],holdout=v['heldout'],projection_residual_px=v['residual_px'],first_hit=None)
            records.setdefault(key,{})[name]=result
            rays.append([C,d/np.linalg.norm(d),np.array(v['xyz']),float('inf'),result])
    for material,tr in triangles(path):
        e1=tr[:,1]-tr[:,0];e2=tr[:,2]-tr[:,0]
        for ray in rays:
            C,d,reference,nearest,obs=ray
            p=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,p)
            valid=np.abs(det)>1e-10
            inv=np.divide(1.,det,out=np.zeros_like(det),where=valid)
            s=C-tr[:,0];u=np.einsum('ij,ij->i',s,p)*inv;q=np.cross(s,e1)
            v=(q@d)*inv;t=np.einsum('ij,ij->i',e2,q)*inv
            valid&=(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>0)&(t<nearest)
            if valid.any():
                distance=float(t[valid].min());position=C+distance*d;ray[3]=distance
                obs['first_hit']=dict(material=material,distance_m=round(distance,6),local_xyz_m=position.round(6).tolist(),distance_to_selected_control_m=round(float(np.linalg.norm(position-reference)),6))
    return dict(sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),stations=records)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded_near',type=Path);parser.add_argument('decoded_far',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    stations=json.loads(Path(__file__).with_name('two-stations.json').read_bytes())
    results={key:survey(p,stations) for key,p in [('near',args.decoded_near),('far',args.decoded_far)]}
    args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

