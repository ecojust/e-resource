"""Reproject the red street front and triangulate the width from its two opposite views."""
import json
from pathlib import Path
import numpy as np
from register_street import Camera
from fit_street_cameras import basis,en_axes,meters,V
D=Path(__file__).parent

def check_front():
    data=json.loads((D/'street-front-measured-limits.json').read_bytes())
    for group,rr in data['observations'].items():
        for o in rr['observations']:
            xyz=Camera(o['view']).wall(o['original_uv'])
            assert np.max(np.abs(xyz-np.asarray(o['xyz_on_front_m'])))<.001
        print(group,rr['median_m'])

def opposite_rays(key,station,point,web_geometry,registered):
    cam=Camera(key)
    c=station['opposite_frame'];size=np.array([c['width'],c['height']]);work=np.array([600.,round(600*c['height']/c['width'])])
    u,v=np.asarray(point)*size/work;f=.5*size[0]/np.tan(np.deg2rad(.5*c['hfov']))
    raw=basis(c['az'],c['pitch'],0).T@[(u-size[0]/2)/f,(v-size[1]/2)/f,1.]
    raw=raw/np.linalg.norm(raw)
    if registered:
        old=V[key];return cam.c,cam.R.T@basis(old['yaw'],old['pitch'],0)@raw
    a=en_axes(web_geometry['x_azimuth_degrees']);loc=(np.asarray(station['station_wgs'])-web_geometry['origin_wgs84'])*meters
    return a.T@np.r_[loc,station['station_height']],a.T@raw

def width_check():
    control=json.loads((D/'opposite-street-width.json').read_text())
    ge=json.loads((D/'street-cameras.json').read_text())
    for name,v in control['marks'].items():
        for mode in ['vendor','registered']:
            marks=[opposite_rays(k,s,p,ge,mode=='registered') for (k,s),p in zip(control['views'].items(),v['working_pixels_600_wide'])]
            h=np.array([np.eye(3)-np.outer(ray,ray)for _,ray in marks]);c=np.array([e for e,_ in marks])
            result=np.linalg.lstsq(h.sum(0),np.einsum('kij,kj->i',h,c),rcond=None)[0]
            assert np.max(np.abs(result-v[mode]['xyz_local_m']))<.001
        print(name,-v['registered']['xyz_local_m'][1])
if __name__=='__main__':
    check_front();width_check()
