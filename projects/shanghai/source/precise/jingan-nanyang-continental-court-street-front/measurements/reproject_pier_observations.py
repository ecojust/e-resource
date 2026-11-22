"""Repeat the measured elevations and the return-depth estimates from the original clicks."""
from pathlib import Path
import json
import numpy as np

HERE=Path(__file__).resolve().parent

def recompute(evidence, layout, portal):
    plan=np.asarray(layout['pier_tip_axes_m']);values=[]
    for r in evidence['observations']:
        station=r['station'];uv=np.array(r['native_px'])
        if r['source']=='high11':
            H=np.asarray(portal['local_P'])[:,[0,2,3]]
            q=np.linalg.solve(H,np.r_[uv,1]);value=q[:2]/q[2]
            assert np.allclose(value,r['local_204_front_x_z_m'],atol=.0001)
        else:
            d=r['reference_d_m'];cam={'gao00':'a','gao08':'c'}[r['source']]
            width=evidence['sources'][r['source']]['size'][0]
            p=np.asarray(evidence['camera_512'][cam]);m=p[:,:2]
            t=plan[min(station+1,11)]-plan[max(station-1,0)];t=t/np.linalg.norm(t)
            n=np.array([-t[1],t[0]])
            def at(depth):
                h=np.column_stack((m@t,p[:,2],m@(plan[station]+n*depth)+p[:,3]))
                q=np.linalg.solve(h,np.r_[uv*512/width,1.]);return q[:2]/q[2]
            value=at(d)
            assert np.allclose(value,r['t_z_m'],atol=.0001)
            if r.get('axis_center_assumption_depth_m') is not None:
                a,b=at(0),at(1)
                assert abs(-a[0]/(b[0]-a[0])-r['axis_center_assumption_depth_m'])<.001
        values.append(value.tolist())
    return values

if __name__=='__main__':
    load=lambda n:json.loads((HERE/n).read_text())
    v=recompute(load('pointed-piers-photo-evidence.json'),load('street-frontage-layout.json'),load('204-front-metric-camera.json'))
    print(len(v),'photographic measurements reproduced')
