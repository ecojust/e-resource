"""Verify source-image crop matrices and visible construction details in the nine cameras."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from wing_frame import WingFrame

BASE=Path(__file__).resolve().parent
HELPER=BASE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Design image pixels at details also measurable from the architect's issued view.
SUBJECTS={
    'oak-entrance':[(255,219),(260,211),(284,203),(301,224),(313,194)],
    'front-dormers':[(198,157),(280,151),(346,168),(322,137)],
    'return-windows':[(120,214),(93,210),(106,216),(125,191)],
    'hip-dormers':[(114,164),(127,160),(93,166),(100,169),(144,138)],
    'roof-joint':[(152,165),(159,151),(165,138),(171,127)],
    'connecting-passage':[(398,199),(431,189),(450,165)],
}

def project(p,xyz):
    q=np.asarray(xyz)@p[:,:3].T+p[:,3]
    return q[...,:2]/q[...,2,None]

def matrix(v):
    eye=np.array(v['eye']);vector=np.array(v['target'])-eye;d=np.linalg.norm(vector)
    forward=vector/d;right=np.cross(forward,v.get('world_up',[0,0,1.]));right/=np.linalg.norm(right)
    up=np.cross(right,forward);rotation=np.array([right,-up,forward])
    w,h=v['width'],v['height'];fx=d*w/v['width_m'];cx,cy=v.get('principal_point_edge_px',[w/2,h/2])
    k=np.array([[fx,v.get('skew_px',0),cx-.5],[0,fx/v.get('pixel_aspect_y',1),cy-.5],[0,0,1]])
    return k@rotation@np.column_stack([np.eye(3),-eye])

def inspect(mesh):
    frame=WingFrame();cameras=BASE.parent/'source/cameras.json';config=json.loads(cameras.read_bytes())
    scene=runpy.run_path(str(HELPER))['SerialScene'](mesh);points=scene.tri.reshape(-1,3)
    collection={}
    for v in config:
        m=matrix(v);w,h=v['width'],v['height'];name=v['name']
        if name=='overview':
            uv=project(m,points)
            collection[name]={'margin_px':[float(uv[:,0].min()),float(uv[:,1].min()),float(w-uv[:,0].max()),float(h-uv[:,1].max())]}
        elif 'reference' in v:
            c=getattr(frame,v['reference'])
            original=c.K@c.R@np.column_stack([np.eye(3),-c.C])
            delta=project(m,points)-project(original,points)+v['source_crop'][:2]
            collection[name]={'reference':v['reference'],'source_dimensions':v['source_dimensions'],'crop':v['source_crop'],'max_native_pixel_error':float(np.max(abs(delta)))}
        else:
            eye=np.array(v['eye']);samples=[];source=frame.design
            for uv in SUBJECTS[name]:
                hit=scene.ray(source.C,source.ray(uv),450)
                row={'design_pixel':uv,'source_hit':bool(hit)}
                if hit:
                    p=np.array(hit['point_enu_m']);xy=project(m,p)
                    viewed=scene.ray(eye,p-eye,450);gap=None if not viewed else float(np.linalg.norm(np.array(viewed['point_enu_m'])-p))
                    row.update(source_material=hit['material'],viewed_material=viewed and viewed['material'],view_pixel=xy.tolist(),reprojection_distance_m=gap,in_frame=bool(0<=xy[0]<w and 0<=xy[1]<h),same_surface=bool(gap is not None and gap<.12))
                samples.append(row)
            collection[name]={'samples':samples}
    return {'mesh_sha256':scene.asset['sha256'],'cameras_sha256':hashlib.sha256(cameras.read_bytes()).hexdigest(),'views':collection}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('out',type=Path)
    a=cli.parse_args();j=inspect(a.mesh);a.out.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
    for k,v in j['views'].items():
        print(k,v.get('margin_px',v.get('max_native_pixel_error')),[(p['design_pixel'],p.get('in_frame'),p.get('same_surface')) for p in v.get('samples',[])])
