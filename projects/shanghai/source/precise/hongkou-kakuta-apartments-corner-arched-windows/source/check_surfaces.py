"""Intersect the decoded meshes through the window heads, reveals, stonework and canopies."""
import os,runpy
from pathlib import Path
from math import cos,sin,pi
from corner_windows import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    samples=[]
    def ray(side,u,z,mat,depth,description):
        origin=point(side,u,-.85,z);direction=list(point(side,0,1,0));hit=reader.ray(origin,direction,2)
        good=bool(hit and hit['material']==mat and abs(hit['distance_m']-.85-depth)<.014)
        samples.append(dict(part=description,side=side,origin=origin,expected=mat,depth=depth,hit=hit,passed=good))
    for side in [-1,1]:
        for u,mat,y in [(.10,TRIM,-.091),(.177,TRIM,-.047),(.215,JOIN,-.012),(.395,WALL,0)]:
            for z in [.28,1.19,2.59]:ray(side,u,z,mat,y,'Corner arris and pier faces')
        for u in WINDOWS:
            for dx in [-.22,.22]:
                ray(side,u+dx,1.14,CLEAR,.172,'Separate lower glazing')
                ray(side,u+dx,1.54,TOP,.172,'Recessed arched transom')
                ray(side,u+dx,1.365,METAL,.105,'Transom rail in front of glass')
                ray(side,u+dx,.719,SILL,-.102,'Overhanging sill')
                ray(side,u+dx,2.145,HOOD,-.422,'Separate metal canopy rim')
            for shift in (-.365,.365):
                origin=point(side,u+shift,-.128,1.88)
                hit=reader.ray(origin,[0,0,1],.5)
                samples.append(dict(part='Canopy support seen from below',side=side,origin=origin,expected=BRACKET,
                                    hit=hit,passed=bool(hit and hit['material']==BRACKET and .105<hit['distance_m']<.20)))
            ray(side,u,1.01,METAL,.117,'Central casement stile')
            for t in [.17,.29,.50,.74,.85]:
                ray(side,u+(R-.026)*cos(t*pi),SPRING+(RISE-.027)*sin(t*pi),METAL,.114,'Arched frame')
            ray(side,u+.495,1.56,WALL,0,'Rendered wall next to pierced jamb')
        ray(side,1.800,2.15,WALL,0,'Narrow independent joint between two canopies')
    return dict(passed=all(x['passed'] for x in samples),samples=samples)
