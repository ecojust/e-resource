"""Street coordinates of the rounded stair enclosure at No. 2."""
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
MEASURE=HERE.parent/'measurements'
sys.path.insert(0,str(MEASURE))
from register_front import Camera
STATIONS=json.loads((MEASURE/'december-street-geometry.json').read_text())
PLAN=np.asarray(json.loads((MEASURE/'round-stair-plan.json').read_text())['horizontal_spine_xy'])
def wall_y(x):return float(np.interp(x,PLAN[:,0],PLAN[:,1]))
def at_surface(pixel,offset=0,view='june'):
    if view=='june':
        c=Camera();o=c.c;d=c.ray(pixel)
    else:
        s=STATIONS['photos'][str(view)]
        o=np.asarray(s['C']);d=np.asarray(s['R']).T@np.linalg.solve(s['K'],[*pixel,1.])
    y=0.
    for i in range(32):
        p=o+d*(y-o[1])/d[1]
        yy=wall_y(p[0])+offset
        if abs(yy-y)<1e-7:break
        y=yy
    return o+d*(yy-o[1])/d[1]
