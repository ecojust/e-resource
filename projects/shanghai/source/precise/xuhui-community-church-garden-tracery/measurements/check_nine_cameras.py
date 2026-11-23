"""Check actual mesh extents, photograph registration and the five detail viewpoints."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Independent native-view targets. The short doorway is supplied by the old photograph
# and is intentionally omitted from the measured high-window views.
def originals(rows):
    w,h=3956,2967
    return [[(u+.5)*w/687-.5,(v+.5)*h/515-.5]for u,v in rows]
TARGETS={'seven-lights':('fayhoo2017',originals([(306,230),(355,240),(406,235)])),
         'foils':('fayhoo2017',originals([(339,176),(372,176),(356,167)])),
         'buttress':('fayhoo2017',originals([(438,135),(434,184),(435,225)])),
         'arch-moulding':('fayhoo2017',originals([(286,195),(351,125),(416,192)])),
         'stoop':('fayhoo2017',originals([(350,363),(338,371),(363,370)]))}
def project(p,points):
    uv=np.asarray(points)@p[:,:3].T+p[:,3]
    return uv[...,:2]/uv[...,2,None]


def check(mesh):
    refs=stations=json.loads((HERE/'church-registration.json').read_bytes())['stations']
    camfile=HERE.parent/'source/cameras.json';views=json.loads(camfile.read_bytes())
    scene=runpy.run_path(str(HELPER))['SerialScene'](mesh)
    points=scene.tri.reshape(-1,3)
    out={}
    for cam in views:
        name=cam['name'];w,h=cam['width'],cam['height']
        eye=np.array(cam['eye']);delta=np.asarray(cam['target'])-eye;distance=np.linalg.norm(delta)
        f=delta/distance;right=np.cross(f,cam.get('world_up',[0.,0.,1.]));right/=np.linalg.norm(right)
        up=np.cross(right,f);r=np.vstack((right,-up,f))
        cx,cy=cam.get('principal_point_edge_px',[w/2,h/2]);fx=w*distance/cam['width_m']
        k=np.array([[fx,0,cx-.5],[0,fx,cy-.5],[0,0,1]])
        p=k@np.column_stack((r,-r@eye))
        if name=='overview':
            uv=project(p,points)
            out[name]={'edge_margins_px':[uv[:,0].min(),w-1-uv[:,0].max(),uv[:,1].min(),h-1-uv[:,1].max()]}
        elif name in stations:
            ground=project(np.asarray(stations[name]['P']),points)-cam['source_crop'][:2]
            out[name]={'max_original_crop_reprojection_diff_px':float(np.max(np.abs(ground-project(p,points))))}
        else:
            ref,samples=TARGETS[name];cam0=refs[ref];c,r0,k0=[np.array(cam0[x])for x in ('C','R','K')]
            checks=[]
            for pixel in samples:
                ray=r0.T@np.linalg.solve(k0,[*pixel,1.])
                surface=scene.ray(c,ray/np.linalg.norm(ray),180)
                offset=[0,0]
                # A point between two thin bars intentionally sees through at the
                # recording station. For framing, report the nearest solid pixel.
                if not surface:
                    neighbors=sorted(((i,j)for i in range(-5,6)for j in range(-5,6)if 0<i*i+j*j<=25),key=lambda o:o[0]**2+o[1]**2)
                    for i,j in neighbors:
                        rr=r0.T@np.linalg.solve(k0,[pixel[0]+i,pixel[1]+j,1.])
                        surface=scene.ray(c,rr/np.linalg.norm(rr),180)
                        if surface:offset=[i,j];break
                if not surface:checks.append({'pixel':pixel,'reference_hit':None});continue
                pt=surface['point_enu_m'];u,v=project(p,pt);v0=np.array(pt)-eye;new=scene.ray(eye,v0/np.linalg.norm(v0),180)
                checks.append({'pixel':pixel,'framing_surface_pixel_offset':offset,'reference_material':surface['material'],'image_pos':[u,v],
                               'in_frame':bool(0<=u<w and 0<=v<h),'new_first_material':new and new['material']})
            out[name]={'controls':checks}
    return {'model_sha256':scene.asset['sha256'],'camera_sha256':hashlib.sha256(camfile.read_bytes()).hexdigest(),'views':out}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();args.output.write_text(json.dumps(check(args.mesh),indent=2)+'\n')
