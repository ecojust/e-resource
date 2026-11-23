"""Original 1080 × 659 plan measured in its two named street axes."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon,box
HERE=Path(__file__).resolve().parent
REGISTER=json.loads((HERE.parent/'measurements/historic-ground-plan.json').read_bytes())
SCALE=REGISTER['metres_per_pixel']
LEVELS=[0.,2.219,5.622,9.132,12.718,16.55]
def xy(u,v):
    return np.array([(u-550.5)*SCALE,(579-v)*SCALE])
def trace(points):
    return Polygon([xy(*p) for p in points])
GROUND=trace(REGISTER['ground_wall_trace_px'])
TOP=trace([(385,579),(716,579),(892,342),(709,59),(683,40),(644,90),(593,151),(521,151),(496,190),(476,144),(199,303)])
STAIR=trace(REGISTER['rear_staircase']['opening_px'])
STREETS={'fuxing':(xy(385,579),xy(199,303)),'wulumuqi':(xy(716,579),xy(892,342))}
def wall(b,a,c,shape,inner,outer,mat,name,outward=None):
    a,c=map(np.asarray,[a,c])
    direction=(c-a)/np.linalg.norm(c-a)
    n=np.array([direction[1],-direction[0]])
    if outward is not None and np.dot(n,outward)<0:
        inner,outer=-outer,-inner
    b.prism(shape,inner,outer,lambda u,z,d:(*(a+u*direction+n*d),z),mat,name)
def segment(b,a,c,bottom,top,inner,outer,mat,name,outward=None):
    length=np.linalg.norm(np.asarray(c)-a)
    wall(b,a,c,box(0,bottom,length,top),inner,outer,mat,name,outward)
