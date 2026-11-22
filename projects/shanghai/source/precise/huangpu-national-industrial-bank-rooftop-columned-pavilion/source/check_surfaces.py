"""Read the pavilion's two actual shafts, five reliefs, stone pier caps, and the roof profile."""
from pathlib import Path
import os,runpy
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def ray(label,origin,direction,mat,dist,tol=.006):
        hit=reader.ray(origin,direction,4);rows.append(dict(part=label,origin=origin,direction=direction,expected_m=dist,material=mat,hit=hit,passed=bool(hit and hit['material']==mat and abs(hit['distance_m']-dist)<tol)))
    def front(label,x,z,mat,y):ray(label,[float(x),-1.,float(z)],[0,1,0],mat,1+y)
    for xc in PILLARS:
        for z,r,m in [(.14,.207,CAP),(.26,.174,COLUMN),(.67,.174,COLUMN),(1.1,.174,COLUMN),(1.55,.196,CAP),(1.62,.172,COLUMN),(1.70,.215,CAP),(1.77,.238,CAP)]:
            for theta in (-pi/2,-pi/3,-2*pi/3):
                dx,dy=cos(theta),sin(theta);ray('Round shaft or collar',[xc+1.15*dx,.18+1.15*dy,z],[-dx,-dy,0],m,1.15-r)
    for x in [-2.04,2.04]:
        for z in (.25,.81,1.49):front('Square pier face',x,z,WALL,-.020)
        for z,y in [(1.73,-.055),(1.80,-.090),(1.86,-.113)]:front('Square pier capital',x,z,CAP,y)
    for x in CRESCENTS:
        for off in (-.068,0,.068):
            z=2.208-(.119**2-off**2)**.5;front('Crescent-shaped raised relief',x+off,z,LEAF,-.076)
        front('Recess within the crescent ends',x,2.195,WALL,-.045)
    for x in [-1.6,-.7,.13,.82,1.74]:
        for z,y,m in [(1.91,-.11,CAP),(1.957,-.054,LINE),(2.005,-.151,CAP),(2.27,-.072,CAP),(2.35,-.104,LINE),(2.52,-.25,TOP)]:front('Layered head beam and roof',x,z,m,y)
    for x in (-.7,0,.7):
        front('Deep rectangular shadow behind pavilion',x,1.02,SHADOW,.85)
        front('Inset sill step',x,.22,CAP,.42)
    for x in np.linspace(-.732,.732,8):
        front('Vertical member of roof rail',x,2.69,IRON,.380)
    for x in (-.60,-.22,.11,.46):
        front('Continuous top rail',x,2.859,IRON,.379)
    return dict(samples=rows,passed=all(s['passed'] for s in rows))
