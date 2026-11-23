"""Read the porch from the full street front and its reverse oblique, at original resolution."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).absolute().parent
# Positions read independently in the 2020 front and corner images.
PAIRS={
 'fronton-peak':[[386.5,266.5],[321,284]],
 'canopy-west-tip':[[265.5,304],[229,299]],
 'west-door-head':[[343.0,316.5],[256.5,316.0]],
 'west-door-spring-left':[[306.5,334.5],[238.5,328]],
 'west-door-spring-right':[[379,336.5],[279,330]],
 'west-door-bottom-left':[[307.5,411.5],[236,401]],
 'west-door-bottom-right':[[384,417],[275,399]],
 'east-door-head':[[446,317.5],[309,322]],
 'east-door-spring-left':[[407.5,337],[292,331]],
 'east-door-spring-right':[[493.0,336.5],[323.5,338]],
 'east-door-bottom-left':[[417.5,422.5],[292.5,396.5]],
 'east-door-bottom-right':[[510.5,429],[323,394]],
 'central-number':[[393,346.5],[286,343.0]]}

def pair(a,b,points):
    origins=[];directions=[]
    for camera,p in zip([a,b],points):
        c=np.asarray(camera['C'])
        t=np.asarray(camera['R']).T@np.linalg.solve(np.asarray(camera['K']),[*p,1.]);t/=np.linalg.norm(t)
        origins.append(c);directions.append(t)
    maps=[np.eye(3)-np.outer(t,t) for t in directions]
    xyz=np.linalg.solve(sum(maps),sum(m@c for m,c in zip(maps,origins)))
    return dict(pixels=points,xyz=xyz.tolist(),distance_to_rays_m=[float(np.linalg.norm(np.cross(xyz-c,t)))for c,t in zip(origins,directions)])
if __name__=='__main__':
    cs=json.loads((HERE/'three-front-stations.json').read_bytes())
    report={k:pair(cs['street-front-2020'],cs['street-corner-2020'],p)for k,p in PAIRS.items()}
    for k,v in report.items():print(k,np.round(v['xyz'],2),np.round(v['distance_to_rays_m'],2))
    (HERE/'portico-two-views.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
