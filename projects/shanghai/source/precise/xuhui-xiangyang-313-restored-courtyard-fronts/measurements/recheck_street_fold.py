"""Recalculate the five surveyed window bounds and the optional far-camera attitude."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from check_street_windows import camera

HERE=Path(__file__).resolve().parent

def bounds(record,edge,station):
    first,last=np.asarray(edge,dtype=float)
    tangent=last-first
    tangent/=np.linalg.norm(tangent)
    normal=np.array([tangent[1],-tangent[0]])
    center=(first+last)/2
    pts=[]
    for pixel in record['pixels']:
        eye,ray=camera(station,pixel)
        ground=eye+ray*(normal@(first-eye[:2]))/(normal@ray[:2])
        pts.append([(ground[:2]-center)@tangent,ground[2]])
    (lu,lz),(ru,rz),(bu,bz),(au,az)=pts
    x0=(lu+au)/2
    x1=(ru+bu)/2
    return [min(x0,x1),(bz+az)/2,max(x0,x1),(lz+rz)/2]

def attitude(station,record):
    s=station['projection'];cx=s['width']/2;cy=s['height']/2
    eye,forward=camera(station,[cx,cy]);angle=np.radians(s['az'])
    right=np.array([np.cos(angle),-np.sin(angle),0.])
    up=np.cross(right,forward);focal=cx/np.tan(np.radians(s['hfov']/2))
    def residual(v):
        rot=Rotation.from_rotvec(np.deg2rad(v)).inv()
        values=[]
        for p in record['controls']:
            d=rot.apply(np.asarray(p['world_point_ENU'])-eye);w=forward@d
            u,vv=p['original_0_pixel']
            values.extend([cx+focal*(right@d)/w-u,cy-focal*(up@d)/w-vv])
        return [*values,*(np.asarray(v)*record['prior_weight_px_per_degree'])]
    return least_squares(residual,[0.,0.,0.],loss='soft_l1',f_scale=4.).x

if __name__=='__main__':
    data=json.loads((HERE/'west-fold-controls.json').read_text())
    views=json.loads((HERE/'street-window-photo-probes.json').read_text())['stations']
    for name,o in data['openings'].items():
        b=bounds(o,data['edges_enu'][str(o['edge'])],views[o['reference']])
        assert np.allclose(b,o['bounds_uz_m'],rtol=0,atol=.0002)
        print(name,np.round(b,3))
    check=views['2002-0']['local_attitude_check'];rot=attitude(views['2002-0'],check)
    assert np.allclose(check['rotvec_ENU_deg'],rot,rtol=0,atol=.0002)
    print('southern view rotation about ENU degrees',rot.round(5))
