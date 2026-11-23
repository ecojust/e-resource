"""Check actual mesh extents, photograph registration and the six detail viewpoints."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Frozen points on the archive photographs, chosen to check display framing.
TARGETS={
 'four-sashes':('garden-2026',[(187,260),(459,249),(715,250),(983,251)]),
 'western-casements':('garden-2026',[(185,261),(225,257),(281,249)]),
 'hip-flashing':('garden-2026',[(966,282),(1134,303),(1102,240)]),
 'centre-chimney':('garden-2026',[(646,103),(640,145),(650,169)]),
 'corbels':('garden-2026',[(327,372),(328,405),(330,434)]),
 'upper-parapet':('garden-2026',[(987,472),(1040,491),(1093,472)])}
def project(p,points):
    uv=np.asarray(points)@p[:,:3].T+p[:,3]
    return uv[...,:2]/uv[...,2,None]


def check(mesh):
    refs=stations=json.loads((HERE/'roof-registration.json').read_bytes())['stations']
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
            ref,samples=TARGETS[name];cam0=refs[ref];c,r0,k0=[np.array(cam0[x])for x in ('eye','R','K')]
            checks=[]
            for pixel in samples:
                ray=r0.T@np.linalg.solve(k0,[*pixel,1.])
                surface=scene.ray(c,ray/np.linalg.norm(ray),500)
                offset=[0,0]
                # A point between two thin bars intentionally sees through at the
                # recording station. For framing, report the nearest solid pixel.
                if not surface:
                    neighbors=sorted(((i,j)for i in range(-5,6)for j in range(-5,6)if 0<i*i+j*j<=25),key=lambda o:o[0]**2+o[1]**2)
                    for i,j in neighbors:
                        rr=r0.T@np.linalg.solve(k0,[pixel[0]+i,pixel[1]+j,1.])
                        surface=scene.ray(c,rr/np.linalg.norm(rr),500)
                        if surface:offset=[i,j];break
                if not surface:checks.append({'pixel':pixel,'reference_hit':None});continue
                pt=surface['point_enu_m'];u,v=project(p,pt);v0=np.array(pt)-eye;new=scene.ray(eye,v0/np.linalg.norm(v0),500)
                checks.append({'pixel':pixel,'framing_surface_pixel_offset':offset,'reference_material':surface['material'],'image_pos':[u,v],
                               'in_frame':bool(0<=u<w and 0<=v<h),'new_first_material':new and new['material']})
            out[name]={'controls':checks}
    return {'model_sha256':scene.asset['sha256'],'camera_sha256':hashlib.sha256(camfile.read_bytes()).hexdigest(),'views':out}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();args.output.write_text(json.dumps(check(args.mesh),indent=2)+'\n')
