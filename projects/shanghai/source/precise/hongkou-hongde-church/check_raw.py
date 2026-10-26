#!/usr/bin/env python3
"""Decode actual raw Float32 triangles: normals, true holes, glass fit and provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np
from shapely.geometry import Point
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'common'))
from photo_architecture import opening


def check(path):
    data=path.read_bytes();n,kind=struct.unpack_from('<II',data,12)
    assert struct.unpack_from('<4sII',data)==(b'glTF',2,len(data)) and kind==0x4e4f534a
    doc=json.loads(data[20:20+n]);binary=data[28+n:]
    assert not doc.get('images') and not doc.get('textures')
    assert all('uri' not in b for b in doc['buffers'])
    assert len(data)<40_000_000
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert doc['extras']['source_geometry_sha256']==sha(HERE/'geometry-input.json')
    assert doc['extras']['calibration_sha256']==sha(HERE/'calibration.json')
    assert doc['extras']['height_measured'] is False and doc['extras']['ground_base_m']==0
    assert all(t in doc['asset']['copyright'] for t in ['CC BY-SA4.0','Livelikerw','Windmemories','ODbL1.0','OFL1.1'])
    for i in [37225841,143735176]:assert doc['extras']['source_photo_sha256'][str(i)]==sha(HERE/f'photos/commons-{i}.jpg')
    def acc(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC3':3}[a['type']]
        assert not v.get('byteStride')
        return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*width).reshape(-1,width)
    meshes={};tris=0;errmax=0
    for p in doc['meshes'][0]['primitives']:
        x=acc(p['attributes']['POSITION']).astype(float);nn=acc(p['attributes']['NORMAL']).astype(float);t=acc(p['indices']).ravel().reshape(-1,3)
        cross=np.cross(x[t[:,1]]-x[t[:,0]],x[t[:,2]]-x[t[:,0]]);length=np.linalg.norm(cross,axis=1)
        assert np.isfinite(x).all() and np.isfinite(nn).all() and length.min()>1e-10
        cross/=length[:,None];normal=nn[t[:,0]];normal/=np.linalg.norm(normal,axis=1)[:,None]
        err=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',cross,normal),-1,1)));errmax=max(errmax,float(err.max()));assert err.max()<.001
        enu=x[:,[0,2,1]]*[1,-1,1];name=doc['materials'][p['material']]['name'];meshes[name]=enu[t];tris+=len(t)
    g=json.loads((HERE/'geometry-input.json').read_text());c=json.loads((HERE/'calibration.json').read_text());v=c['nominal_estimates_m']
    edge=g['front_edge'];O=np.r_[edge['center_local_east_north_m'],0.];T=-np.r_[edge['tangent_east_north'],0.];N=np.r_[edge['outward_normal_east_north'],0.]
    masonry=np.concatenate([m for name,m in meshes.items() if name.startswith('grey brick')]);allmesh=np.concatenate(list(meshes.values()))
    def ray(mesh,u,z,depth=0,far=.8):
        origin=O+T*u-N*depth+N*.20+[0,0,z];direction=-N
        e1=mesh[:,1]-mesh[:,0];e2=mesh[:,2]-mesh[:,0];h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h)
        good=np.abs(det)>1e-10;inv=np.zeros(len(det));inv[good]=1/det[good];s=origin-mesh[:,0];q=np.cross(s,e1)
        a=inv*np.einsum('ij,ij->i',s,h);b=inv*np.einsum('ij,j->i',q,direction);d=inv*np.einsum('ij,ij->i',e2,q)
        return int(np.sum(good&(a>=-1e-7)&(b>=-1e-7)&(a+b<=1+1e-7)&(d>1e-6)&(d<far)))
    holes=[('door',opening(0,.72,2.15,3.5,1.05),0)]
    holes += [('tower-middle-'+str(i),opening(u,6.05,w,3.25 if u==0 else 2.88,.72 if u==0 else 0),0) for i,(u,w) in enumerate([(-2,1.15),(0,1.55),(2,1.15)])]
    holes += [('tower-upper-'+str(i),opening(u,10.65,.7,1.65),0) for i,u in enumerate([-1.22,0,1.22])]
    for side in [-1,1]:
        center=side*(v['tower_width']/2+(edge['length_m']/2-v['tower_width']/2)*.54)
        holes += [('wing-arch-'+str(side),opening(center,.72,1.65,3.05,.82),v['wing_front_recess']),('wing-circle-'+str(side),Point(center,5.12).buffer(.70,quad_segs=20),v['wing_front_recess'])]
    results=[]
    for label,poly,depth in holes:
        safe=poly.buffer(-.14);x0,z0,x1,z1=safe.bounds;count=0
        for x in np.linspace(x0+.03,x1-.03,3):
            for z in np.linspace(z0+.03,z1-.03,3):
                if safe.contains(Point(x,z)):
                    hit=ray(masonry,x,z,depth);assert hit==0,(label,x,z,hit);count+=1
        assert count>0;results.append({'label':label,'masonry_interior_rays':count,'hits':0})
    negative=ray(masonry,3.10,5.0);assert negative>0
    entry=ray(allmesh,0,2.0,far=1.7);assert entry==0,'Entry blocked before open leaves/inner room'
    return {'schema':'hongde-actual-raw-check-v8','passed':True,'raw_sha256':sha(path),'raw_bytes':len(data),'triangles':tris,'materials':len(meshes),'max_actual_normal_error_degrees':errmax,
            'source_geometry_sha256':sha(HERE/'geometry-input.json'),'all_original_photo_sha_bound':True,'embedded_images':0,'opening_samples':results,'masonry_adjacent_negative_hits':negative,'open_entry_all_geometry_hits':entry,
            'footprint_owner_only':[2557],'retained_same_near_ids':g['replacement']['retained_same_near_feature_local_ids'],'height_measured':False,'visual_browser_accepted':False,
            'scope':'Actual raw triangles/normals and finite front aperture interior samples. Does not prove all roof intersections, hidden dimensions or visual similarity.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,default=HERE/'output/hongkou-hongde-church-raw.glb');p.add_argument('--report',type=Path,default=HERE/'audit/actual-raw-check.json');a=p.parse_args()
    report=check(a.glb);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['passed','raw_sha256','triangles','max_actual_normal_error_degrees']}))
