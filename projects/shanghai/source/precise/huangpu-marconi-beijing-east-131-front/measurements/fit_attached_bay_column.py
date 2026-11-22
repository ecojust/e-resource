"""Fit the taper and plan centre of the eastern fluted shaft to measured silhouette pairs."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from marconi_photo_plane import CALIBRATION
EDGES={
    '2017_front':[(3460,1920,1981),(3520,1919,1980),(3600,1917,1977),(3680,1915,1974),(3760,1913,1972)],
    '2015_oblique':[(4920,1737,1812),(5020,1738,1813),(5120,1738,1812),(5200,1737,1810)],
}

def fit():
    theta=np.linspace(0.,2*np.pi,360,endpoint=False)
    def limits(par,cam,v):
        cx,cy,r,dr=par
        m=np.array(CALIBRATION['camera_matrices'][cam])
        a=np.cos(theta);b=np.sin(theta)
        eq=m[1]-v*m[2]
        # Radius changes linearly about height 2.30 metres.
        base=r-2.30*dr
        z=-(eq[0]*(cx+a*base)+eq[1]*(cy+b*base)+eq[3])/(eq[0]*dr*a+eq[1]*dr*b+eq[2])
        radial=base+dr*z
        p=np.stack([cx+radial*a,cy+radial*b,z,np.ones_like(z)],axis=-1)@m.T
        u=p[:,0]/p[:,2]
        return [float(u.min()),float(u.max())]
    def residual(param):
        return np.ravel([np.array(limits(param,cam,v))-[lo,hi]
                         for cam,rows in EDGES.items() for v,lo,hi in rows])
    result=least_squares(residual,[-1.30,.40,.145,-.002],bounds=([-1.6,0.,.09,-.045],[-1.,.8,.25,.045]))
    rows=[]
    for cam,edges in EDGES.items():
        for v,l,r in edges:
            rows.append(dict(camera=cam,v=v,observed_native_u=[l,r],model_native_u=limits(result.x,cam,v)))
    # The 2015 signal hides the western column. Its front photograph still
    # records both arrises, so only its section depth is shared with the east.
    opp=[(3500,2600,2661),(3590,2601,2662),(3680,2602,2664),(3780,2604,2666)]
    def west_error(x):
        param=result.x.copy();param[0]=x[0]
        return np.ravel([np.array(limits(param,'2017_front',v))-[lo,hi] for v,lo,hi in opp])
    west=least_squares(west_error,[1.30])
    return dict(axis_xy_m=result.x[:2].tolist(),western_x_m=float(west.x[0]),
                western_observed_v_left_right=opp,western_rmse_px=float(np.sqrt(np.mean(west.fun**2))),radius_at_z_230_m=float(result.x[2]),radius_gradient_per_m=float(result.x[3]),
                rmse_px=float(np.sqrt(np.mean(result.fun**2))),views=rows,
                observation='Left dark arris and the change from curved to flat coursing on the eastern shaft. Radius and scale are estimates. The opposite shaft is partly obscured in the oblique photograph.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
    d=fit();a.output.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n')
    print(d['axis_xy_m'],d['radius_at_z_230_m'],d['radius_gradient_per_m'],d['rmse_px'])
