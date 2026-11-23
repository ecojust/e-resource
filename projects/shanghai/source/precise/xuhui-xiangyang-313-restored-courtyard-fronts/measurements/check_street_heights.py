"""Rebuild the registered exterior roof and sill triangulations without photographs."""
from pathlib import Path
import json
import numpy as np

def intersect(rows):
    origin=np.array([121.453558,31.210602])
    metric=np.array([95180.,110867.])
    blocks=[]
    centres=[]
    for row in rows.values():
        cx,cy=np.asarray(row['size'],dtype=float)/2
        fx=cx/np.tan(np.radians(row['hfov']/2))
        az,el=np.radians([row['yaw'],row['pitch']])
        f=np.array([np.sin(az)*np.cos(el),np.cos(az)*np.cos(el),np.sin(el)])
        right=np.array([np.cos(az),-np.sin(az),0.])
        up=np.cross(right,f)
        u,v=row['pixel']
        ray=f+(u-cx)/fx*right-(v-cy)/fx*up
        ray/=np.linalg.norm(ray)
        blocks.append(np.eye(3)-np.outer(ray,ray))
        centres.append(np.r_[(np.array(row['wgs84'])-origin)*metric,row['provider_device_height']])
    p=np.linalg.lstsq(np.sum(blocks,axis=0),np.einsum('kij,kj->i',blocks,centres),rcond=None)[0]
    return p[:2]/metric+origin,p[2]

if __name__=='__main__':
    source=Path(__file__).resolve().with_name('street-height-controls.json')
    for label,row in json.loads(source.read_text())['observations'].items():
        xy,z=intersect(row['original_pixels'])
        assert abs(z-row['height_above_station_ground']) < .006
        assert np.allclose(xy,row['point_wgs84'],rtol=0,atol=1.e-9)
        print(label,round(z,2),*xy.round(8))
