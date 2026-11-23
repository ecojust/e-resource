"""The ground-plan partitions, set-back floor plates and the rear building enclosure."""
import numpy as np
from shapely.geometry import Polygon,box
from plan import GROUND,TOP,STAIR,LEVELS,xy,wall,segment
from materials import STUCCO,BASE,PALE,TERRAZZO,WHITE

def add_floors(b,lod=False):
    b.plan_prism(GROUND.buffer(-.025,join_style=2),-.145,0,TERRAZZO,'ground floor on original trace')
    corner=box(-3.17,-1.,3.17,1.82)
    # The four triangular front balconies have their own floor and back wall.
    # All other slabs terminate inside the street wall to keep the render surface continuous.
    floor=TOP.buffer(-.13,join_style=2).difference(STAIR.buffer(.025,join_style=2)).difference(corner)
    for i,z in enumerate(LEVELS[1:-1],start=2):
        b.plan_prism(floor,z-.15,z,TERRAZZO,f'floor {i} with two-flight stair opening')
    # The actual plan traces continuous partitions as well as the breaks at the hall doors.
    segments=[[(496,545),(496,451)],[(496,407),(451,332),(419,355),(338,228)],
              [(496,306),(479,309),(453,261)],[(431,239),(403,196)],
              [(605,543),(605,451)],[(605,405),(665,326),(665,271),(725,193)],
              [(664,324),(814,438)],[(449,333),(300,438)],
              [(492,471),(476,480)],[(607,464),(623,479)]]
    for n,polyline in enumerate(segments):
        for p,q in zip(polyline,polyline[1:]):
            segment(b,xy(*p),xy(*q),.012,LEVELS[1]-.17,-.070,.070,WHITE,f'ground hall partition {n+1}')

def add_back(b,lod=False):
    # Original rear wall has a wide return into the light well of the stair.
    # The sash in the stair end is visible as a break on the historical plan.
    points=[(892,342),(709,59),(683,40),(644,90),(593,151),(521,151),(496,190),(476,144),(199,303)]
    for i,(a,c) in enumerate(zip(points,points[1:])):
        p,q=xy(*a),xy(*c)
        u=q-p
        n=np.array([u[1],-u[0]])/np.linalg.norm(u)
        if i==4:
            for lo,hi in [(0.,.27),(.73,1.)]:
                segment(b,p+lo*u,p+hi*u,0,LEVELS[-1]-.12,-.20,.0,STUCCO,'rear stair end wall edge',n)
            for z,h in zip(LEVELS,LEVELS[1:]):
                segment(b,p+u*.27,p+u*.73,z,z+.84,-.20,.0,STUCCO,'rear stair sill wall',n)
                segment(b,p+u*.27,p+u*.73,h-.40,h,-.20,.0,STUCCO,'rear stair head wall',n)
        else:
            segment(b,p,q,0,LEVELS[-1]-.12,-.20,.0,STUCCO,'rear envelope from historical plan',n)
        segment(b,p,q,0,.35,-.04,.028,BASE,'rear plinth',n)
