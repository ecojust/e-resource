"""Probe the finished GLB geometry at its slabs, arrises, cheeks, brass rails and two newel caps."""
from pathlib import Path
import os,runpy
from stair_foot import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def test(label,origin,axis,material,dmin,dmax):
        hit=reader.ray(origin,axis,6.)
        rows.append(dict(part=label,origin=origin,direction=axis,hit=hit,passed=bool(hit and hit['material']==material and dmin<=hit['distance_m']<=dmax)))
    for i in range(COUNT):
        y=GOING*i;z=RISE*(i+1)
        for x in [-1.45,-.55,.1,.95,1.49]:
            test('Level stone tread', [x,y+.123,2.],[0,0,-1],TREAD,2.-z-.002,2.-z+.002)
            test('Rounded lip', [x,y-.09,z-.022],[0,1,0],NOSE,.054,.063)
            test('Stone riser', [x,y-.078,z-.093],[0,1,0],TREAD,.075,.080)
        for sign in (-1,1):
            ymid=y+(.233 if i==0 else .13);wall_x=sign*(half_width(ymid)+.072)
            test('Moulding below open handrail',[wall_x-.051,ymid,2.3],[0,0,-1],CAP,2.3-.245-ymid*RISE/GOING-.003,2.3-.245-ymid*RISE/GOING+.003)
            test('Round brass handrail',[sign*(half_width(ymid)+.081),ymid,2.44],[0,0,-1],BRASS,2.44-.904-ymid*RISE/GOING-.033,2.44-.904-ymid*RISE/GOING-.020)
    for sign in (-1,1):
        test('Original first-tread projection hits newel cap',[sign*(half_width(.13)+.072)-.051,.13,2.3],[0,0,-1],CAP,1.32,1.365)
        test('Raised cap',[sign*POST_X,0,1.28],[0,0,-1],CAP,.304,.308)
        test('Stone end post',[sign*POST_X,-.5,.3],[0,1,0],TREAD,.347,.351)
        for y in (.29,.71,1.17,1.62):
            x=sign*(half_width(y)+.072)
            origin=[x-1.1*sign,y,.57+y*RISE/GOING]
            hit=reader.ray(origin,[sign,0,0],1.35)
            rows.append(dict(part='Open space below brass',origin=origin,hit=hit,passed=hit is None))
    return dict(passed=all(x['passed']for x in rows),samples=rows)
