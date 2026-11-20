"""Recompute the plan positions of five matched roof features from the observed street photographs."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np

root=Path(__file__).resolve().parents[3]
src=root/'source/precise/jingan-yanan-955-no2'
registration=json.loads((src/'roof-feature-triangulation.json').read_bytes())
references=json.loads((src/'reference-review.json').read_bytes())
a,b=registration['local_origin_wgs84']
ky=math.pi*6371008.8/180
kx=ky*math.cos(math.radians(b))
result={}
for name,point in registration['points'].items():
    normals=[];stations=[];directions=[];slopes=[]
    for key,(u,v) in point['observations_xy'].items():
        station=references['panoramas'][key];width,height=600,410
        assert station['sha256']==registration['station_inputs'][key]['sha256']
        focal=width/2/math.tan(math.radians(station['hfov']/2))
        x,y=(u-width/2)/focal,(height/2-v)/focal
        pitch=math.radians(station['pitch'])
        forward=math.cos(pitch)-y*math.sin(pitch)
        az=math.radians(station['bearing'])+math.atan2(x,forward)
        directions.append([math.sin(az),math.cos(az)])
        slopes.append((math.sin(pitch)+y*math.cos(pitch))/math.hypot(x,forward))
        normals.append([math.cos(az),-math.sin(az)])
        lon,lat=station['position'];stations.append([(lon-a)*kx,(lat-b)*ky])
    normals=np.array(normals);stations=np.array(stations)
    rhs=np.einsum('ij,ij->i',normals,stations)
    estimate=np.linalg.lstsq(normals,rhs,rcond=None)[0]
    offsets=np.abs(normals@estimate-rhs)
    distance=np.einsum('ij,ij->i',directions,estimate-stations)
    assert np.max(np.abs(estimate-point['local_enu_m']))<=.0006
    assert np.max(np.abs(offsets-point['rays_residual_m']))<=.0006
    heights=np.array(slopes)*distance
    assert np.max(np.abs(heights-point['lens_relative_height_range_m']))<=.006
    result[name]={'stations':len(stations),'largest_residual_m':float(max(offsets))}
assert len(result)==5
print(json.dumps(result,indent=2))
