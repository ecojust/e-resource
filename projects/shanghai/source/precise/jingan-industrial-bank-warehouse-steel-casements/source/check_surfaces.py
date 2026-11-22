"""Read back the delivered glass, moving-leaf positions, facade panels and lintel from triangles."""
from pathlib import Path
from math import cos,sin,pi
import os,runpy
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def test(name,x,z,y,material,tol=.013):
        ray=reader.ray([x,-2,z],[0,1,0],5)
        rows.append(dict(part=name,origin=[x,-2,z],hit=ray,depth=y,material=material,passed=bool(ray and ray['material']==material and abs(ray['distance_m']-(2+y))<tol)))
    for x in [-2.88,2.88]:
        for z in [.4,2.62,4.71,6.24,8.39]:test('Stepped face of the pier',x,z,-.11,BRICK)
    for lo,hi in LEVELS:
        for x in [-1.80,-.95,0,.64,1.91]:test('Upper surface lip seen from river',x,lo-.039,-.126,EDGE)
    for k,(lo,hi)in enumerate(LEVELS):
        width=2*HALF/5;transom=lo+.76*(hi-lo) if k==0 else hi
        for j in range(5):
            x0=-HALF+j*width
            test('Fixed mullion',x0+.027,hi-.32,.154,STEEL)
            if k==0:
                test('Continuous lower-storey transom',x0+.25,transom,.156,STEEL);test('Fixed transom glass',x0+.18,hi-.24,.253,GLASS)
            opened=(j==0 if k==0 else j in [0,1,4])
            if opened:
                a=-(52 if j==0 else 24 if j==1 else 35)*pi/180;hinge=x0+.055
                for u in [.16,.49]:
                    y=.219-.195;x=hinge+u*cos(a)-y*sin(a);depth=.195+u*sin(a)+y*cos(a)
                    test('Partly opened sash glazing',x,lo+.27,depth,OPEN if j==0 else SWING)
                if k==1 and j==1:
                    test('Projecting edge of the lightly opened sash',x0+.75,lo+.56,-.147,STEEL)
                test('Deep recess exposed by the swing',x0+.812,lo+.56,.575,DARK)
            else:
                test('Fixed window glass',x0+.22,lo+.27,.253,GLASS);test('Fixed vertical glazing bar',x0+width/2,lo+.47,.197,BEAD)
    for lo,hi in [(.10,1.04),(3.76,5.22)]:
        for left,right in [(-1.99,-.98),(-.85,.75),(.90,1.99)]:
            test('Inset spandrel',.5*(left+right),lo+.29,.013,RECESS);test('Panel border',left+.024,lo+.37,-.041,GRAY)
    for s in [-1,1]:
        a,c=sorted((s*.245,s*2.09))
        for j in range(4):
            x=a+(j+.5)*(c-a)/4;test('Centre ridge of the angular relief',x+.012,7.715,-.157,RELIEF,.025)
    test('Round central boss',0,7.67,-.178,RELIEF);test('Dark boss ring',.162,7.67,-.094,DARK)
    return dict(passed=all(row['passed']for row in rows),samples=rows)
